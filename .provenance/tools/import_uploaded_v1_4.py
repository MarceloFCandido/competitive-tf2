"""Archive the three hash-verified original uploads without executing source code."""
from pathlib import Path
import ast
import collections
import datetime as dt
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = Path('/Users/marcelofcandido/git/personal/games/competitive-tf2')
OLD_HEAD = 'ce6b59cce5980e40e535288a35a01637acec712f'
PENDING = json.loads((ROOT / 'pending-user-upload-turn-1.json').read_text())
INPUT = Path(PENDING['destination'])
TRANSFER = json.loads((INPUT / 'transfer-verified.json').read_text())
INSPECTION = json.loads((ROOT / 'upload-turn-1-inspection.json').read_text())
ORIGIN_ID = '5ee4f90d-4bdd-4de7-9845-74f77fe5e13a'
ORIGIN_URL = PENDING['expected_origin_message_url']
UPLOAD_ID = PENDING['user_upload_message_id']
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
    path = REPO / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


assert git('rev-parse', 'HEAD').decode().strip() == OLD_HEAD
assert not git('status', '--porcelain'), 'User changes detected; refusing to overwrite.'
prior = git('rev-list', '--reverse', 'HEAD').decode().splitlines()
assert len(prior) == 28
assert TRANSFER['parts'] == 10 and len(TRANSFER['files']) == 3
assert next(r for r in INSPECTION if r['canonical_name'] == 'setup_tf2_bazzite.py')['declared_SCRIPT_VERSION'] == ['1.4.0']
assert 'v1.4.0' in next(r for r in INSPECTION if r['canonical_name'].endswith('.md'))['heading']
snapshot = json.loads((REPO / '.provenance/source/conversation.json').read_text())
source_message = snapshot['mapping'][ORIGIN_ID]['message']
source_time = source_message['create_time']
source_time_iso = dt.datetime.fromtimestamp(source_time, dt.timezone.utc).isoformat()
event = {'sequence': 'user-upload-turn-1', 'message_id': ORIGIN_ID,
         'source_timestamp': source_time, 'source_message_url': ORIGIN_URL,
         'upload_message_id': UPLOAD_ID, 'upload_label': '1o turno',
         'received_and_verified_at_utc': TRANSFER['verified_at_utc'],
         'notes': ['Original bytes supplied by the user; version association is supported by the user label/origin and literal v1.4.0 declarations.',
                   'No identity with other historical links or other version groups is assumed.'], 'writes': []}
for row in TRANSFER['files']:
    path = Path(row['path']); data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == row['sha256']
    assert len(data) == row['bytes']
    info = next(i for i in INSPECTION if i['upload_name'] == row['upload_name'])
    destination = REPO / row['canonical_name']
    assert hashlib.sha256(destination.read_bytes()).hexdigest() == info['previous_sha256']
    write = {'original_path': '/mnt/data/' + row['canonical_name'], 'repo_path': row['canonical_name'],
             'upload_name': row['upload_name'], 'status': 'original_user_upload',
             'sha256': row['sha256'], 'bytes': row['bytes'], 'previous_repository_sha256': info['previous_sha256'],
             'source_upload_message_id': UPLOAD_ID, 'source_message_id': ORIGIN_ID,
             'library_identity_scope': 'The three Library IDs are recorded as a group; an individual ID-to-filename mapping was not supplied.'}
    if row['canonical_name'].endswith('.py'):
        ast.parse(data.decode('utf-8'))
        write['static_syntax'] = 'parsed_without_execution'
    event['writes'].append(write)
    destination.write_bytes(data)
    destination.chmod(0o644)

receipt_path = '.provenance/user-uploads/turn-1-v1.4.0/receipt.json'
receipt = {'receipt_type': 'original_files_uploaded_by_user', 'upload_message_id': UPLOAD_ID,
           'user_label': '1o turno', 'user_indicated_origin_message_id': ORIGIN_ID,
           'user_indicated_origin_url': ORIGIN_URL, 'origin_announcement_timestamp_utc': source_time_iso,
           'received_and_verified_at_utc': TRANSFER['verified_at_utc'], 'imported_at_utc': NOW,
           'library_file_ids_as_group': PENDING['library_file_ids'], 'individual_library_id_mapping_available': False,
           'version_check': {'installer_SCRIPT_VERSION': '1.4.0', 'test_docstring': 'v1.4.0', 'README_heading': 'v1.4.0'},
           'transport': {'kind': '10 verified ASCII base64 parts containing gzip JSON file-byte map',
                         'all_part_hashes_verified': True, 'all_final_file_hashes_verified': True,
                         'initial_single_message_attempt_truncated': True},
           'files': event['writes'], 'source_code_executions': 0, 'test_runs': 0,
           'historical_link_identity_scope': 'This upload group is associated with the v1.4.0 announcement by the user and matching declarations. No byte identity with other historical links is inferred.',
           'date_policy': 'Append-only late recovery. Commit author/committer dates record this import; the earlier source announcement date is retained here without rewriting prior commits.'}
