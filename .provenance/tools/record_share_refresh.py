"""Record refreshed public snapshots and unchanged content in a new archival commit."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = Path('/Users/marcelofcandido/git/personal/games/competitive-tf2')
OLD_HEAD = '26961a7b00c8698be650480e62b8482626e9a112'
NOW = dt.datetime.now(dt.timezone.utc).isoformat()
REPORT = json.loads((ROOT / 'refresh-comparison-final.json').read_text())
PREFIX = '.provenance/source/refresh-20261019T145800Z'
ENV = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
           GIT_AUTHOR_NAME='Codex archive import', GIT_AUTHOR_EMAIL='import@archive.invalid',
           GIT_COMMITTER_NAME='Codex archive import', GIT_COMMITTER_EMAIL='import@archive.invalid')
for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_CONFIG_PARAMETERS', 'GIT_CONFIG_COUNT'):
    ENV.pop(key, None)


def git(*args):
    return subprocess.run(['git', '-C', str(REPO), '-c', 'core.hooksPath=/dev/null',
                           '-c', 'core.fsmonitor=false', '-c', 'commit.gpgsign=false',
                           *args], env=ENV, capture_output=True, check=True).stdout


def jwrite(relative, data):
    path = REPO / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


assert git('rev-parse', 'HEAD').decode().strip() == OLD_HEAD
assert not git('status', '--porcelain'), 'User changes detected; refusing to overwrite.'
prior = git('rev-list', '--reverse', 'HEAD').decode().splitlines()
assert len(prior) == 25
original_raw = REPO / '.provenance/source/shared-chat.html.txt'
assert hashlib.sha256(original_raw.read_bytes()).hexdigest() == REPORT['original_capture_sha256']
for request in REPORT['requests']:
    label = request['request_kind']
    raw = (ROOT / request['raw_file']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == request['raw_sha256']
    raw_destination = f'{PREFIX}/{label}.html.txt'
    target = REPO / raw_destination
    target.parent.mkdir(parents=True, exist_ok=True)
    assert not target.exists()
    target.write_bytes(raw)
    conversation_source = ROOT / f'share-conversation-{label}-refreshed.json'
    conversation_dest = f'{PREFIX}/{label}-conversation.json'
    (REPO / conversation_dest).write_bytes(conversation_source.read_bytes())
    request['archived_raw_path'] = raw_destination
    request['archived_conversation_path'] = conversation_dest
    assert request['mapping_equal'] and request['code_messages_equal']
    assert request['nodes'] == 615 and request['code_message_count'] == 89
    assert not request['new_node_ids'] and not request['changed_node_ids']
REPORT['recorded_at_utc'] = NOW
REPORT['prior_head_preserved'] = OLD_HEAD
REPORT['browser_attempted_during_refresh'] = False
REPORT['mac_unlock_assumed'] = False
comparison_path = f'{PREFIX}/comparison.json'
jwrite(comparison_path, REPORT)
(REPO / '.provenance/tools/compare_refreshed_share.py').write_bytes((ROOT / 'compare_refreshed_share.py').read_bytes())
(REPO / '.provenance/tools/record_share_refresh.py').write_bytes(Path(__file__).read_bytes())

capture = json.loads((REPO / '.provenance/capture.json').read_text())
capture['latest_refresh'] = {
    'comparison': comparison_path,
    'request_times_utc': [r['captured_at_utc'] for r in REPORT['requests']],
    'request_count': 2, 'http_statuses': [r['http_status'] for r in REPORT['requests']],
    'no_cache_recheck': True,
    'confirmed_share_metadata_update_time_utc': REPORT['requests'][0]['share_metadata_update_time_utc'],
    'message_nodes_unchanged': True, 'code_messages_unchanged': True,
    'new_artifact_revisions_recovered': 0, 'later_v1_6_message_present': False,
    'browser_attempted': False, 'mac_unlock_assumed': False}
jwrite('.provenance/capture.json', capture)
gaps = json.loads((REPO / '.provenance/gaps.json').read_text())
gaps.append({'id': 'updated_share_still_serves_same_message_content',
             'status': 'public_response_content_limitation',
             'target': REPORT['requests'][0]['source_url'],
             'metadata_update_time_utc': REPORT['requests'][0]['share_metadata_update_time_utc'],
             'detail': REPORT['evidence_conclusion'], 'evidence': comparison_path,
             'next_recovery_input': 'A shared response containing the later message/file content, or original attachment bytes from the authenticated conversation/export/backups. No guarantee is made that expired/overwritten historical bytes still exist.'})
jwrite('.provenance/gaps.json', gaps)

refresh_doc = '''# Rechecagem do compartilhamento atualizado — 19/10/2026

O mesmo link foi baixado novamente às **14:57:17 UTC** e às **14:58:00 UTC**. A segunda requisição enviou `Cache-Control: no-cache` e `Pragma: no-cache`. Ambas retornaram **HTTP 200**; a segunda resposta informou `cf-cache-status: DYNAMIC`.

A atualização do compartilhamento está registrada nos metadados: `update_time` passou de **12:59:54 UTC** para **14:55:52 UTC**. O HTML bruto mudou, mas o conteúdo de mensagens retornado permaneceu igual:

- **615 nós**, com zero adições, remoções ou alterações.
- **89 mensagens de código**, todas iguais à captura original.
- Mesmo último nó, `6300a988-456c-4c43-bc20-c2eb770c75ad`, de **12:56:12 UTC**.
- Mesmas **331 URLs**, apenas em outra ordem; nenhum novo endereço.
- Mesmas **16 referências literais únicas de mensagem + anexo** no compartilhamento.
- Mensagem posterior `e4b8944c-7916-4302-8016-463828ec503e` e rótulo `1.6.0` ainda ausentes dessas respostas.

O hash canônico do mapa de mensagens é idêntico nas três capturas: `a54469380631e1e556eaaada3431768075d292dafca15bf7d0d68b09b85906df`.

## Efeito no inventário

| Item procurado | Resultado da rechecagem |
|---|---|
| Instalador v1.4.0 | Anúncio anterior continua presente; nenhum novo corpo completo ou alteração intermediária recuperada. |
| Instalador/testes v1.5.0 | Mesmos scripts de alteração e candidatos incompletos; nenhum novo byte original confirmado. |
| v1.6.0 e seus três anexos | Continuam conhecidos apenas pelo relato da leitura direta no pai; não estão na captura pública atual. |
| Testes e READMEs | Nenhuma mensagem de código ou referência nova; os registros já preservados continuam iguais. |
| `TF2_HUD_Visual_Comparison.html` | Corpo original continua indisponível; não foi inferido a partir de outro nome. |
| Galeria offline reparada | Não foi entregue como anexo, conforme esclarecimento de v1.6.0; deveria ser construída no PC. |

**Nenhuma revisão nova de artefato foi recuperada.** Permanecem 27 caminhos e 42 registros, além de 19 referências auditadas de mensagem + anexo (16 visíveis no compartilhamento, 3 da mensagem posterior relatada pelo pai). O novo commit registra somente as capturas, a comparação e a atualização de documentação.

As respostas brutas e os JSONs decodificados estão em `.provenance/source/refresh-20261019T145800Z/`; `comparison.json` contém horários, tamanhos, hashes, diferenças e cabeçalhos selecionados. A captura original e todos os commits anteriores foram preservados. Nenhum JavaScript da página, instalador, teste ou CFG recuperado foi executado. Não foi tentado acesso ao navegador e não foi presumido desbloqueio do Mac.

## Limitação remanescente

O servidor confirma a atualização dos metadados do link, mas as respostas públicas continuam expondo o mesmo recorte antigo de mensagens. A causa não pode ser determinada somente por essas respostas. Para avançar é necessário obter uma resposta compartilhada que inclua o conteúdo posterior ou recuperar os bytes dos anexos na conversa autenticada/exportação/backups. Não é possível presumir a existência de versões históricas substituídas ou expiradas.
'''
(REPO / 'REFRESH.md').write_text(refresh_doc)
readme = (REPO / 'README.md').read_text()
readme = readme.replace('**3 commits de documentação/evidências** (**25 commits no total**)',
                        '**4 commits de documentação/evidências** (**26 commits no total**)')
paragraph = ('O compartilhamento atualizado foi consultado novamente às **14:57 e 14:58 UTC** de 19/10/2026, incluindo uma requisição com cabeçalhos de não usar cache. Embora `update_time` confirme a atualização do link às **14:55:52 UTC**, ambas as respostas mantêm exatamente os mesmos 615 nós, 89 mensagens de código e último nó de 12:56:12 UTC. **Nenhuma revisão nova foi recuperada.** Consulte [REFRESH.md](REFRESH.md) para a comparação e os hashes das novas capturas.\n\n')
marker = '## Consultar o histórico'
assert marker in readme
readme = readme.replace(marker, paragraph + marker)
(REPO / 'README.md').write_text(readme)
gap_doc = (REPO / 'GAPS.md').read_text()
gap_doc += ('\nRechecagem do link atualizado em 19/10/2026 às 14:57 e 14:58 UTC: HTTP 200 nas duas requisições, incluindo `no-cache`. A atualização de metadados às 14:55:52 UTC foi confirmada, mas os 615 nós e 89 mensagens de código retornados são idênticos à captura anterior; v1.6.0 continua ausente. Não surgiram novos conteúdos de v1.4.0/v1.5.0, testes, READMEs ou HTML. Essa limitação da resposta pública, documentada em `REFRESH.md`, permanece como bloqueio para a recuperação de novos bytes. Não foi presumido desbloqueio do Mac.\n')
(REPO / 'GAPS.md').write_text(gap_doc)
revision_doc = (REPO / 'REVISIONS.md').read_text()
revision_doc += ('\n## Capturas atualizadas sem nova revisão de artefato\n\n'
                 'As consultas HTTP de 19/10/2026 às 14:57 e 14:58 UTC confirmaram a atualização de `update_time` do compartilhamento, mas não acrescentaram mensagens, código ou referências de anexos. O mapa de 615 nós e as 89 mensagens de código são idênticos à captura inicial. O commit da rechecagem preserva as duas respostas e sua comparação; os 42 registros de revisão de artefatos permanecem inalterados. Veja [REFRESH.md](REFRESH.md).\n')
(REPO / 'REVISIONS.md').write_text(revision_doc)
attachment_doc = (REPO / 'ATTACHMENTS.md').read_text()
attachment_doc += ('\nRechecagem de 19/10/2026 às 14:57/14:58 UTC: o link atualizado ainda contém as mesmas 16 referências literais das sete primeiras mensagens. A mensagem v1.6.0 e suas três referências continuam ausentes da resposta pública e fundamentadas no relato do pai. Nenhuma nova referência ou identidade binária foi confirmada.\n')
(REPO / 'ATTACHMENTS.md').write_text(attachment_doc)
progress = (REPO / '.provenance/PROGRESS.md').read_text()
progress += (f'\n- {NOW}: retomada a pedido do usuário com o mesmo link atualizado; estado inicial limpo e 25 commits verificados.\n'
             '- Novos downloads em 14:57:17 e 14:58:00 UTC, ambos HTTP 200; segundo com cabeçalhos no-cache e resposta DYNAMIC.\n'
             '- Metadados confirmam atualização do link em 14:55:52 UTC; apenas update_time e ordenação de safe_urls mudaram. Os mesmos 615 nós, 89 mensagens de código e 16 pares literais de mensagem+anexo permanecem inalterados.\n'
             '- Zero novas revisões recuperadas. Capturas preservadas em diretório próprio; inventário e lacunas atualizados sem criar conteúdo faltante. Nenhuma tentativa de navegador ou suposição de desbloqueio do Mac.\n')
(REPO / '.provenance/PROGRESS.md').write_text(progress)
(ROOT / 'PROGRESS.md').write_text(progress)

hashes = {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted(REPO.rglob('*')) if p.is_file() and '.git' not in p.relative_to(REPO).parts
          and p != REPO / '.provenance/final-files.sha256.json'}
jwrite('.provenance/final-files.sha256.json', hashes)
git('add', '--all')
git('commit', '--no-verify', '-m', 'docs: archive refreshed share responses and verify unchanged message content',
    '-m', 'The shared URL reports an updated timestamp, but normal and no-cache HTTP 200 responses preserve exactly 615 nodes and 89 code messages. No new artifact revisions were exposed. Preserve all 25 previous commits and the original capture.')
current = git('rev-list', '--reverse', 'HEAD').decode().splitlines()
assert len(current) == 26 and current[:25] == prior
assert git('rev-parse', 'HEAD^').decode().strip() == OLD_HEAD
count = 0
for event in json.loads((REPO / '.provenance/revisions.json').read_text()):
    for write in event['writes']:
        data = git('show', event['commit'] + ':' + write['repo_path'])
        assert hashlib.sha256(data).hexdigest() == write['sha256']
        count += 1
for name, sha in hashes.items():
    assert hashlib.sha256((REPO / name).read_bytes()).hexdigest() == sha
assert hashlib.sha256(original_raw.read_bytes()).hexdigest() == REPORT['original_capture_sha256']
assert not git('status', '--porcelain')
assert not git('remote')
git('fsck', '--full', '--strict')
dates = [int(d) for d in git('log', '--reverse', '--format=%at').splitlines()]
assert dates == sorted(dates)
summary = {'repository': str(REPO), 'head': git('rev-parse', 'HEAD').decode().strip(),
           'parent_head_preserved': OLD_HEAD, 'prior_commits_preserved': 25, 'commits': 26,
           'artifact_paths': 27, 'revision_records': count, 'new_artifact_revisions_recovered': 0,
           'refresh_comparison': comparison_path, 'metadata_update_confirmed_utc': REPORT['requests'][0]['share_metadata_update_time_utc'],
           'public_message_nodes': 615, 'public_code_messages': 89, 'message_content_unchanged': True,
           'unique_audited_message_attachment_references': 19, 'public_literal_message_attachment_references': 16,
           'later_v1_6_message_present': False, 'original_capture_preserved': True,
           'final_files_checked': len(hashes), 'tracked_files': len(git('ls-files').splitlines()),
           'status_porcelain': '', 'remotes': '', 'fsck': 'passed --full --strict',
           'source_author_dates': 'chronological', 'browser_attempted': False, 'mac_unlock_assumed': False,
           'completed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
           'log': git('log', '--reverse', '--format=%h %aI %s').decode()}
(ROOT / 'verification-final.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in summary.items() if k != 'log'}, ensure_ascii=False, indent=2))
print(git('status', '--short', '--branch').decode())
print(git('log', '-3', '--format=%h %aI %s').decode())
