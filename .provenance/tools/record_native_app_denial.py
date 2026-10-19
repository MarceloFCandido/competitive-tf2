"""Record the native ChatGPT app control denial without retrying or bypassing it."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = Path('/Users/marcelofcandido/git/personal/games/competitive-tf2')
OLD_HEAD = '2532ce91b8a6260d70fd9db2352772b8d3fc6afa'
NOW = dt.datetime.now(dt.timezone.utc).isoformat()
META = json.loads((ROOT / 'chatgpt-app-installation-metadata.json').read_text())
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
    target = REPO / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


assert git('rev-parse', 'HEAD').decode().strip() == OLD_HEAD
assert not git('status', '--porcelain'), 'User changes detected; refusing to overwrite.'
prior = git('rev-list', '--reverse', 'HEAD').decode().splitlines()
assert len(prior) == 27
assert META['installations'] == [{'path': '/Applications/ChatGPT.app', 'bundle_id': 'com.openai.codex',
                                  'display_name': 'ChatGPT', 'bundle_name': 'ChatGPT', 'version': '26.1013.40934'}]
evidence_path = '.provenance/browser-access-attempts/native-chatgpt-app-denied.json'
evidence = {
    'recorded_at_utc': NOW, 'user_requested_route': 'Native ChatGPT app on the Mac',
    'intended_conversation_url': 'https://chatgpt.com/c/6acfa42a-f8fc-83e8-b025-370fd5942d5b',
    'attempted_action': 'cua.getApp("com.openai.codex")',
    'target_app_path': '/Applications/ChatGPT.app', 'target_bundle_id': 'com.openai.codex',
    'outcome': 'denied_before_app_inspection',
    'reason_verbatim': "Computer Use is not allowed to use the app 'com.openai.codex' for safety reasons.",
    'installation_metadata': META,
    'session_state': 'not verified because app control was denied',
    'conversation_opened_in_app_by_assistant': False, 'attachment_download_attempts_in_app': 0,
    'new_original_files_recovered': 0, 'new_binary_versions_verified': 0,
    'denied_action_retried': False, 'alternate_alias_or_automation_bypass_attempted': False,
    'credentials_or_tokens_extracted': False,
    'app_download_capability': 'unknown; the denial does not prove the app lacks download support',
    'next_minimal_step': 'User downloads the current installer, test suite and README from the authenticated app to Downloads; assistant can then inspect bytes, hash and archive them. Historical links remain unverified until content evidence is available.'}
jwrite(evidence_path, evidence)
capture = json.loads((REPO / '.provenance/capture.json').read_text())
capture['native_app_attempt'] = {'evidence': evidence_path, 'bundle_id': 'com.openai.codex',
                                'app_path': '/Applications/ChatGPT.app', 'status': 'denied_before_app_inspection',
                                'session_verified': False, 'new_original_files_recovered': 0}
jwrite('.provenance/capture.json', capture)
gaps = json.loads((REPO / '.provenance/gaps.json').read_text())
gaps.append({'id': 'native_chatgpt_app_control_denied', 'status': 'denied',
             'action': evidence['attempted_action'], 'target': '/Applications/ChatGPT.app',
             'bundle_id': 'com.openai.codex', 'reason': evidence['reason_verbatim'],
             'session_status': 'unverified', 'app_download_capability': 'unverified',
             'next_step': evidence['next_minimal_step'], 'evidence': evidence_path})
jwrite('.provenance/gaps.json', gaps)
browser_doc = (REPO / 'BROWSER_ACCESS.md').read_text()
browser_doc += '''
## Tentativa pelo app ChatGPT

A pedido do usuário, foi tentada a seleção do app nativo. A ferramenta recusou a operação antes de inspecionar a janela:

> Computer Use is not allowed to use the app 'com.openai.codex' for safety reasons.

Os metadados de `/Applications/ChatGPT.app/Contents/Info.plist` confirmam que o app se chama **ChatGPT**, usa o identificador **`com.openai.codex`** e está na versão **26.1013.40934**. Nos dois diretórios padrão verificados (`/Applications` e `~/Applications`), não foi encontrada outra instalação com nome ChatGPT/Codex. Foram lidos somente esses metadados; não foram extraídos credenciais, cookies, tokens ou dados internos de sessão.

**A sessão do app e sua capacidade de baixar anexos não puderam ser verificadas.** A recusa é da ferramenta de controle; ela não demonstra que o app seja incapaz de fornecer os arquivos. A operação negada não foi repetida por outro nome nem contornada por outra automação.

Nenhum anexo foi baixado pelo app. Para usar o app autenticado como fonte, o menor passo é o usuário baixar o instalador, os testes e o README atuais para `Downloads`. Os bytes recebidos poderão então ser conferidos e versionados. Links antigos com o mesmo caminho não serão tratados como versões históricas distintas sem evidência de conteúdo. O HTML e eventuais versões antigas continuam dependendo de sua disponibilidade efetiva.

Evidência: `.provenance/browser-access-attempts/native-chatgpt-app-denied.json`.
'''
(REPO / 'BROWSER_ACCESS.md').write_text(browser_doc)
readme = (REPO / 'README.md').read_text()
readme = readme.replace('**5 commits de documentação/evidências** (**27 commits no total**)',
                        '**6 commits de documentação/evidências** (**28 commits no total**)')
note = ('A via do **app ChatGPT** também foi tentada a pedido do usuário. O app instalado é `/Applications/ChatGPT.app`, identificador `com.openai.codex`; a ferramenta de controle recusou acessá-lo por segurança. A sessão e os downloads do app não puderam ser inspecionados. Nenhum arquivo foi recuperado por essa tentativa; o usuário pode baixar os anexos pelo app para `Downloads`, permitindo posterior verificação dos bytes. A recusa e os metadados estão documentados em [BROWSER_ACCESS.md](BROWSER_ACCESS.md).\n\n')
marker = '## Consultar o histórico'
assert marker in readme; readme = readme.replace(marker, note + marker)
(REPO / 'README.md').write_text(readme)
gaps_doc = (REPO / 'GAPS.md').read_text()
gaps_doc += ('\nTentativa posterior pelo app nativo ChatGPT: a operação `cua.getApp("com.openai.codex")` foi negada pela ferramenta de controle por segurança. Metadados confirmam `/Applications/ChatGPT.app` com esse identificador. A sessão e a capacidade de download do app permanecem não verificadas; não houve extração de tokens, contorno da recusa ou download de anexos. Para usar essa via, o usuário pode baixar os arquivos pelo app para `Downloads`. O bloqueio é da automação, não evidência de ausência de suporte do aplicativo a anexos.\n')
(REPO / 'GAPS.md').write_text(gaps_doc)
progress = (REPO / '.provenance/PROGRESS.md').read_text()
progress += (f'\n- {NOW}: solicitado uso do app ChatGPT; seleção de com.openai.codex recusada por segurança antes da inspeção da janela.\n'
             '- Info.plist confirma /Applications/ChatGPT.app, nome ChatGPT, bundle com.openai.codex, versão 26.1013.40934. Nenhuma instalação separada encontrada nos diretórios padrão verificados. Somente metadados lidos.\n'
             '- Sessão do app e downloads não verificados; operação negada não repetida ou contornada. Zero anexos/versões novos; nenhum instalador executado, nenhuma credencial ou token extraído. Próximo passo mínimo: baixar os anexos pelo app autenticado para Downloads.\n')
(REPO / '.provenance/PROGRESS.md').write_text(progress)
(ROOT / 'PROGRESS.md').write_text(progress)
(REPO / '.provenance/tools/record_native_app_denial.py').write_bytes(Path(__file__).read_bytes())
hashes = {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted(REPO.rglob('*')) if p.is_file() and '.git' not in p.relative_to(REPO).parts
          and p != REPO / '.provenance/final-files.sha256.json'}
jwrite('.provenance/final-files.sha256.json', hashes)
git('add', '--all')
git('commit', '--no-verify', '-m', 'docs: record native ChatGPT app control denial and installed metadata',
    '-m', 'Computer Use denied com.openai.codex before inspection. Info.plist identifies that app as /Applications/ChatGPT.app. No credential/token extraction, bypass, attachment download or binary-version claim. All 27 prior commits preserved.')
current = git('rev-list', '--reverse', 'HEAD').decode().splitlines()
assert len(current) == 28 and current[:27] == prior
assert git('rev-parse', 'HEAD^').decode().strip() == OLD_HEAD
checked = 0
for event in json.loads((REPO / '.provenance/revisions.json').read_text()):
    for write in event['writes']:
        assert hashlib.sha256(git('show', event['commit'] + ':' + write['repo_path'])).hexdigest() == write['sha256']
        checked += 1
for name, sha in hashes.items():
    assert hashlib.sha256((REPO / name).read_bytes()).hexdigest() == sha
assert not git('status', '--porcelain')
assert not git('remote')
git('fsck', '--full', '--strict')
summary = {'repository': str(REPO), 'head': git('rev-parse', 'HEAD').decode().strip(),
           'parent_head_preserved': OLD_HEAD, 'prior_commits_preserved': 27, 'commits': 28,
           'artifact_paths': 27, 'revision_records': checked, 'new_original_files_recovered': 0,
           'native_app_action': evidence['attempted_action'], 'native_app_status': 'denied_before_app_inspection',
           'native_app_reason': evidence['reason_verbatim'], 'native_app_session_verified': False,
           'native_app_downloads': 0, 'credentials_or_tokens_extracted': False,
           'final_files_checked': len(hashes), 'tracked_files': len(git('ls-files').splitlines()),
           'status_porcelain': '', 'remotes': '', 'fsck': 'passed --full --strict',
           'completed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
           'log': git('log', '--reverse', '--format=%h %aI %s').decode()}
(ROOT / 'verification-final.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in summary.items() if k != 'log'}, ensure_ascii=False, indent=2))
print(git('status', '--short', '--branch').decode())
print(git('log', '-2', '--format=%h %aI %s').decode())