jwrite(receipt_path, receipt)
jwrite('.provenance/user-uploads/turn-1-v1.4.0/transport-verification.json', {
    'summary': TRANSFER, 'part_manifest': json.loads((INPUT / 'transfer-parts/manifest.json').read_text()),
    'raw_base64_or_binary_packet_archived': False})
jwrite('.provenance/user-uploads/turn-1-v1.4.0/static-inspection.json', INSPECTION)
jwrite('.provenance/events/user-upload-turn-1.json', event)
git('add', '--all')
git('commit', '--no-verify', '-m', 'archive: import user-uploaded TF2 v1.4.0 installer tests and README',
    '-m', f'All ten transport part hashes and three final file hashes verified. Original bytes preserved under canonical filenames; upload filenames retained in provenance.\nSource-Message: {ORIGIN_ID}\nSource-URL: {ORIGIN_URL}\nUpload-Message: {UPLOAD_ID}\nUpload-Label: 1o turno\nDeclared-Version: 1.4.0\nRecovered-Code-Execution: none')
content_commit = git('rev-parse', 'HEAD').decode().strip()
event['commit'] = content_commit
events = json.loads((REPO / '.provenance/revisions.json').read_text()); events.append(event)
jwrite('.provenance/revisions.json', events)
all_writes = [write for item in events for write in item['writes']]
assert len(all_writes) == 45
paths = collections.Counter(w['repo_path'] for w in all_writes)
types = collections.Counter(w['status'] for w in all_writes)
assert len(paths) == 27 and types['original_user_upload'] == 3

capture = json.loads((REPO / '.provenance/capture.json').read_text())
capture.update(revision_records=45, artifact_paths=27, classification=dict(types))
capture['validation'].update(sha256_revision_checks=45, python_static_parses=33, recovered_code_executions=0)
capture['user_upload_groups'] = [{'group': '1o turno', 'declared_version': '1.4.0', 'files': 3,
                                  'upload_message_id': UPLOAD_ID, 'receipt': receipt_path,
                                  'content_commit': content_commit, 'all_hashes_verified': True}]
capture['late_recovery_dates'] = receipt['date_policy']
jwrite('.provenance/capture.json', capture)
gaps = json.loads((REPO / '.provenance/gaps.json').read_text())
for gap in gaps:
    if gap['id'] == 'version_1_4_0':
        gap.update(status='resolved_by_original_user_upload',
                   detail='Three original uploads received for the v1.4.0 group. Installer SCRIPT_VERSION, test docstring and README identify v1.4.0; all supplied file hashes match.',
                   resolution={'receipt': receipt_path, 'commit': content_commit, 'files': [w['repo_path'] for w in event['writes']]})
    elif gap['id'] == 'version_1_5_0':
        gap.update(status='original_v1_5_upload_not_yet_received',
                   detail='Original v1.4.0 baseline is now available through the user upload. The previous incomplete candidate is preserved as an earlier reconstruction and has not been replaced by original v1.5.0 bytes.',
                   v1_4_baseline_available=True)
    elif gap['id'] == 'sandbox_attachments':
        gap['user_upload_recovery'] = {'declared_version': '1.4.0', 'verified_file_count': 3, 'receipt': receipt_path}
    elif gap['id'] == 'attachment_binary_identity':
        gap['verified_original_user_uploads'] = 3
        gap['identity_note'] = 'Three user-uploaded v1.4.0 contents are verified. This does not establish binary identity across all 19 historical message+attachment references.'
