"""Build an archive from data. Never import, eval, exec, or run recovered code.

Reconstruction recipes below were selected by inspection of the source messages.
Only literal text substitutions and explicit text splices are performed.
"""
from pathlib import Path, PurePosixPath
import ast
import datetime as dt
import difflib
import hashlib
import html
import json
import re

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'prepared-final'
OUT.mkdir(exist_ok=False)
SOURCE = json.loads((ROOT / 'share-route.json').read_text())['serverResponse']['data']
NODES = SOURCE['linear_conversation']
HD = json.loads((ROOT / 'heredoc-index.json').read_text())
EVENTS = {}
STATE = {}
GAPS = []


def sha(data):
    return hashlib.sha256(data).hexdigest()


def event(seq):
    if seq not in EVENTS:
        m = NODES[seq-1]['message']
        EVENTS[seq] = {'sequence': seq, 'message_id': m['id'],
                       'source_timestamp': m['create_time'], 'writes': [], 'notes': []}
    return EVENTS[seq]


def put(seq, original, data, status='available_literal', recipe=None, repo_path=None):
    if isinstance(data, str):
        data = data.encode('utf-8')
    rel = repo_path or original.removeprefix('/mnt/data/')
    path = PurePosixPath(rel)
    assert not path.is_absolute() and '..' not in path.parts and '.git' not in path.parts
    # APFS may be case insensitive. Keep both original README names as basenames.
    if rel == 'TF2_HUD_UPDATE_README.md':
        rel = 'case-variants/TF2_HUD_UPDATE_README.md'
    output = OUT / f'{seq:04d}' / rel
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    rec = {'original_path': original, 'repo_path': rel, 'status': status,
           'sha256': sha(data), 'bytes': len(data), 'payload': str(output.relative_to(ROOT))}
    if recipe is not None:
        rec['recipe'] = recipe
    event(seq)['writes'].append(rec)
    STATE[rel] = data
    return data.decode('utf-8')


def literal(expr, variables=None):
    variables = variables or {}
    if isinstance(expr, ast.Constant) and isinstance(expr.value, (str, int)):
        return expr.value
    if isinstance(expr, ast.Name) and expr.id in variables:
        return variables[expr.id]
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
        return literal(expr.left, variables) + literal(expr.right, variables)
    raise ValueError('Not a static literal: ' + ast.dump(expr)[:200])


def inserted(expr):
    # Extract literal material from an explicitly reviewed splice, excluding s slices.
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return expr.value
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
        return inserted(expr.left) + inserted(expr.right)
    if isinstance(expr, ast.Subscript) and isinstance(expr.value, ast.Name) and expr.value.id == 's':
        return ''
    raise ValueError('Unexpected splice: ' + ast.dump(expr)[:200])


def patch_tree(seq, inline=False):
    d = next(d for d in HD if d['sequence'] == seq and
             d['kind'] == ('inline_python' if inline else 'heredoc_literal'))
    return ast.parse((ROOT / d['file']).read_text())


def node(tree, line):
    return next(n for n in tree.body if n.lineno == line)


def replacements(text, tree, lines=None, start=0, stop=10**8, permissive=False):
    variables = {}
    log = []
    for n in tree.body:
        if not isinstance(n, ast.Assign) or not isinstance(n.targets[0], ast.Name):
            continue
        name = n.targets[0].id
        if name != 's':
            try:
                variables[name] = literal(n.value, variables)
            except (ValueError, TypeError):
                pass
        if name != 's' or not (start <= n.lineno < stop) or (lines is not None and n.lineno not in lines):
            continue
        call = n.value
        if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == 'replace'):
            continue
        old, new = (literal(a, variables) for a in call.args[:2])
        count = literal(call.args[2], variables) if len(call.args) > 2 else -1
        matches = text.count(old)
        if not matches and not permissive:
            raise ValueError(f'Missing replacement at source line {n.lineno}: {old[:100]!r}')
        text = text.replace(old, new, count)
        log.append({'operation': 'replace', 'source_line': n.lineno, 'old': old, 'new': new,
                    'limit': count, 'matches': matches})
    return text, log


