"""Record final access limitations and verify the installed archive without running it."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = Path('/Users/marcelofcandido/git/personal/games/competitive-tf2')
ENV = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
           GIT_COMMITTER_NAME='Codex archive import', GIT_COMMITTER_EMAIL='import@archive.invalid')
for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_CONFIG_PARAMETERS', 'GIT_CONFIG_COUNT'):
    ENV.pop(key, None)


def git(*args):
    return subprocess.run(['git', '-C', str(REPO), '-c', 'core.hooksPath=/dev/null',
                           '-c', 'core.fsmonitor=false', '-c', 'commit.gpgsign=false',
                           *args], env=ENV, capture_output=True, check=True).stdout


def jwrite(path, data):
    (REPO / path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


assert git('rev-parse', 'HEAD').decode().strip() == '1b34d7b54074c9080d9193ad99cf313dc6000667'
assert not git('status', '--porcelain')
capture = json.loads((REPO / '.provenance/capture.json').read_text())
capture.update({
    'direct_conversation_search_attempted_after_user_enabled_memory': True,
    'direct_conversation_search_content_used': False,
    'original_conversation_id': '6acfa42a-f8fc-83e8-b025-370fd5942d5b',
    'original_conversation_url': 'https://chatgpt.com/c/6acfa42a-f8fc-83e8-b025-370fd5942d5b',
    'original_context_attempt': 'Personal context is unavailable for this conversation.',
    'read_conversation_context_api': 'Not exposed in this executor.',
    'final_browser_attempt': 'Mac remains locked; authenticated attachments unavailable.',
})
jwrite('.provenance/capture.json', capture)
gap = (REPO / 'GAPS.md').read_text()
gap = gap.replace('Não houve busca direta de conversas.',
                  'Após a autorização decorrente da habilitação de memória, uma consulta de contexto restrita à conversa original retornou `Personal context is unavailable for this conversation.` neste executor; nenhum conteúdo foi recuperado por essa via. A API paginada `read_conversation_context` não está exposta aqui.')
gap += '\nO menor próximo passo é recuperar os anexos na conversa original autenticada, após desbloquear o Mac, ou extrair o histórico integral pela API disponível no thread pai. Se os anexos estiverem expirados ou substituídos, serão necessários os arquivos originais/exportação/backups correspondentes; a existência desses bytes não pode ser presumida.\n'
(REPO / 'GAPS.md').write_text(gap)
gaps = json.loads((REPO / '.provenance/gaps.json').read_text())
gaps.append({'id': 'original_context_access', 'target': capture['original_conversation_url'],
             'status': 'unavailable', 'reason': capture['original_context_attempt'],
             'paginated_api': capture['read_conversation_context_api'],
             'authenticated_browser': capture['final_browser_attempt']})
jwrite('.provenance/gaps.json', gaps)
(REPO / '.provenance/PROGRESS.md').write_bytes((ROOT / 'PROGRESS.md').read_bytes())
(REPO / '.provenance/tools/finalize_repository.py').write_bytes(Path(__file__).read_bytes())
hashes = {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted(REPO.rglob('*')) if p.is_file() and '.git' not in p.relative_to(REPO).parts
          and p != REPO / '.provenance/final-files.sha256.json'}
jwrite('.provenance/final-files.sha256.json', hashes)
git('add', '--all')
git('commit', '--amend', '--no-edit', '--no-verify')
records = json.loads((REPO / '.provenance/revisions.json').read_text())
checked = 0
for e in records:
    for w in e['writes']:
        blob = git('show', e['commit'] + ':' + w['repo_path'])
        assert hashlib.sha256(blob).hexdigest() == w['sha256']
        checked += 1
for name, digest in hashes.items():
    assert hashlib.sha256((REPO / name).read_bytes()).hexdigest() == digest
git('fsck', '--full', '--strict')
assert not git('status', '--porcelain')
assert not git('remote')
assert int(git('rev-list', '--count', 'HEAD')) == 23
dates = [int(x) for x in git('log', '--reverse', '--format=%at').splitlines()]
assert dates == sorted(dates)
summary = {'repository': str(REPO), 'head': git('rev-parse', 'HEAD').decode().strip(),
           'commits': 23, 'artifact_paths': 27, 'revision_records': checked,
           'final_files_checked': len(hashes), 'tracked_files': len(git('ls-files').splitlines()),
           'status_porcelain': '', 'remotes': '', 'fsck': 'passed --full --strict',
           'source_author_dates': 'chronological', 'completed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
           'log': git('log', '--reverse', '--format=%h %aI %s').decode()}
(ROOT / 'verification-final.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in summary.items() if k != 'log'}, ensure_ascii=False, indent=2))
print(git('status', '--short', '--branch').decode())
print(git('log', '-4', '--format=%h %aI %s').decode())