jwrite('.provenance/gaps.json', gaps)
announcements = json.loads((REPO / '.provenance/announced-revisions.json').read_text())
for item in announcements:
    if item.get('source_message_id') == ORIGIN_ID:
        item.update(content_status='original_user_uploads_received_and_hash_verified', receipt=receipt_path,
                    content_commit=content_commit,
                    note='User-provided group labeled 1o turno, associated with this announcement; code/test docstring/README identify v1.4.0. No equivalence with other links or version groups is assumed.')
jwrite('.provenance/announced-revisions.json', announcements)
references = json.loads((REPO / '.provenance/references.json').read_text())
for ref in references:
    for write in event['writes']:
        if ref['original_path'] == write['original_path']:
            ref['revisions'].append({'sequence': event['sequence'], 'commit': content_commit,
                                     'repo_path': write['repo_path'], 'status': 'original_user_upload',
                                     'sha256': write['sha256'], 'upload_name': write['upload_name']})
jwrite('.provenance/references.json', references)
attachment_refs = json.loads((REPO / '.provenance/attachment-references.json').read_text())
for ref in attachment_refs['references']:
    if ref['message_id'] == ORIGIN_ID:
        write = next(w for w in event['writes'] if w['repo_path'] == ref['filename'])
        ref.update(user_uploaded_bytes_verified=True, uploaded_sha256=write['sha256'],
                   upload_name=write['upload_name'], user_upload_receipt=receipt_path, content_commit=content_commit,
                   binary_revision_identity='User-uploaded v1.4.0 bytes verified. Identity with other historical links is not inferred.')
attachment_refs['verified_user_upload_group_count'] = 1
attachment_refs['verified_user_uploaded_file_count'] = 3
jwrite('.provenance/attachment-references.json', attachment_refs)
code_states = json.loads((REPO / '.provenance/code-version-states.json').read_text())
code_states.append({'version': '1.4.0', 'classification': 'original_user_upload', 'receipt': receipt_path,
                    'content_commit': content_commit, 'installer_sha256': event['writes'][0]['sha256'],
                    'literal_SCRIPT_VERSION': '1.4.0', 'source_announcement_message_id': ORIGIN_ID,
                    'note': 'Literal code-state 1.3.1 remains preserved; these original bytes also contain substantive Middle Mann changes.'})
jwrite('.provenance/code-version-states.json', code_states)