def splice(text, start, end, value, recipe):
    a = text.index(start)
    b = text.index(end, a) if end else a
    recipe.append({'operation': 'splice', 'start': start, 'end': end, 'insert': value})
    return text[:a] + value + text[b:]


def copy(seq, original, source_path, baseline=None, note=None):
    data = baseline.encode() if baseline is not None else STATE[source_path]
    put(seq, original, data, 'static_reconstruction',
        [{'operation': 'copy', 'from': source_path, 'note': note or 'Copy command present; execution output redacted.'}])


# Exact literal file bodies from cat heredocs; no shell or recovered Python is run.
for d in HD:
    if d['kind'] == 'heredoc_literal' and d.get('mode') != 'append':
        put(d['sequence'], d['path'], (ROOT / d['file']).read_bytes())

# Guide: the optional Medic addition is an alternative, not an asserted applied edit.
guide = (ROOT / 'inspection/0050-assistant.txt').read_text()
cfgs = re.findall(r'```cfg\n(.*?)\n```', guide, re.S)
assert len(cfgs) == 3
put(50, 'tf/cfg/overrides/autoexec.cfg', cfgs[0] + '\n')
put(50, 'tf/cfg/overrides/modules.cfg', cfgs[2] + '\n')
put(50, 'tf/cfg/overrides/autoexec.cfg', cfgs[0] + '\n' + cfgs[1] + '\n',
    'static_reconstruction', [{'operation': 'append_optional_medic_block', 'message': 50}],
    'alternatives/medic/tf/cfg/overrides/autoexec.cfg')

installer = (ROOT / 'heredocs/0084-1-setup_tf2_bazzite.py').read_text()
t = patch_tree(137, inline=True)
installer, rec = replacements(installer, t, lines={5})
put(137, '/mnt/data/setup_tf2_bazzite.py', installer, 'static_reconstruction', rec)
baseline0 = installer
copy(205, '/mnt/data/tf2-script-tests/setup_tf2_bazzite_before_visual_clarity.py',
     'setup_tf2_bazzite.py', baseline0)

t = patch_tree(205)
installer, rec = replacements(installer, t, lines={4, 9, 20, 25})
installer = splice(installer, "PERSONAL = '''", '// No sensitivity or keybind changes.',
                   inserted(node(t, 28).value), rec)
installer = splice(installer, '\n\n\nclass SetupError', None, inserted(node(t, 30).value), rec)
# The source inserts a provisional function block then replaces it. Insert only its final literal.
installer = splice(installer, '\ndef stage_cfg(', None, inserted(node(t, 84).value), rec)
installer, r = replacements(installer, t, lines={117}); rec += r
installer = splice(installer, "    managed_file(overrides / 'autoexec.cfg', PERSONAL)",
                   '\n\n\ndef download(', inserted(node(t, 122).value), rec)
installer, r = replacements(installer, t, start=125); rec += r
put(205, '/mnt/data/setup_tf2_bazzite.py', installer, 'static_reconstruction', rec)
baseline11 = installer
copy(246, '/mnt/data/tf2-script-tests/setup_tf2_bazzite_v1_1.py', 'setup_tf2_bazzite.py', installer)

t = patch_tree(246); rec = []
a = installer.index('"""Reversible'); b = installer.index('"""', a+3) + 3
installer = installer[:a] + inserted(node(t, 6).value) + installer[b:]
rec.append({'operation': 'replace_opening_docstring', 'source_line': 6})
installer, r = replacements(installer, t, lines={69, 70}); rec += r
installer = splice(installer, 'FPS_CAPS = ', None, inserted(node(t, 72).value), rec)
installer = splice(installer, '# Keep impact effects', 'CLARITY_MODULES = (', inserted(node(t, 85).value), rec)
installer, r = replacements(installer, t, start=89); rec += r
installer = splice(installer, '\ndef check_hud_conflicts(', '\ndef confirm(', '', rec)
installer = installer[:installer.index('\ndef main()')]
append = next(d for d in HD if d['sequence'] == 246 and d.get('mode') == 'append')
installer += (ROOT / append['file']).read_text()
rec.append({'operation': 'cut_old_main_and_append_literal', 'source': append['file']})
put(246, '/mnt/data/setup_tf2_bazzite.py', installer, 'static_reconstruction', rec)

