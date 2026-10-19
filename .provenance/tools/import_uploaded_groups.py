"""Append hash-verified original uploads v1.5.0 then v1.6.0; never run source code."""
from pathlib import Path
import ast
import datetime as dt
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = Path('/Users/marcelofcandido/git/personal/games/competitive-tf2')
OLD_HEAD = '6e2dd25bceffe039ee15bf70fea7c346dc6af03a'
ENV = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
           GIT_AUTHOR_NAME='Codex archive import', GIT_AUTHOR_EMAIL='import@archive.invalid',
           GIT_COMMITTER_NAME='Codex archive import', GIT_COMMITTER_EMAIL='import@archive.invalid')
for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_CONFIG_PARAMETERS', 'GIT_CONFIG_COUNT', 'GIT_AUTHOR_DATE', 'GIT_COMMITTER_DATE'):
    ENV.pop(key, None)


def git(*args):
    return subprocess.run(['git', '-C', str(REPO), '-c', 'core.hooksPath=/dev/null',
                           '-c', 'core.fsmonitor=false', '-c', 'commit.gpgsign=false', *args],
                          env=ENV, capture_output=True, check=True).stdout


def jwrite(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    assert git('rev-parse', 'HEAD').decode().strip() == OLD_HEAD
    assert not git('status', '--porcelain'), 'Existing changes detected; refusing to overwrite.'
    prior = git('rev-list', '--reverse', 'HEAD').decode().splitlines()
    assert len(prior) == 30 and not git('remote')
    old_hashes = json.loads((REPO / '.provenance/final-files.sha256.json').read_text())
    for name, sha in old_hashes.items():
        assert hashlib.sha256((REPO / name).read_bytes()).hexdigest() == sha, name
    announcements = json.loads((REPO / '.provenance/announced-revisions.json').read_text())
    prepared = []
    for group, version, origin_id in [(2, '1.5.0', '454439cb-235e-4787-96c0-19a40f8c2b1d'),
                                      (3, '1.6.0', 'e4b8944c-7916-4302-8016-463828ec503e')]:
        pending_path = ROOT / f'pending-user-upload-turn-{group}.json'
        pending = json.loads(pending_path.read_text())
        incoming = Path(pending['incoming_directory'])
        transfer = json.loads((incoming / 'transfer-verified.json').read_text())
        inspection = json.loads((ROOT / f'upload-turn-{group}-inspection.json').read_text())
        assert len(inspection) == (4 if group == 2 else 3)
        assert next(i for i in inspection if i['canonical_name'] == 'setup_tf2_bazzite.py')['declared_SCRIPT_VERSION'] == [version]
        assert version in next(i for i in inspection if i['canonical_name'].startswith('test_'))['module_docstring']
        assert version in next(i for i in inspection if i['canonical_name'].endswith('.md'))['heading']
        for row in inspection:
            raw = (incoming / 'decoded-originals' / row['upload_name']).read_bytes()
            assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
            assert pending['expected_hashes'][row['upload_name']] == row['sha256']
        origin = next(a for a in announcements if a['source_message_id'] == origin_id)
        prepared.append((group, version, origin, pending_path, pending, incoming, transfer, inspection))
    results = []
    for group, version, origin, pending_path, pending, incoming, transfer, inspection in prepared:
        assert not git('status', '--porcelain')
        receipt_dir = f'.provenance/user-uploads/turn-{group}-v{version}'
        assert not (REPO / receipt_dir).exists()
        event = {'sequence': f'user-upload-turn-{group}', 'message_id': origin['source_message_id'],
                 'source_timestamp': dt.datetime.fromisoformat(origin['source_timestamp_utc'].replace('Z', '+00:00')).timestamp(),
                 'source_message_url': origin['source_message_url'], 'upload_message_id': pending['source_message'],
                 'upload_label': pending['label'], 'received_and_verified_at_utc': transfer['verified_at_utc'],
                 'notes': ['Original user-uploaded bytes; version declarations inspected statically.',
                           'Version association does not prove identity with other historical links.'], 'writes': []}
        for row in inspection:
            name = row['canonical_name']
            dest = REPO / name
            assert dest.parent == REPO and not dest.is_symlink()
            if row['previous_sha256'] is None:
                assert not dest.exists()
            else:
                assert hashlib.sha256(dest.read_bytes()).hexdigest() == row['previous_sha256'], name
            raw = (incoming / 'decoded-originals' / row['upload_name']).read_bytes()
            write = {'original_path': '/mnt/data/' + name if group == 2 else None,
                     'source_filename': name, 'repo_path': name, 'upload_name': row['upload_name'],
                     'status': 'original_user_upload', 'sha256': row['sha256'], 'bytes': row['bytes'],
                     'previous_repository_sha256': row['previous_sha256'],
                     'source_upload_message_id': pending['source_message'], 'source_message_id': origin['source_message_id']}
            if group == 2:
                write['library_identity_scope'] = 'Four Library IDs supplied as a group; individual ID-to-filename mapping not provided.'
            else:
                write['library_file_id'] = next(f['library_id'] for f in pending['expected_files_metadata'] if f['upload_name'] == row['upload_name'])
                write['source_path_status'] = 'Canonical filename reported by parent; exact v1.6.0 sandbox link was not supplied. No original absolute path guessed.'
            if name.endswith('.py'):
                ast.parse(raw.decode('utf-8'), filename=name)
                write['static_syntax'] = 'parsed_without_execution'
            dest.write_bytes(raw)
            dest.chmod(0o644)
            event['writes'].append(write)
        receipt = {'receipt_type': 'original_files_uploaded_by_user', 'upload_message_id': pending['source_message'],
                   'user_label': pending['label'], 'associated_announcement_message_id': origin['source_message_id'],
                   'associated_announcement_url': origin['source_message_url'],
                   'origin_announcement_timestamp_utc': origin['source_timestamp_utc'],
                   'upload_message_timestamp_utc': pending.get('source_date'),
                   'received_and_verified_at_utc': transfer['verified_at_utc'], 'imported_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                   'library_file_ids_as_group': pending['library_ids'], 'individual_library_id_mapping_available': group == 3,
                   'version_check': {'installer_SCRIPT_VERSION': version, 'test_docstring': version, 'README_heading': version,
                                     'HTML_version_association': 'Parent-provided v1.5.0 group; HTML does not independently declare a semantic version.' if group == 2 else None},
                   'transport': {'kind': f'{transfer["total_parts"]} verified ASCII base64 parts containing gzip JSON file-byte map',
                                 'all_part_hashes_verified': True, 'all_final_file_hashes_verified': True},
                   'files': event['writes'], 'source_code_executions': 0, 'test_runs': 0,
                   'historical_link_identity_scope': 'User-uploaded originals associated by group and matching declarations with this release; no byte identity across other historical links inferred.',
                   'date_policy': 'Append-only late recovery in v1.5.0 then v1.6.0 order. Git dates record import; source dates remain in provenance. All earlier commits preserved.'}
        jwrite(REPO / receipt_dir / 'receipt.json', receipt)
        jwrite(REPO / receipt_dir / 'transport-verification.json', {'summary': transfer, 'part_manifest': json.loads((incoming / 'transfer-parts/manifest.json').read_text()), 'raw_base64_or_binary_packet_archived': False})
        jwrite(REPO / receipt_dir / 'static-inspection.json', inspection)
        jwrite(REPO / f'.provenance/events/user-upload-turn-{group}.json', event)
        git('add', '--all')
        git('commit', '--no-verify', '-m', f'archive: import user-uploaded TF2 v{version} originals' + (' and comparison HTML' if group == 2 else ''),
            '-m', f'Part hashes and final file hashes verified. Original bytes stored under canonical names; received names retained in provenance.\nSource-Message: {origin["source_message_id"]}\nSource-URL: {origin["source_message_url"]}\nUpload-Message: {pending["source_message"]}\nUpload-Label: {pending["label"]}\nDeclared-Version: {version}\nRecovered-Code-Execution: none')
        event['commit'] = git('rev-parse', 'HEAD').decode().strip()
        results.append({'group': group, 'version': version, 'event': event, 'receipt_directory': receipt_dir,
                        'static_test_methods': next(i['test_methods'] for i in inspection if i['canonical_name'].startswith('test_'))})
        pending.update(status='original_bytes_committed_pending_inventory_reconciliation', content_commit=event['commit'], version=version)
        jwrite(pending_path, pending)
        jwrite(ROOT / 'uploaded-groups-import-result.json', {'old_head': OLD_HEAD, 'prior_commits': prior, 'groups': results})
        print(json.dumps({'group': group, 'version': version, 'content_commit': event['commit'], 'files': len(event['writes'])}), flush=True)
    history = git('rev-list', '--reverse', 'HEAD').decode().splitlines()
    assert len(history) == 32 and history[:30] == prior
    assert history[30:] == [g['event']['commit'] for g in results]
    assert not git('status', '--porcelain') and not git('remote')


if __name__ == '__main__':
    main()