rows = ['| Nome recebido no upload | Nome canônico no Git | Bytes | SHA-256 |', '|---|---|---:|---|']
rows += [f"| `{w['upload_name']}` | `{w['repo_path']}` | {w['bytes']} | `{w['sha256']}` |" for w in event['writes']]
(REPO / 'UPLOADS.md').write_text(f'''# Originais recebidos — grupo “1o turno”

Foram recebidos **três arquivos originais fornecidos pelo usuário**, relacionados por ele ao [anúncio v1.4.0]({ORIGIN_URL}). Os nomes do upload foram mantidos neste registro e no manifesto; o Git usa os nomes canônicos.

{chr(10).join(rows)}

As dez partes de transporte e os três hashes finais conferem. O instalador declara `SCRIPT_VERSION = '1.4.0'`; o docstring da suíte e o título do README também indicam v1.4.0. Foram contados **56 métodos de teste por análise estática**. Os arquivos foram preservados byte a byte; nenhum script foi importado/executado e os testes não foram rodados.

O upload corresponde à mensagem de envio `{UPLOAD_ID}`, rotulada **“1o turno”**. A associação com o anúncio original é fornecida pelo usuário e corroborada pelas declarações de versão; isso não prova que outros links antigos apontem para bytes distintos ou iguais. Os três IDs Library são preservados como grupo, pois não foi fornecido o vínculo individual entre cada ID e nome de arquivo. Os sufixos `(1)` e `(5)` dos nomes de upload não foram tratados como números de revisão.

Em comparação com o estado reconstruído 1.3.1, o instalador recebido contém mudanças nas verificações dos arquivos `cfg` do Middle Mann, um helper para imprimir suas notas e outros ajustes. A suíte recebida e o README também diferem dos estados anteriores. O README literal v1.5.0 já arquivado continua disponível em seu commit histórico; os três arquivos canônicos da raiz agora formam o grupo original v1.4.0 recebido.

Commit dos bytes: `{content_commit}`. Prova de recebimento, transporte e inspeção: `.provenance/user-uploads/turn-1-v1.4.0/`. Datas Git desta recuperação tardia indicam a importação; a data histórica do anúncio ({source_time_iso}) permanece no manifesto. Nenhum dos 28 commits anteriores foi reescrito.

Uma busca independente, limitada aos três padrões de nome em `~/Downloads` e nas subpastas `v1.4.0`, `v1.5.0` e `v1.6.0`, não encontrou cópias alternativas. A fonte destes bytes é o upload transferido pelo pai. Os demais grupos de arquivos originais ainda não foram recebidos.
''')
(REPO / 'README.md').write_text(f'''# TF2 Competitive Setup Linux — arquivo da conversa

Repositório Git local de preservação da [conversa compartilhada](https://chatgpt.com/share/6ad6143e-d894-83e9-a306-302b4fc65c66), em `/Users/marcelofcandido/git/personal/games/competitive-tf2`, no `NEBULOSA-2.local`.

**Os três arquivos canônicos da raiz agora são os originais v1.4.0 fornecidos pelo usuário:** `setup_tf2_bazzite.py`, `test_setup_tf2_bazzite.py` e `TF2_HUD_Update_README.md`. Todos os hashes da transferência conferem; instalador, docstring dos testes e README identificam v1.4.0. Veja [UPLOADS.md](UPLOADS.md).

Há **30 commits**: **23 de conteúdo** (22 etapas da captura inicial e este grupo original) e **7 de documentação/evidências**. Os **27 caminhos de artefatos** têm **45 registros de revisão**: 18 conteúdos literais da captura, 22 reconstruções estáticas, 2 candidatos incompletos e **3 originais recebidos por upload**. Registros e links repetidos não significam versões binárias distintas. Os 28 commits anteriores foram preservados.

O instalador possui nove estados arquivados, incluindo as reconstruções anteriores e o original v1.4.0. `1.3.1` permanece identificado como estado literal de código/README, sem anúncio visível de lançamento. A lacuna do grupo v1.4.0 foi resolvida por este upload. **Os outros grupos originais, especialmente v1.5.0, v1.6.0 e o corpo de `TF2_HUD_Visual_Comparison.html`, ainda não foram recebidos.** A galeria offline reparada não foi entregue no chat; deveria ser construída no PC. Veja [GAPS.md](GAPS.md).

A auditoria identifica 19 referências únicas de mensagem + anexo (8 instalador, 5 testes, 5 README, 1 HTML), sem confirmar 19 revisões binárias. [ATTACHMENTS.md](ATTACHMENTS.md) distingue esses anúncios dos conteúdos recuperados. O candidato v1.5.0 anterior permanece separado, com sua limitação histórica registrada; não foi apresentado como anexo original.

**Nenhum instalador, script de alteração, teste ou CFG recuperado foi executado.** A validação usa hashes, comparação de bytes e análise sintática estática. A suíte v1.4.0 possui 56 métodos contados estaticamente; isso não é um resultado de execução.

## Consultar o histórico

```bash
git status --short
git log --reverse --format='%h %aI %s'
git log --follow -- setup_tf2_bazzite.py
git show {content_commit}:setup_tf2_bazzite.py
```

[REVISIONS.md](REVISIONS.md) e `.provenance/revisions.json` registram commits, mensagens de origem, classificação e SHA-256. `.provenance/user-uploads/turn-1-v1.4.0/` preserva nomes recebidos, IDs Library do grupo, mensagem de envio, partes de transporte verificadas e versão declarada. Os nomes canônicos mantêm os nomes originais do chat; os sufixos dos uploads são metadados de recebimento.

As capturas públicas, incluindo duas rechecagens que retornaram os mesmos 615 nós e 89 mensagens de código, estão preservadas como dados. [REFRESH.md](REFRESH.md) explica seus limites. [BROWSER_ACCESS.md](BROWSER_ACCESS.md) registra o desbloqueio confirmado do Mac, a autenticação pendente no Safari e a recusa da ferramenta em controlar o app ChatGPT; essas tentativas não são a fonte dos arquivos recebidos.

O README `TF2_HUD_UPDATE_README.md` está em `case-variants/` para preservar a diferença de maiúsculas no macOS. O CFG opcional de Medic está em `alternatives/medic/`. Templates que dependem do estado de uma instalação TF2 não foram executados para produzir arquivos presumidos.

Nos commits iniciais de conteúdo, `AuthorDate` registra a data da mensagem da captura. Recuperações tardias por upload e commits de documentação usam a data de importação, preservando a data histórica da origem nos manifestos e sem reescrever o histórico existente. Não há remoto configurado e nada foi publicado. Este repositório é um arquivo histórico, não uma instalação ou configuração aplicada de TF2.
''')
gap_doc = (REPO / 'GAPS.md').read_text()
gap_doc = gap_doc.replace('- **v1.4.0:** anunciada na resposta 468, mas a última edição de código disponível define `1.3.1`. Não há bytes completos de v1.4.0 nem a alteração intermediária correspondente.',
    f'- **v1.4.0 — resolvida por upload:** recebidos os originais do instalador, testes e README do grupo “1o turno”. Os três hashes conferem e os arquivos identificam v1.4.0. Estão no commit `{content_commit}` e em `UPLOADS.md`. A associação ao anúncio é informada pelo usuário; nenhuma identidade com outros links históricos é presumida.')
