"""Record visually verified unlock and the remaining ChatGPT authentication blocker."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = Path('/Users/marcelofcandido/git/personal/games/competitive-tf2')
OLD_HEAD = 'ac7b17d95480c9b387e73ebd70d8064afc576c72'
NOW = dt.datetime.now(dt.timezone.utc).isoformat()
TARGET = 'https://chatgpt.com/c/6acfa42a-f8fc-83e8-b025-370fd5942d5b'
ENV = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
           GIT_AUTHOR_NAME='Codex archive import', GIT_AUTHOR_EMAIL='import@archive.invalid',
           GIT_COMMITTER_NAME='Codex archive import', GIT_COMMITTER_EMAIL='import@archive.invalid')
for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_CONFIG_PARAMETERS', 'GIT_CONFIG_COUNT'):
    ENV.pop(key, None)


def git(*args):
    return subprocess.run(['git', '-C', str(REPO), '-c', 'core.hooksPath=/dev/null',
                           '-c', 'core.fsmonitor=false', '-c', 'commit.gpgsign=false',
                           *args], env=ENV, capture_output=True, check=True).stdout


def jwrite(relative, value):
    path = REPO / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


assert git('rev-parse', 'HEAD').decode().strip() == OLD_HEAD
assert not git('status', '--porcelain'), 'User changes detected; refusing to overwrite.'
prior = git('rev-list', '--reverse', 'HEAD').decode().splitlines()
assert len(prior) == 26
evidence_path = '.provenance/browser-access-attempts/unlocked-authentication-required.json'
evidence = {
    'recorded_at_utc': NOW, 'computer': 'NEBULOSA-2.local', 'requested_conversation_url': TARGET,
    'mac_unlocked': True, 'unlock_verification': 'Safari window observed through accessibility state and screenshot; no lock screen.',
    'safari_available': True, 'original_conversation_navigation_attempted': True,
    'navigation_result': 'Redirected to unauthenticated chatgpt.com landing page.',
    'observed_authenticated_session': False,
    'current_safari_ui': 'Log in or sign up dialog with Continue with Google, Continue with Apple, phone and blank email field.',
    'user_login_pending': True, 'required_user_step': 'Log into ChatGPT in the open Safari window using the account that owns the original conversation. Do not send passwords to the assistant.',
    'zen_attempt': {
        'initial_app_read': 'Timed out and reset the computer-use kernel.',
        'subsequent_app_read': 'Window and screenshot became readable.',
        'navigation_confirmed': False,
        'coordinate_action_result': 'Computer Use server error -10005: windowNotFoundAtPosition((75.0, 625.0))',
        'scope': 'Zen navigation/control not confirmed; no authenticated ChatGPT content or downloaded bytes obtained from Zen.'},
    'attachment_download_attempts': 0, 'new_original_files_recovered': 0,
    'new_binary_revisions_verified': 0, 'historical_attachment_identity_assumed': False,
    'recovered_code_executions': 0, 'remote_publication': False,
    'outcome': 'blocked_pending_user_authentication; not an automatic-approval denial',
    'screenshots_archived': False,
    'privacy_note': 'Only relevant UI observations are recorded; no screenshots, unrelated browser content, login credentials or cookies were archived.'}
jwrite(evidence_path, evidence)
capture = json.loads((REPO / '.provenance/capture.json').read_text())
capture['latest_browser_attempt'] = {'evidence': evidence_path, 'recorded_at_utc': NOW,
                                      'mac_unlocked_visually_verified': True,
                                      'safari_accessible': True, 'chatgpt_authentication_required': True,
                                      'new_original_files_recovered': 0}
jwrite('.provenance/capture.json', capture)
gaps = json.loads((REPO / '.provenance/gaps.json').read_text())
gaps.append({'id': 'authenticated_browser_requires_chatgpt_login',
             'status': 'pending_user_authentication', 'target': TARGET,
             'mac_unlocked_visually_verified': True,
             'detail': 'Mac unlock is confirmed. Safari is accessible, but the original conversation redirects to a logged-out landing page. Login dialog is open. No attachment bytes downloaded.',
             'next_step': evidence['required_user_step'], 'evidence': evidence_path})
jwrite('.provenance/gaps.json', gaps)
(REPO / 'BROWSER_ACCESS.md').write_text('''# Acesso ao navegador e anexos originais

O **Mac foi confirmado visualmente como desbloqueado**. O Safari está acessível. A navegação para a conversa original redirecionou ao ChatGPT sem sessão autenticada; o diálogo **“Log in or sign up”** está aberto.

O bloqueio atual é **login no ChatGPT**, não a tela de bloqueio do macOS. O próximo passo é entrar na janela aberta do Safari com a mesma conta da conversa original. Não é necessário enviar senha ao assistente.

O Zen também foi inspecionado. Sua primeira leitura excedeu o tempo limite; depois a janela ficou legível, mas a navegação não foi confirmada e um clique retornou `windowNotFoundAtPosition`. Nenhum conteúdo autenticado ou anexo foi obtido por essa via.

**Nenhum anexo foi baixado nesta etapa e nenhuma revisão binária nova foi confirmada.** A identidade de versões antigas que compartilham o mesmo caminho continuará sendo verificada por evidência de conteúdo, sem suposição a partir do nome ou do rótulo do link.

Os 26 commits anteriores e os 42 registros de revisão foram preservados. Este commit acrescenta somente o estado de acesso e o bloqueio restante. Nenhum instalador, teste ou CFG recuperado foi executado. Não houve publicação remota.

A evidência textual está em `.provenance/browser-access-attempts/unlocked-authentication-required.json`. Capturas de tela, credenciais, cookies e conteúdo de outras abas não foram arquivados.
''')
readme = (REPO / 'README.md').read_text()
readme = readme.replace('**4 commits de documentação/evidências** (**26 commits no total**)',
                        '**5 commits de documentação/evidências** (**27 commits no total**)')
marker = '## Consultar o histórico'
note = ('A verificação posterior do computador confirmou visualmente o **Mac desbloqueado e o Safari acessível**. A conversa original, porém, abre o ChatGPT sem autenticação. O diálogo de login está aberto; os anexos ainda dependem de entrar com a mesma conta da conversa. Veja [BROWSER_ACCESS.md](BROWSER_ACCESS.md). Nenhum novo arquivo foi recuperado nessa tentativa.\n\n')
assert marker in readme; readme = readme.replace(marker, note + marker)
(REPO / 'README.md').write_text(readme)
gaps_doc = (REPO / 'GAPS.md').read_text()
gaps_doc += ('\nVerificação posterior do navegador: o Mac foi confirmado visualmente como desbloqueado e o Safari está acessível. A tentativa de abrir a conversa original redirecionou ao ChatGPT sem sessão; o diálogo de login está aberto. O bloqueio atual é autenticação no ChatGPT, pendente de ação do usuário. Nenhum anexo foi baixado. Os registros anteriores de Mac bloqueado permanecem como histórico, não como descrição do estado atual. Veja `BROWSER_ACCESS.md`.\n')
(REPO / 'GAPS.md').write_text(gaps_doc)
progress = (REPO / '.provenance/PROGRESS.md').read_text()
progress += (f'\n- {NOW}: Mac desbloqueado confirmado visualmente no Safari; aplicativos disponíveis sem erro de tela bloqueada.\n'
             '- Safari acessível; navegação para conversa original redirecionou a chatgpt.com sem autenticação. Diálogo de login aberto; pendente entrar com a mesma conta.\n'
             '- Zen ficou legível após timeout inicial, mas navegação não foi confirmada e houve windowNotFoundAtPosition. Nenhum anexo baixado, versão nova inventada ou script recuperado executado.\n')
(REPO / '.provenance/PROGRESS.md').write_text(progress)
(ROOT / 'PROGRESS.md').write_text(progress)
(REPO / '.provenance/tools/record_browser_auth_block.py').write_bytes(Path(__file__).read_bytes())
hashes = {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted(REPO.rglob('*')) if p.is_file() and '.git' not in p.relative_to(REPO).parts
          and p != REPO / '.provenance/final-files.sha256.json'}
jwrite('.provenance/final-files.sha256.json', hashes)
git('add', '--all')
git('commit', '--no-verify', '-m', 'docs: verify Mac unlock and record ChatGPT login blocker',
    '-m', 'Safari is visually accessible but the original conversation redirects to a logged-out page. Login dialog is open. No original attachments downloaded; all 26 prior commits preserved.')
current = git('rev-list', '--reverse', 'HEAD').decode().splitlines()
assert len(current) == 27 and current[:26] == prior
assert git('rev-parse', 'HEAD^').decode().strip() == OLD_HEAD
checked = 0
for event in json.loads((REPO / '.provenance/revisions.json').read_text()):
    for write in event['writes']:
        data = git('show', event['commit'] + ':' + write['repo_path'])
        assert hashlib.sha256(data).hexdigest() == write['sha256']
        checked += 1
for name, sha in hashes.items():
    assert hashlib.sha256((REPO / name).read_bytes()).hexdigest() == sha
assert not git('status', '--porcelain')
assert not git('remote')
git('fsck', '--full', '--strict')
dates = [int(d) for d in git('log', '--reverse', '--format=%at').splitlines()]
assert dates == sorted(dates)
summary = {'repository': str(REPO), 'head': git('rev-parse', 'HEAD').decode().strip(),
           'parent_head_preserved': OLD_HEAD, 'prior_commits_preserved': 26, 'commits': 27,
           'artifact_paths': 27, 'revision_records': checked, 'new_original_files_recovered': 0,
           'mac_unlocked_visually_verified': True, 'safari_accessible': True,
           'chatgpt_authentication_required': True, 'blocker_status': 'pending_user_authentication',
           'login_dialog_open': True, 'attachment_downloads': 0,
           'final_files_checked': len(hashes), 'tracked_files': len(git('ls-files').splitlines()),
           'status_porcelain': '', 'remotes': '', 'fsck': 'passed --full --strict',
           'source_author_dates': 'chronological', 'completed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
           'log': git('log', '--reverse', '--format=%h %aI %s').decode()}
(ROOT / 'verification-final.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in summary.items() if k != 'log'}, ensure_ascii=False, indent=2))
print(git('status', '--short', '--branch').decode())
print(git('log', '-2', '--format=%h %aI %s').decode())
