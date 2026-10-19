"""Append a documented correction from the parent's direct-conversation evidence."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = Path('/Users/marcelofcandido/git/personal/games/competitive-tf2')
OLD_HEAD = 'cdc4a357f4228985b042275dd0c6a308caa3666c'
MESSAGE_ID = 'e4b8944c-7916-4302-8016-463828ec503e'
CONVERSATION_ID = '6acfa42a-f8fc-83e8-b025-370fd5942d5b'
MESSAGE_URL = f'https://chatgpt.com/c/{CONVERSATION_ID}?messageId={MESSAGE_ID}'
SOURCE_TIME = '2026-10-19T13:12:17Z'
NOW = dt.datetime.now(dt.timezone.utc).isoformat()
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
prior_commits = git('rev-list', '--reverse', 'HEAD').decode().splitlines()
assert len(prior_commits) == 23
source = json.loads((REPO / '.provenance/source/conversation.json').read_text())
nodes = source['linear_conversation']
assert MESSAGE_ID not in source['mapping']
assert not any(n.get('id') == MESSAGE_ID or (n.get('message') or {}).get('id') == MESSAGE_ID for n in nodes)
assert '1.6.0' not in json.dumps(source, ensure_ascii=False)
assert source['backing_conversation_id'] == CONVERSATION_ID
current = source['mapping'][source['current_node']]['message']
current_time = dt.datetime.fromtimestamp(current['create_time'], dt.timezone.utc).isoformat()

evidence_path = '.provenance/supplemental-evidence/v1.6.0-parent-report.json'
report = {
    'evidence_type': 'parent_report_of_direct_conversation_read',
    'received_at_utc': NOW,
    'original_conversation_id': CONVERSATION_ID,
    'original_message_id': MESSAGE_ID,
    'original_message_url': MESSAGE_URL,
    'reported_source_timestamp_utc': SOURCE_TIME,
    'full_original_message_received_by_executor': False,
    'original_attachment_bytes_received': False,
    'advertised_version': '1.6.0',
    'advertised_attachment_filenames': ['setup_tf2_bazzite.py', 'test_setup_tf2_bazzite.py', 'TF2_HUD_Update_README.md'],
    'reported_features': ['--hud-info all', '--fetch-hud middlemann --output', '--build-gallery'],
    'reported_test_count': 103,
    'test_claim_status': 'reported by source, not rerun or independently verified',
    'gallery_clarification': 'The message explicitly says screenshot binaries could not be downloaded. The offline gallery must be built on the gaming PC; a repaired offline gallery was not delivered as an attachment.',
    'shared_snapshot_comparison': {
        'same_backing_conversation': True,
        'snapshot_nodes': len(nodes),
        'snapshot_current_node': source['current_node'],
        'snapshot_current_node_timestamp_utc': current_time,
        'later_message_in_mapping': False,
        'later_message_in_linear_conversation': False,
        'literal_version_1_6_0_present': False,
        'conclusion': 'The public shared data is an earlier snapshot of the same original conversation and does not include the later v1.6.0 announcement.'
    },
    'parent_message_verbatim': 'Leitura direta funciona no pai. Encontrei mensagem posterior/atual que precisa constar no inventário: https://chatgpt.com/c/6acfa42a-f8fc-83e8-b025-370fd5942d5b?messageId=e4b8944c-7916-4302-8016-463828ec503e ,19/10/2026 13:12:17UTC, anuncia v1.6.0 de setup_tf2_bazzite.py, 103 testes e links dos mesmos test_setup_tf2_bazzite.py e TF2_HUD_Update_README.md. Descreve --hud-info all, --fetch-hud middlemann --output e --build-gallery. Importante: afirma explicitamente que não conseguiu baixar binários de screenshots e que a galeria offline precisa ser construída no PC; o anexo anterior NÃO é galeria já reparada. Portanto não classifique uma galeria reparada inexistente como anexo faltante. Revise GAPS/inventário para incluir v1.6.0 anunciado se não consta, sem inventar seu conteúdo. Confirme se dados compartilhados cobrem essa mensagem ou são outra versão da conversa. A busca só fornece texto, não bytes dos anexos. Posso enviar o texto integral dessa mensagem se precisar. Preserve commits anteriores e adicione correção documentada.'
}
jwrite(evidence_path, report)
jwrite('.provenance/announced-revisions.json', [
    {'version': '1.4.0', 'evidence': 'shared snapshot message sequence 468',
     'artifact_filenames': ['setup_tf2_bazzite.py'], 'content_status': 'original_bytes_unavailable',
     'note': 'The preceding visible source edit sets 1.3.1; the transition is absent.'},
    {'version': '1.5.0', 'evidence': 'shared snapshot messages 544, 548, 550, 570',
     'artifact_filenames': ['setup_tf2_bazzite.py', 'test_setup_tf2_bazzite.py', 'TF2_HUD_Update_README.md'],
     'content_status': 'original_installer_and_test_bytes_unavailable',
     'note': 'Literal README and change scripts are archived. Installer/test candidates are explicitly incomplete.'},
    {'version': '1.6.0', 'evidence': evidence_path, 'source_message_id': MESSAGE_ID,
     'source_message_url': MESSAGE_URL, 'source_timestamp_utc': SOURCE_TIME,
     'artifact_filenames': report['advertised_attachment_filenames'],
     'content_status': 'announcement_only_original_bytes_unavailable',
     'note': 'Reported by the parent after a direct read of the original conversation; absent from the public snapshot. No artifact was fabricated.'}
])

readme = (REPO / 'README.md').read_text()
readme = readme.replace('e um commit final de documentação/evidências.',
                        'e **2 commits de documentação/evidências** (**24 commits no total**).')
readme = readme.replace('**A fonte não permite recuperar exatamente v1.4.0 e v1.5.0**,',
                        '**Os bytes originais completos de v1.4.0, v1.5.0 e v1.6.0 não foram recuperados**,')
needle = 'Conteúdos literais vieram de heredocs/blocos fornecidos no chat;'
addition = (f'Uma leitura posterior da conversa original, relatada pelo thread pai, identificou o [anúncio de v1.6.0]({MESSAGE_URL}) em **19/10/2026 às 13:12:17 UTC**, com 103 testes relatados e as opções `--hud-info all`, `--fetch-hud middlemann --output` e `--build-gallery`. Essa mensagem **não consta nos 615 nós da captura pública**, que é um estado anterior da mesma conversa. A evidência suplementar é um relato identificado; o texto integral e os bytes dos anexos não foram recebidos aqui. O anúncio esclarece que os binários de screenshots não puderam ser baixados e que a galeria offline deveria ser construída no PC. **Não existe uma galeria já reparada a classificar como anexo faltante.**\n\n')
assert needle in readme
readme = readme.replace(needle, addition + needle)
(REPO / 'README.md').write_text(readme)

gaps = (REPO / 'GAPS.md').read_text()
old = '- **Reparo das imagens:** aparecem a reclamação e uma tentativa de buscar imagens, mas os bytes baixados e a galeria reparada estão ausentes. URLs atuais não foram usadas para inventar cópias históricas.'
new = '- **Galeria offline:** o anúncio posterior de v1.6.0 esclarece que os binários de screenshots não puderam ser baixados e que a galeria offline deve ser construída no PC com `--build-gallery`. Uma galeria já reparada não foi entregue; ela não é um anexo faltante. O corpo original de `TF2_HUD_Visual_Comparison.html` segue indisponível, conforme a lacuna distinta acima. URLs atuais não foram usadas para inventar cópias históricas.'
assert old in gaps; gaps = gaps.replace(old, new)
old = '- **Pedido final:** a conversa termina com a solicitação de tratar dependências externas dos HUDs e uma intenção de atualizar. Nenhuma nova revisão concluída está disponível.'
new = f'- **Cobertura da captura e v1.6.0:** a captura pública de 615 nós termina antes da [mensagem original `{MESSAGE_ID}`]({MESSAGE_URL}), de **19/10/2026 às 13:12:17 UTC**. Essa mensagem anuncia `setup_tf2_bazzite.py` v1.6.0, 103 testes e novas revisões dos anexos `test_setup_tf2_bazzite.py` e `TF2_HUD_Update_README.md`. Os recursos anunciados incluem `--hud-info all`, `--fetch-hud middlemann --output` e `--build-gallery`. O texto foi consultado diretamente pelo pai e relatado a este executor; os bytes desses anexos e o texto integral da mensagem não foram recebidos. Não há versão v1.6.0 reconstruída ou inventada neste repositório.'
assert old in gaps; gaps = gaps.replace(old, new)
gaps += '\nCorreção acrescentada em commit próprio: os 23 commits existentes foram preservados. O anúncio v1.6.0 está em `.provenance/announced-revisions.json` e a origem do relato em `.provenance/supplemental-evidence/v1.6.0-parent-report.json`. A falha da consulta de contexto descrita acima se aplica somente a este executor; a leitura no pai funciona, mas a busca fornece texto, não bytes dos anexos.\n'
(REPO / 'GAPS.md').write_text(gaps)

records = json.loads((REPO / '.provenance/gaps.json').read_text())
for entry in records:
    if entry['id'] == 'gallery_repair':
        entry.update(status='not_a_missing_attachment',
                     detail=report['gallery_clarification'], supplementary_evidence=evidence_path)
    if entry['id'] == 'last_request':
        entry.update(id='snapshot_coverage', status='earlier_public_snapshot',
                     detail='The public snapshot ends during the dependency follow-up. The original conversation later contains a v1.6.0 announcement at 2026-10-19T13:12:17Z, absent from the public snapshot.',
                     later_message_id=MESSAGE_ID, supplementary_evidence=evidence_path)
    if entry['id'] == 'original_context_access':
        entry['scope'] = 'executor_only; parent direct-conversation reading works but does not supply attachment bytes'
records.append({'id': 'version_1_6_0', 'status': 'announced_original_bytes_unavailable',
                'message_id': MESSAGE_ID, 'source_timestamp_utc': SOURCE_TIME,
                'artifact_filenames': report['advertised_attachment_filenames'],
                'detail': 'Later announcement of v1.6.0, 103 tests and new CLI features. No original file bytes supplied to this executor. No synthetic v1.6.0 artifact created.',
                'supplementary_evidence': evidence_path})
jwrite('.provenance/gaps.json', records)

references = json.loads((REPO / '.provenance/references.json').read_text())
for entry in references:
    if entry['original_path'] in ['/mnt/data/' + name for name in report['advertised_attachment_filenames']]:
        entry['later_announcements'] = [{'version': '1.6.0', 'message_id': MESSAGE_ID,
                                         'content_status': 'original_bytes_unavailable', 'evidence': evidence_path}]
jwrite('.provenance/references.json', references)
capture = json.loads((REPO / '.provenance/capture.json').read_text())
capture['supplemental_source_comparison'] = report['shared_snapshot_comparison']
capture['later_announced_version'] = {'version': '1.6.0', 'message_id': MESSAGE_ID,
                                    'timestamp_utc': SOURCE_TIME, 'content_available': False,
                                    'evidence': evidence_path}
jwrite('.provenance/capture.json', capture)

revisions = (REPO / 'REVISIONS.md').read_text()
revisions += (f'\n## Anúncio posterior sem bytes recuperados\n\n'
              f'Em **{SOURCE_TIME}**, a [mensagem original `{MESSAGE_ID}`]({MESSAGE_URL}) anuncia **v1.6.0**, uma suíte de **103 testes** e revisões dos mesmos três nomes: `setup_tf2_bazzite.py`, `test_setup_tf2_bazzite.py` e `TF2_HUD_Update_README.md`. A leitura foi relatada pelo pai; o texto integral e os bytes não foram recebidos. O inventário `.provenance/announced-revisions.json` registra esse anúncio sem contá-lo como arquivo recuperado.\n\n'
              'A captura pública é anterior e não contém essa mensagem. O anúncio também confirma que a galeria offline precisa ser construída no PC; uma galeria já reparada não foi entregue como anexo. Os 42 registros e 27 caminhos de artefatos acima permanecem iguais. A correção foi acrescentada em um novo commit, preservando os 23 anteriores.\n')
(REPO / 'REVISIONS.md').write_text(revisions)
progress = (REPO / '.provenance/PROGRESS.md').read_text()
progress += (f'\n- {NOW}: evidência suplementar do pai registra anúncio original de v1.6.0 ({SOURCE_TIME}, mensagem {MESSAGE_ID}), 103 testes relatados e opções adicionais. Sem bytes dos anexos.\n'
             f'- Comparação local: mesma conversa original; mensagem v1.6.0 ausente dos 615 nós do compartilhamento; último nó da captura em {current_time}.\n'
             '- Corrigido: galeria offline deveria ser construída no PC, não foi entregue como anexo reparado. Commit de correção novo; histórico anterior preservado.\n')
(REPO / '.provenance/PROGRESS.md').write_text(progress)
(ROOT / 'PROGRESS.md').write_text(progress)
(REPO / '.provenance/tools/correct_v1_6_inventory.py').write_bytes(Path(__file__).read_bytes())

hashes = {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted(REPO.rglob('*')) if p.is_file() and '.git' not in p.relative_to(REPO).parts
          and p != REPO / '.provenance/final-files.sha256.json'}
jwrite('.provenance/final-files.sha256.json', hashes)
git('add', '--all')
git('commit', '--no-verify', '-m', 'docs: record later v1.6.0 announcement and correct offline gallery status',
    '-m', f'Supplemental evidence: {MESSAGE_URL}\nSource timestamp: {SOURCE_TIME}\nPublic snapshot lacks this message. No attachment bytes supplied; no code version fabricated. Prior commits preserved.')
new_commits = git('rev-list', '--reverse', 'HEAD').decode().splitlines()
assert new_commits[:len(prior_commits)] == prior_commits and len(new_commits) == 24
assert git('rev-parse', 'HEAD^').decode().strip() == OLD_HEAD
blob_checks = 0
for entry in json.loads((REPO / '.provenance/revisions.json').read_text()):
    for write in entry['writes']:
        data = git('show', entry['commit'] + ':' + write['repo_path'])
        assert hashlib.sha256(data).hexdigest() == write['sha256']
        blob_checks += 1
for name, digest in hashes.items():
    assert hashlib.sha256((REPO / name).read_bytes()).hexdigest() == digest
assert not git('status', '--porcelain')
assert not git('remote')
git('fsck', '--full', '--strict')
dates = [int(d) for d in git('log', '--reverse', '--format=%at').splitlines()]
assert dates == sorted(dates)
summary = {'repository': str(REPO), 'head': git('rev-parse', 'HEAD').decode().strip(),
           'parent_head_preserved': OLD_HEAD, 'prior_commits_preserved': 23, 'commits': 24,
           'artifact_paths': 27, 'revision_records': blob_checks, 'announced_latest_version': '1.6.0',
           'version_1_6_original_bytes_available': False,
           'share_comparison': report['shared_snapshot_comparison'],
           'final_files_checked': len(hashes), 'tracked_files': len(git('ls-files').splitlines()),
           'status_porcelain': '', 'remotes': '', 'fsck': 'passed --full --strict',
           'source_author_dates': 'chronological', 'completed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
           'log': git('log', '--reverse', '--format=%h %aI %s').decode()}
(ROOT / 'verification-final.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in summary.items() if k != 'log'}, ensure_ascii=False, indent=2))
print(git('status', '--short', '--branch').decode())
print(git('log', '-3', '--format=%h %aI %s').decode())