t = patch_tree(251, inline=True)
installer, rec = replacements(installer, t, lines={4, 5})
put(251, '/mnt/data/setup_tf2_bazzite.py', installer, 'static_reconstruction', rec)
baseline12 = installer
tests12 = (ROOT / 'heredocs/0248-1-test_setup_v1_2.py').read_text()
rec = []; tests12 = splice(tests12, '\n    def test_checksum_verification_rejects_bad_content', None,
                           literal(node(t, 10).value), rec)
put(251, '/mnt/data/tf2-script-tests/test_setup_v1_2.py', tests12, 'static_reconstruction', rec)
copy(307, '/mnt/data/tf2_work/setup_tf2_bazzite_v1_2_0.py', 'setup_tf2_bazzite.py', baseline12)

t = patch_tree(325)
installer, rec = replacements(baseline12, t)
put(325, '/mnt/data/setup_tf2_bazzite.py', installer, 'static_reconstruction', rec)
baseline13a = installer

# A second v1.3.0 implementation in the source starts from the explicit v1.2.0 backup.
copy(359, '/mnt/data/tf2_hud_work/setup_tf2_bazzite_v1.2.0.py', 'setup_tf2_bazzite.py', baseline12,
     'Source path says v1.2.0; later patch asserts v1.2.0 text. The v1.3.0 branch restart is inferred.')
t = patch_tree(398)
installer, rec = replacements(baseline12, t)
rec.insert(0, {'operation': 'choose_baseline', 'message': 251,
               'note': 'Independent v1.3.0 variant; using preceding v1.3.0 text would fail old-text assertions.'})
put(398, '/mnt/data/setup_tf2_bazzite.py', installer, 'static_reconstruction', rec)
baseline13b = installer
tests = (ROOT / 'heredocs/0401-1-test_setup_tf2_bazzite.py').read_text()
copy(405, '/mnt/data/test_setup_tf2_bazzite.py', 'tf2_hud_work/test_setup_tf2_bazzite.py', tests)
copy(446, '/mnt/data/tf2_work/setup_tf2_bazzite_v1_3_0.py', 'setup_tf2_bazzite.py', baseline13b)
copy(446, '/mnt/data/tf2_work/test_v1_3_0.py', 'test_setup_tf2_bazzite.py', tests)
t = patch_tree(451)
installer, rec = replacements(installer, t, stop=18)
put(451, '/mnt/data/setup_tf2_bazzite.py', installer, 'static_reconstruction', rec)
tests, rec = replacements(tests, t, start=20)
put(451, '/mnt/data/test_setup_tf2_bazzite.py', tests, 'static_reconstruction', rec)
t = patch_tree(456, inline=True)
tests, rec = replacements(tests, t)
put(456, '/mnt/data/test_setup_tf2_bazzite.py', tests, 'static_reconstruction', rec)
baseline131 = installer

GAPS.extend([
    {'id': 'version_1_4_0', 'message': 468,
     'detail': 'Response advertises v1.4.0, but the last available edit sets SCRIPT_VERSION to 1.3.1. No complete v1.4.0 bytes or intervening version edit are present.'},
    {'id': 'branch_restart', 'messages': [325, 359, 398],
     'detail': 'Two v1.3.0 implementations exist. Patch 398 requires v1.2.0 text, not the prior v1.3.0 implementation. Both are preserved; the baseline choice is a documented inference.'},
])

# Apply the later available edits only as explicitly incomplete candidates.
# Do not synthesize the missing v1.4.0 version bump or claim exact attachment bytes.
t = patch_tree(544)
candidate, rec = replacements(baseline131, t, stop=17, permissive=True)
candidate = splice(candidate, '# Do not silently upgrade the HUDs or mastercomfig from the earlier installer.',
                   'HUD_MARKER =', inserted(node(t, 20).value), rec)