gap_doc = gap_doc.replace('- **v1.5.0:** a alteração 544 depende dessa base v1.4.0. Foi preservado um candidato em `reconstructions/incomplete-v1.5.0/`, obtido aplicando somente os trechos disponíveis à última base recuperável. A substituição de versão não encontra correspondência; o código conserva `1.3.1`. O candidato e seus testes não representam anexos originais verificados.',
    '- **v1.5.0:** os originais desse grupo ainda não foram recebidos. A base original v1.4.0 agora está disponível. O candidato anterior em `reconstructions/incomplete-v1.5.0/` foi produzido antes desse recebimento sobre a reconstrução 1.3.1; permanece preservado como estado histórico e não foi convertido em anexo original.')
gap_doc += ('\nRecuperação por upload do grupo “1o turno”: três originais v1.4.0 recebidos e verificados, resolvendo a ausência dos bytes desse grupo. As limitações do navegador e da captura pública não impediram essa via de transferência. Os demais grupos originais continuam pendentes.\n')
(REPO / 'GAPS.md').write_text(gap_doc)
(REPO / 'reconstructions/incomplete-v1.5.0/README.md').write_text('''# Candidato histórico incompleto, não um anexo original

Estes arquivos foram produzidos a partir das alterações de texto das mensagens 544 e 548 aplicadas à reconstrução v1.3.1 e seus testes. À época, a base v1.4.0 esperada não estava disponível; a troca `1.4.0 → 1.5.0` não correspondia ao texto e nenhum número foi inventado.

Os originais v1.4.0 foram recebidos posteriormente por upload e estão na raiz e no histórico, conforme `../../UPLOADS.md`. Este candidato antigo foi preservado sem alteração dos bytes de código; não foi reconstruído novamente nem promovido a original v1.5.0. Os originais v1.5.0 ainda não foram recebidos. Nenhum destes scripts ou testes foi executado.
''')
revisions_doc = (REPO / 'REVISIONS.md').read_text()
revisions_doc = revisions_doc.replace('| `setup_tf2_bazzite.py` | 8 |', '| `setup_tf2_bazzite.py` | 9 |')
revisions_doc = revisions_doc.replace('| `test_setup_tf2_bazzite.py` | 4 |', '| `test_setup_tf2_bazzite.py` | 5 |')
revisions_doc = revisions_doc.replace('| `TF2_HUD_Update_README.md` | 3 |', '| `TF2_HUD_Update_README.md` | 4 |')
revisions_doc += (f'\n## Originais v1.4.0 recebidos por upload\n\n'
                  f'Commit `{content_commit}`: os três arquivos do grupo “1o turno”, mensagem de envio `{UPLOAD_ID}`, foram preservados byte a byte sob nomes canônicos. A origem indicada é [o anúncio v1.4.0]({ORIGIN_URL}), de {source_time_iso}. Os nomes de upload, Library IDs do grupo e hashes estão em [UPLOADS.md](UPLOADS.md). As datas deste novo commit registram a recuperação tardia; os 28 commits anteriores não foram reescritos.\n\n'
                  'O manifesto agora possui 45 registros em 27 caminhos: os 42 anteriores e três originais recebidos. A suíte v1.4.0 tem 56 métodos de teste contados por AST, sem execução. Os estados 1.3.1 e o README literal v1.5.0 permanecem disponíveis nos commits anteriores.\n')
