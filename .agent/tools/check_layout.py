"""Read-only checks for the repository organization; never execute archived code."""
from pathlib import Path
import ast
from collections import Counter
import datetime
import hashlib
from html.parser import HTMLParser
import json
import os
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
MANIFESTS = ROOT / '.agent/manifests'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_OPTIONAL_LOCKS='0')
    for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_CONFIG_PARAMETERS', 'GIT_CONFIG_COUNT'):
        env.pop(key, None)
    return subprocess.run(['git', '-C', str(ROOT), '-c', 'core.hooksPath=/dev/null',
                           '-c', 'core.fsmonitor=false', *args], env=env,
                          capture_output=True, check=True).stdout


class HTMLLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.images = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'img' and attrs.get('src'):
            self.images.append(attrs['src'])
        for key in ('href', 'src'):
            if attrs.get(key):
                self.links.append(attrs[key])


def without_fences(text):
    output = []
    fence = None
    for line in text.splitlines():
        match = re.match(r'^\s*(`{3,}|~{3,})', line)
        if match:
            marker = match.group(1)[0]
            if fence is None:
                fence = marker
            elif marker == fence:
                fence = None
            continue
        if fence is None:
            output.append(line)
    return '\n'.join(output)


def markdown_ids(text):
    ids = set()
    counts = {}
    for heading in re.findall(r'^#{1,6}\s+(.+?)\s*#*\s*$', without_fences(text), re.M):
        slug = re.sub(r'[^\w\s-]', '', heading.lower()).replace(' ', '-')
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        ids.add(slug if count == 0 else slug + '-' + str(count))
    return ids


def verify_local_link(source, target, html_ids=None):
    target = target.strip()
    if target.startswith('<'):
        target = target[1:target.index('>')]
    else:
        target = target.split()[0]
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return False
    if not parsed.path and html_ids is not None:
        if parsed.fragment:
            assert unquote(parsed.fragment) in html_ids, (str(source), target)
        return False
    path = (source.parent / unquote(parsed.path)).resolve() if parsed.path else source
    assert path.is_relative_to(ROOT), ('Local link escapes repository', str(source), target)
    assert path.exists(), ('Broken local link', str(source), target)
    if parsed.fragment and path.suffix.lower() == '.md':
        assert unquote(parsed.fragment) in markdown_ids(path.read_text()), ('Broken Markdown anchor', str(source), target)
    return bool(parsed.path or parsed.fragment)


def verify_consolidation(maintenance):
    receipt = json.loads((MANIFESTS / 'documentation-consolidation.json').read_text())
    found = []
    for directory, dirs, files in os.walk(ROOT):
        dirs[:] = [name for name in dirs if name != '.git']
        for name in files:
            if 'readme' in name.lower():
                found.append((Path(directory) / name).relative_to(ROOT).as_posix())
    assert sorted(found) == ['README.md'], ('Extra README filename or variant', found)
    snapshot = git('show', maintenance['documentation_snapshot_commit'] + ':README.md')
    assert hashlib.sha256(snapshot).hexdigest() == receipt['main_document_sha256']
    for item in receipt['documentation_inputs']:
        raw = git('show', receipt['base_commit'] + ':' + item['path'])
        assert hashlib.sha256(raw).hexdigest() == item['sha256']
    for item in receipt['literal_documents_preserved']:
        assert sha(ROOT / item['current_path']) == item['sha256']
    removed = {item['path'] for item in receipt['removed_files']}
    allowed = set(receipt['allowed_changed_current_paths']) | set(maintenance['allowed_changed_paths'])
    exact = 0
    total = 0
    for entry in git('ls-tree', '-rz', '--full-tree', receipt['base_commit']).split(b'\0'):
        if not entry:
            continue
        metadata, previous_name = entry.split(b'\t', 1)
        mode, kind, blob = metadata.decode().split()
        assert kind == 'blob'
        previous_name = previous_name.decode()
        total += 1
        if previous_name in removed:
            assert not (ROOT / previous_name).exists()
            continue
        current_name = receipt['renamed_files'].get(previous_name, previous_name)
        current = ROOT / current_name
        assert current.is_file() and not current.is_symlink(), current_name
        if current_name not in allowed:
            raw = current.read_bytes()
            actual_blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            assert actual_blob == blob, ('Unrelated file changed', previous_name, current_name)
            exact += 1
    return {'README_filename_variants_found': sorted(found),
            'prior_snapshot_files_accounted_for': total,
            'prior_snapshot_files_preserved_byte_identical': exact,
            'renamed_files_in_this_change': len(receipt['renamed_files']),
            'redundant_files_retained_in_prior_commit': len(removed),
            'literal_document_bodies_preserved': len(receipt['literal_documents_preserved'])}