candidate = splice(candidate, 'def hud_is_current(', None, inserted(node(t, 63).value), rec)
candidate, r = replacements(candidate, t, start=101, permissive=True); rec += r
failed = [r for r in rec if r.get('operation') == 'replace' and r.get('matches') == 0]
put(544, '/mnt/data/setup_tf2_bazzite.py', candidate, 'partial_static_candidate', rec,
    'reconstructions/incomplete-v1.5.0/setup_tf2_bazzite.py')
GAPS.append({'id': 'version_1_5_0', 'message': 544,
             'detail': 'The v1.5.0 edit expects the missing v1.4.0 baseline. Only an incomplete candidate is archived. The exact installer remains unavailable.',
             'unmatched_replacements': failed})
t = patch_tree(548)
candidate_tests, rec = replacements(tests, t, permissive=True)
put(548, '/mnt/data/test_setup_tf2_bazzite.py', candidate_tests, 'partial_static_candidate', rec,
    'reconstructions/incomplete-v1.5.0/test_setup_tf2_bazzite.py')

# Metadata emitted by the gallery builder is a literal list, serialized by our code.
t = patch_tree(550)
huds = ast.literal_eval(next(n.value for n in t.body if isinstance(n, ast.Assign)
                            and isinstance(n.targets[0], ast.Name) and n.targets[0].id == 'huds'))
put(550, '/mnt/data/hud_preview_sources.json', json.dumps(huds, indent=2) + '\n',
    'static_reconstruction', [{'operation': 'serialize_literal_gallery_metadata', 'message': 550}])
# Keep both differently cased README originals under distinct directories on macOS.
latest_readme = (ROOT / 'heredocs/0550-2-TF2_HUD_Update_README.md').read_bytes()
put(550, '/mnt/data/TF2_HUD_UPDATE_README.md', latest_readme, 'static_reconstruction',
    [{'operation': 'copy', 'from': '/mnt/data/TF2_HUD_Update_README.md', 'message': 550}])

# Re-create the static HTML using our own renderer, the recovered literal metadata,
# and the original literal page shell. The recovered builder is never imported/run.
cards = []
esc = html.escape
for number, hud in enumerate(huds, 1):
    command = f"python3 setup_tf2_bazzite.py --update-only --hud {hud['id']} --replace-hud"
    if hud['id'] in ('maxihud', 'toonhud'):
        command += ' --hud-zip "/path/to/downloaded-hud.zip"'
    command += ' --dry-run'
    more = ''
    if hud.get('more'):
        more = '<details><summary>More published screenshots</summary>' + ''.join(
            f'<a href="{esc(u)}" target="_blank" rel="noopener noreferrer"><img src="{esc(u)}" alt="Additional {esc(hud["name"])} screenshot" loading="lazy" referrerpolicy="no-referrer"></a>'
            for u in hud['more']) + '</details>'
    # Literal card formatting transcribed from the source; only text data inserted.
    cards.append(f'''<article id="{hud['id']}">
      <div class="cardhead"><div class="number">{number:02d}</div><div><p class="eyebrow">{esc(hud['group'])}</p><h2>{esc(hud['name'])}</h2></div></div>
      <a class="shot" href="{esc(hud['image'])}" target="_blank" rel="noopener noreferrer" aria-label="Open full-size {esc(hud['name'])} screenshot">
      <img src="{esc(hud['image'])}" alt="Published {esc(hud['name'])} preview. If the image does not load, use the source gallery link below." loading="{'eager' if number < 3 else 'lazy'}" referrerpolicy="no-referrer"></a>
      <div class="body"><p>{esc(hud['caption'])}</p>
      <p class="links"><a href="{esc(hud['source'])}" target="_blank" rel="noopener noreferrer">Screenshot source / gallery</a> · <a href="{esc(hud['project'])}" target="_blank" rel="noopener noreferrer">HUD project</a></p>
      <p class="install"><code>--hud {hud['id']}</code><br>{esc(hud['install'])}</p>
      <p class="note">{esc(hud['note'])}</p>{more}
      <details><summary>Preview installation command (does not apply changes)</summary><pre>{esc(command)}</pre></details>
      </div></article>''')