(REPO / 'REVISIONS.md').write_text(revisions_doc)
attachment_doc = (REPO / 'ATTACHMENTS.md').read_text()
attachment_doc += (f'\n## Bytes recebidos para o grupo v1.4.0\n\n'
                   f'O usuário forneceu os três arquivos do grupo associado à mensagem `{ORIGIN_ID}` como “1o turno”. Os hashes conferem e instalador, testes e README identificam v1.4.0. Foram importados em `{content_commit}`; nomes de upload e hashes constam em [UPLOADS.md](UPLOADS.md). A associação é fornecida pelo usuário e compatível com o conteúdo; não se deduz identidade binária para os demais links. O total permanece 19 referências de mensagem + anexo, agora com três conteúdos originais fornecidos por upload verificados.\n')
(REPO / 'ATTACHMENTS.md').write_text(attachment_doc)
progress = (REPO / '.provenance/PROGRESS.md').read_text()
progress += (f'\n- {NOW}: dez partes recebidas e verificadas individualmente; base64/gzip/JSON decodificados somente como dados. Os três SHA-256 finais conferem.\n'
             '- Originais recebidos: instalador 53.740 bytes, testes 27.981 bytes e README 5.823 bytes. Instalador, docstring dos testes e README identificam v1.4.0; 56 métodos de teste contados estaticamente. Nenhum código recuperado executado.\n'
             f'- Bytes importados no commit {content_commit}; nomes de upload e origem preservados. Busca restrita em Downloads sem cópias alternativas. Outros grupos originais ainda não recebidos.\n')
(REPO / '.provenance/PROGRESS.md').write_text(progress)
(ROOT / 'PROGRESS.md').write_text(progress)
(REPO / '.provenance/tools/import_uploaded_v1_4.py').write_bytes(Path(__file__).read_bytes())
hashes = {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted(REPO.rglob('*')) if p.is_file() and '.git' not in p.relative_to(REPO).parts
          and p != REPO / '.provenance/final-files.sha256.json'}
jwrite('.provenance/final-files.sha256.json', hashes)
git('add', '--all')
git('commit', '--no-verify', '-m', 'docs: reconcile verified v1.4.0 originals with provenance and remaining gaps')
history = git('rev-list', '--reverse', 'HEAD').decode().splitlines()
assert len(history) == 30 and history[:28] == prior and history[28] == content_commit
checked = 0
for item in events:
    for write in item['writes']:
        assert hashlib.sha256(git('show', item['commit'] + ':' + write['repo_path'])).hexdigest() == write['sha256']
        checked += 1
assert checked == 45
for name, sha in hashes.items():
    assert hashlib.sha256((REPO / name).read_bytes()).hexdigest() == sha
assert not git('status', '--porcelain')
assert not git('remote')
git('fsck', '--full', '--strict')
dates = [int(d) for d in git('log', '--reverse', '--format=%at').splitlines()]
assert dates == sorted(dates)
summary = {'repository': str(REPO), 'head': git('rev-parse', 'HEAD').decode().strip(),
           'content_import_commit': content_commit, 'parent_head_preserved': OLD_HEAD,
           'prior_commits_preserved': 28, 'commits': 30, 'artifact_paths': 27, 'revision_records': checked,
           'new_original_files_recovered': 3, 'verified_upload_version': '1.4.0',
           'transport_parts_verified': 10, 'all_three_final_hashes_match': True,
           'static_test_method_count': 56, 'source_code_executions': 0, 'test_runs': 0,
           'classification': dict(types), 'uploaded_files': event['writes'],
           'final_files_checked': len(hashes), 'tracked_files': len(git('ls-files').splitlines()),
           'status_porcelain': '', 'remotes': '', 'fsck': 'passed --full --strict',
           'commit_dates': 'chronological acquisition order; original announcement date retained in provenance',
           'remaining_original_upload_groups': ['v1.5.0', 'v1.6.0', 'TF2_HUD_Visual_Comparison.html and any other unavailable original attachment'],
           'completed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
           'log': git('log', '--reverse', '--format=%h %aI %s').decode()}
(ROOT / 'verification-final.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
PENDING.update(status='imported_and_verified', content_commit=content_commit, final_head=summary['head'],
               repository=str(REPO), source_code_executions=0)
(ROOT / 'pending-user-upload-turn-1.json').write_text(json.dumps(PENDING, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in summary.items() if k not in ('log', 'uploaded_files')}, ensure_ascii=False, indent=2))
print(git('status', '--short', '--branch').decode())
print(git('log', '-3', '--format=%h %aI %s').decode())