def verify_maintenance():
    receipt = json.loads((MANIFESTS / 'maintenance.json').read_text())
    audit = json.loads((ROOT / receipt['source_audit']).read_text())
    assert receipt['version'] == '1.6.2' and receipt['tests_executed'] == 130
    assert not receipt['HUD_cfg_executed'] and not receipt['real_game_modified']
    for name, hashes in receipt['product_files'].items():
        prior = git('show', receipt['base_commit'] + ':' + name)
        assert hashlib.sha256(prior).hexdigest() == hashes['before_sha256']
        assert sha(ROOT / name) == hashes['after_sha256']
    tree = ast.parse((ROOT / 'setup_tf2_bazzite.py').read_text())
    constants = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
                 if isinstance(node, ast.Assign) and len(node.targets) == 1
                 and isinstance(node.targets[0], ast.Name)
                 and node.targets[0].id in ('SCRIPT_VERSION', 'MAXIHUD_REVIEWED_SHA256', 'MAXIHUD_MENU_FRAME')}
    assert constants['SCRIPT_VERSION'] == receipt['version']
    assert constants['MAXIHUD_REVIEWED_SHA256'] == audit['reviewed_source_sha256']
    eol = next(node.value for node in tree.body if isinstance(node, ast.Assign)
               and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'MAXIHUD_CRLF_FILES')
    paths = tuple(constants[item.id] if isinstance(item, ast.Name) else ast.literal_eval(item) for item in eol.elts)
    assert list(paths) == audit['CRLF_canonical_paths'] and len(paths) == 3
    prior_tree = ast.parse(git('show', receipt['base_commit'] + ':setup_tf2_bazzite.py').decode())
    prior_pins = next(ast.literal_eval(node.value) for node in prior_tree.body if isinstance(node, ast.Assign)
                      and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'MAXIHUD_REVIEWED_SHA256')
    assert prior_pins == constants['MAXIHUD_REVIEWED_SHA256']
    assert audit['test_run']['result'] == 'OK' and audit['test_run']['tests'] == 130
    assert audit['test_run']['installer_sha256'] == sha(ROOT / 'setup_tf2_bazzite.py')
    assert audit['test_run']['tests_sha256'] == sha(ROOT / 'test_setup_tf2_bazzite.py')
    assert audit['test_run']['live_HTTP_blocked']
    assert audit['test_run']['official_archive_tests'] == 5 and audit['test_run']['skipped'] == 0
    assert not audit['production_pins_mocked_in_official_tests']
    assert audit['official_ZIP_sha256_after_tests'] == audit['reproduction']['archive_sha256']
    assert audit['known_queue_mode_commands_removed'] == 4 and not audit['runtime_visual_tested']
    return receipt