nav = ''.join(f'<a href="#{hud["id"]}">{esc(hud["name"])}</a>' for hud in huds)
page_node = next(n for n in t.body if isinstance(n, ast.Assign)
                 and isinstance(n.targets[0], ast.Name) and n.targets[0].id == 'page')


def page_shell(expr):
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return expr.value
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
        return page_shell(expr.left) + page_shell(expr.right)
    if isinstance(expr, ast.Name) and expr.id == 'nav':
        return nav
    if (isinstance(expr, ast.Call) and isinstance(expr.func, ast.Attribute)
            and expr.func.attr == 'join' and isinstance(expr.func.value, ast.Constant)
            and expr.func.value.value == '' and len(expr.args) == 1
            and isinstance(expr.args[0], ast.Name) and expr.args[0].id == 'cards'):
        return ''.join(cards)
    raise ValueError('Unexpected page shell material')


put(550, '/mnt/data/TF2_HUD_Gallery.html', page_shell(page_node.value),
    'static_reconstruction', [{'operation': 'own_static_renderer', 'message': 550,
                               'note': 'Literal metadata/page shell and transcribed card template; no recovered builder execution.'}])
put(458, '/mnt/data/tf2_work/v1_3_1.diff', ''.join(difflib.unified_diff(
    baseline13b.splitlines(keepends=True), baseline131.splitlines(keepends=True),
    fromfile='v1.3.0', tofile='v1.3.1')), 'static_reconstruction',
    [{'operation': 'unified_diff_of_reconstructions', 'baselines': [398, 451]}])

# Collect named references without claiming their contents were downloaded.
refs = {}
for seq, n in enumerate(NODES, 1):
    m = n.get('message') or {}; c = m.get('content') or {}
    text = c.get('text', '') if c.get('content_type') == 'code' else '\n'.join(
        p for p in c.get('parts', []) if isinstance(p, str))
    for ref in re.findall(r'/mnt/data/[\w./_-]+', text):
        refs.setdefault(ref.rstrip('.'), []).append(seq)
GAPS.extend([
    {'id': 'visual_comparison', 'messages': [570, 573, 577],
     'detail': 'Linked TF2_HUD_Visual_Comparison.html has no full file body or rename/copy from TF2_HUD_Gallery.html. Do not invent it.'},
    {'id': 'redacted_tool_results', 'detail': '222 tool-text nodes exist; many contain only The output of this plugin was redacted. Logs, fetched JSON, image downloads, ZIPs and test results cannot be verified.'},
    {'id': 'gallery_repair', 'messages': [571, 577, 582, 589],
     'detail': 'A fetch/repair attempt is shown, but downloaded images and a completed repaired HTML file are absent.'},
    {'id': 'last_request', 'messages': [582, 606],
     'detail': 'The conversation ends with a request to handle external HUD dependencies and an intention to update. No completed new revision is available.'},
    {'id': 'sandbox_attachments',
     'detail': 'sandbox:/mnt/data links refer to the original conversation runtime, not public download URLs. Exact attachment bytes were not recovered; no content is guessed from a filename.'},
    {'id': 'generated_configuration',
     'detail': 'Generated autoexec.cfg/modules.cfg/setup_hook.cfg, class CFG migrations, manifests, downloaded HUD assets/VPKs/ZIPs and test fixtures depend on inputs or redacted outputs. Only the explicitly supplied guide CFG blocks are instantiated; other templates remain embedded in the archived scripts.'},
])

manifest = {'source_url': 'https://chatgpt.com/share/6ad6143e-d894-83e9-a306-302b4fc65c66',
            'title': SOURCE['title'], 'nodes': len(NODES), 'events': sorted(EVENTS.values(), key=lambda e: (e['source_timestamp'], e['sequence'])),
            'gaps': GAPS, 'named_references': refs}
(ROOT / 'archive-plan.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'events': len(EVENTS), 'writes': sum(len(e['writes']) for e in EVENTS.values()),
                  'gaps': len(GAPS), 'unmatched_candidate_edits': len(failed)}, indent=2))