def verify(bootstrap=False):
    layout = json.loads((MANIFESTS / 'layout.json').read_text())
    maintenance = verify_maintenance()
    relocated = 0
    unchanged_relocated = 0
    changed_docs = []
    history_only = []
    for row in layout['files']:
        if row['current_path'] is None:
            assert row['retention'] == 'history_only' and not row['content_changed']
            raw = git('show', row['preserved_commit'] + ':' + row['preserved_path'])
            assert hashlib.sha256(raw).hexdigest() == row['before_sha256'] == row['after_sha256']
            assert not (ROOT / row['previous_path']).exists()
            history_only.append(row['previous_path'])
            continue
        current = ROOT / row['current_path']
        assert current.is_file() and not current.is_symlink(), row['current_path']
        assert sha(current) == row['after_sha256'], row['current_path']
        if not row['content_changed']:
            assert row['before_sha256'] == row['after_sha256']
        else:
            assert (row['current_path'].endswith('.md') or row['current_path'] in maintenance['product_files']) and row.get('change_reason')
            changed_docs.append(row['current_path'])
        if row['previous_path'] != row['current_path']:
            relocated += 1
            unchanged_relocated += not row['content_changed']
            assert not (ROOT / row['previous_path']).exists(), row['previous_path']
    protected = [row for row in layout['files'] if row['previous_path'].startswith('.provenance/')]
    assert all(not row['content_changed'] for row in protected), 'Historical provenance was edited'
    for name in ('setup_tf2_bazzite.py', 'test_setup_tf2_bazzite.py'):
        row = next(row for row in layout['files'] if row['previous_path'] == name)
        assert row['current_path'] == name, name
        original = git('show', layout['original_files_snapshot_commit'] + ':' + name)
        assert hashlib.sha256(original).hexdigest() == row['before_sha256'], name
        assert row['after_sha256'] == maintenance['product_files'][name]['after_sha256'], name
    assert (ROOT / 'test_setup_tf2_bazzite.py').with_name('setup_tf2_bazzite.py').is_file()
    history = git('rev-list', '--reverse', 'HEAD').decode().splitlines()
    previous = layout['previous_commits']
    assert history[:len(previous)] == previous, 'Previous history is not preserved'
    revisions = json.loads((ROOT / '.agent/provenance/revisions.json').read_text())
    revision_checks = 0
    for event in revisions:
        for write in event['writes']:
            raw = git('show', event['commit'] + ':' + write['repo_path'])
            assert len(raw) == write['bytes'] and hashlib.sha256(raw).hexdigest() == write['sha256']
            revision_checks += 1
    active_docs = [ROOT / 'README.md', ROOT / '.agent/ARCHIVE.md',
                   ROOT / '.agent/reconstructions/incomplete-v1.5.0/CANDIDATE.md']
    active_docs += sorted((ROOT / '.agent/history/guides').glob('*.md'))
    active_docs += sorted((ROOT / '.agent/docs').glob('*.md'))
    local_links = 0
    for doc in active_docs:
        body = without_fences(doc.read_text())
        targets = re.findall(r'!?\[[^\]\n]*\]\(([^)\n]+)\)', body)
        targets += re.findall(r'^\s*\[[^\]]+\]:\s*(\S+)', body, re.M)
        for target in targets:
            local_links += verify_local_link(doc, target)
    visual = json.loads((MANIFESTS / 'visual-comparison.json').read_text())
    assert visual['visual_verification_status'] == 'confirmed_rendered_images'
    assert visual['decoded_images'] == visual['visually_inspected_images'] == 15
    assert visual['visually_inspected_HUDs'] == 8
    verified_readme = git('show', visual['verified_README_commit'] + ':README.md')
    assert hashlib.sha256(verified_readme).hexdigest() == visual['README_sha256']
    assert sha(ROOT / 'README.md') == visual['current_README_sha256']
    section = re.compile(r'^## HUD comparison\n.*?(?=^## |\Z)', re.M | re.S)
    prior_comparison = section.search(verified_readme.decode()).group()
    current_comparison = section.search((ROOT / 'README.md').read_text()).group()
    assert hashlib.sha256(prior_comparison.encode()).hexdigest() == visual['comparison_section_sha256']
    image_lines = lambda body: [line for line in body.splitlines() if line.startswith('[![')]
    assert image_lines(prior_comparison) == image_lines(current_comparison)
    assert hashlib.sha256('\n'.join(image_lines(current_comparison)).encode()).hexdigest() == visual['current_image_markdown_sha256']
    page = ROOT / visual['source_html_previous_path']
    source_html = git('show', visual['source_html_commit'] + ':' + visual['source_html_previous_path'])
    assert hashlib.sha256(source_html).hexdigest() == visual['source_html_sha256']
    parser = HTMLLinks()
    parser.feed(source_html.decode())
    readme_images = re.findall(r'!\[[^\]\n]*\]\((https?://[^)\s]+)\)', (ROOT / 'README.md').read_text())
    assert len(readme_images) == 15 and Counter(readme_images) == Counter(parser.images)
    assert Counter(readme_images) == Counter(img['url'] for card in visual['cards'] for img in card['images'])
    assert not page.exists() and visual['current_html_path'] is None
    audit = json.loads((MANIFESTS / 'command-audit.json').read_text())
    assert sha(ROOT / 'setup_tf2_bazzite.py') == audit['installer_sha256']
    source_tree = ast.parse((ROOT / 'setup_tf2_bazzite.py').read_text())
    declared_flags = {arg.value for call in ast.walk(source_tree)
                      if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                      and call.func.attr == 'add_argument'
                      for arg in call.args if isinstance(arg, ast.Constant)
                      and isinstance(arg.value, str) and arg.value.startswith('--')}
    used_flags = set(re.findall(r'--[a-z][a-z0-9-]*', (ROOT / 'README.md').read_text()))
    assert used_flags <= declared_flags
    assert used_flags == set(audit['README_flags_verified'])
    assert declared_flags == set(audit['declared_flags'])
    for target in parser.links:
        local_links += verify_local_link(page, target, parser.ids)
    consolidation = verify_consolidation(maintenance)
    current_checks = 0
    hashes_file = MANIFESTS / 'files.sha256.json'
    if not bootstrap:
        hashes = json.loads(hashes_file.read_text())
        for name, expected in hashes.items():
            assert sha(ROOT / name) == expected, name
            current_checks += 1
        declared = {row['current_path'] for row in layout['files'] if row['current_path'] is not None} | set(layout['new_files'])
        assert set(hashes) == declared - {'.agent/manifests/files.sha256.json'}
    return {'verified_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'repository': str(ROOT), 'head': git('rev-parse', 'HEAD').decode().strip(),
            'original_files_accounted_for': len(layout['files']), 'files_relocated': relocated,
            'relocated_files_byte_identical': unchanged_relocated,
            'files_preserved_only_in_Git': history_only, 'curated_or_maintained_files_updated': changed_docs,
            'historical_provenance_files_byte_identical': len(protected),
            'prior_commits_preserved': len(previous), 'historical_revision_hashes_checked': revision_checks,
            'README_original_image_URLs_matched': len(readme_images),
            'README_flags_checked_statically': len(used_flags),
            'rendered_image_confirmation_receipt_verified': True,
            'active_markdown_documents_checked': len(active_docs), 'local_links_checked': local_links,
            'current_manifest_files_checked': current_checks, 'current_manifest_skipped_for_bootstrap': bootstrap,
            'this_verifier_executes_product_code': False, 'network_requests': 0,
            'recorded_tests_executed': maintenance['tests_executed'],
            'recorded_synthetic_tests': maintenance['tests_executed'] - maintenance['official_zip_integration_tests'],
            'recorded_official_archive_tests': maintenance['official_zip_integration_tests'],
            'HUD_cfg_executed': False, 'real_game_modified': False,
            **consolidation}


if __name__ == '__main__':
    try:
        print(json.dumps(verify(bootstrap='--bootstrap' in sys.argv[1:]), ensure_ascii=False, indent=2))
    except (AssertionError, OSError, subprocess.CalledProcessError) as error:
        print('Layout verification failed: ' + str(error), file=sys.stderr)
        sys.exit(1)
