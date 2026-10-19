"""Add the parent's complete visible-message attachment audit without fabricating bytes."""
from pathlib import Path
import collections
import datetime as dt
import hashlib
import json
import os
import re
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = Path('/Users/marcelofcandido/git/personal/games/competitive-tf2')
OLD_HEAD = 'ae67b8bd260729ba93a7a4ac8e965a91219c7c8b'
CONVERSATION = '6acfa42a-f8fc-83e8-b025-370fd5942d5b'
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
assert len(prior_commits) == 24
source = json.loads((REPO / '.provenance/source/conversation.json').read_text())
snapshot = {}
for seq, node in enumerate(source['linear_conversation'], 1):
    message = node.get('message')
    if message:
        snapshot[message['id']] = (seq, message)

installer = 'setup_tf2_bazzite.py'
tests = 'test_setup_tf2_bazzite.py'
upper = 'TF2_HUD_UPDATE_README.md'
mixed = 'TF2_HUD_Update_README.md'
gallery = 'TF2_HUD_Visual_Comparison.html'
specs = [
    ('2c2ebc16-741c-48e5-84fb-c2023c643341', '2026-10-18 00:37 UTC', None, 'initial_link_without_version', [installer]),
    ('3d1026f5-29a5-4318-8091-2f5a8b143c83', '2026-10-18 00:46 UTC', None, 'relink_without_new_version', [installer]),
    ('b59710b3-be3f-4531-bef4-76ec764c8ec3', '2026-10-19 02:43 UTC', '1.2.0', 'version_announcement', [installer]),
    ('49a6cc70-733a-44f2-be7d-384c1382ae26', '2026-10-19 03:34 UTC', '1.3.0', 'version_announcement', [installer, upper, tests]),
    ('62fc5fff-4c15-45a9-b7cd-a332d4e886ac', '2026-10-19 03:45 UTC', '1.3.0', 'version_announcement', [installer, mixed, tests]),
    ('5ee4f90d-4bdd-4de7-9845-74f77fe5e13a', '2026-10-19 12:00 UTC', '1.4.0', 'version_announcement', [installer, mixed, tests]),
    ('454439cb-235e-4787-96c0-19a40f8c2b1d', '2026-10-19 12:30 UTC', '1.5.0', 'version_announcement', [installer, mixed, tests, gallery]),
    ('e4b8944c-7916-4302-8016-463828ec503e', '2026-10-19 13:12 UTC', '1.6.0', 'version_announcement', [installer, mixed, tests]),
]
events = json.loads((REPO / '.provenance/revisions.json').read_text())
groups = []
references = []
for message_id, parent_time, version, kind, filenames in specs:
    entry = {'message_id': message_id,
             'message_url': f'https://chatgpt.com/c/{CONVERSATION}?messageId={message_id}',
             'parent_reported_time_utc_minute_precision': parent_time,
             'announced_version': version, 'kind': kind, 'filenames': filenames}
    if message_id in snapshot:
        seq, message = snapshot[message_id]
        text = '\n'.join(p for p in message.get('content', {}).get('parts', []) if isinstance(p, str))
        links = re.findall(r'\[[^\]]*\]\((sandbox:[^)]*)\)', text)
        unique = sorted(set(link.removeprefix('sandbox:/mnt/data/') for link in links))
        assert unique == sorted(filenames), (message_id, unique, filenames)
        if version:
            assert 'v' + version in text
        entry.update(shared_snapshot_sequence=seq,
                     exact_source_timestamp_utc=dt.datetime.fromtimestamp(message['create_time'], dt.timezone.utc).isoformat(),
                     evidence='parent direct-read audit, independently matched to literal shared-snapshot links',
                     original_message_text_available=True)
    else:
        assert message_id == 'e4b8944c-7916-4302-8016-463828ec503e'
        entry.update(shared_snapshot_sequence=None, exact_source_timestamp_utc='2026-10-19T13:12:17Z',
                     evidence='parent direct-read audit; absent from earlier public snapshot',
                     original_message_text_available=False)
    groups.append(entry)
    for filename in filenames:
        category = 'installer' if filename == installer else ('tests' if filename == tests else ('html' if filename == gallery else 'readme'))
        ref = {'message_id': message_id, 'message_url': entry['message_url'], 'filename': filename,
               'category': category, 'announced_version': version, 'kind': kind,
               'evidence': entry['evidence'], 'source_timestamp_utc': entry['exact_source_timestamp_utc'],
               'original_attachment_bytes_verified': False,
               'binary_revision_identity': 'unknown; a repeated path or link is not proof of identical or distinct bytes'}
        if message_id in snapshot:
            ref['literal_sandbox_reference'] = 'sandbox:/mnt/data/' + filename
        else:
            ref['literal_sandbox_reference'] = None
            ref['reference_note'] = 'Filename reported by parent; exact original link text not supplied to executor.'
        ref['related_recovered_paths'] = sorted({write['repo_path'] for event in events for write in event['writes']
                                                 if write['original_path'] == '/mnt/data/' + filename})
        ref['relationship_note'] = 'Related recovered source material is inventoried separately; no exact announcement-to-attachment binary match is asserted.'
        references.append(ref)
assert len({(r['message_id'], r['filename']) for r in references}) == len(references) == 19
counts = dict(collections.Counter(r['category'] for r in references))
assert counts == {'installer': 8, 'readme': 5, 'tests': 5, 'html': 1}

parent_evidence_path = '.provenance/supplemental-evidence/complete-attachment-audit-parent-report.json'
parent_report = {
    'evidence_type': 'parent_report_of_complete_direct_conversation_text_read',
    'received_at_utc': NOW, 'conversation_id': CONVERSATION,
    'reported_message_count': 26, 'reported_pages_exhausted': 3, 'reported_content_omitted': False,
    'attachment_bytes_provided': False, 'unique_message_attachment_pairs': 19,
    'counts': counts, 'not_a_binary_revision_count': True,
    'independent_snapshot_crosscheck': {'matched_message_groups': 7, 'message_groups_absent_from_snapshot': 1,
                                      'unique_pairs_matched_to_literal_links': 16, 'later_pairs_reported_only': 3},
    'parent_message_verbatim': 'Auditoria completa da leitura direta:26 mensagens, três páginas esgotadas, sem content_omitted. Há19 referências únicas mensagem+anexo (não19 revisões binárias confirmadas):8 instalador,5 testes,5 README,1HTML. Sequência:18Oct00:37 sem versão msg2c2ebc16-741c-48e5-84fb-c2023c643341;18Oct00:46 relink sem nova versão msg3d1026f5-29a5-4318-8091-2f5a8b143c83;19Oct02:43 v1.2 msgb59710b3-be3f-4531-bef4-76ec764c8ec3;03:34 v1.3 msg49a6cc70-733a-44f2-be7d-384c1382ae26 com TF2_HUD_UPDATE_README.md e testes;03:45 outra v1.3 msg62fc5fff-4c15-45a9-b7cd-a332d4e886ac com TF2_HUD_Update_README.md e testes;12:00 v1.4 msg5ee4f90d-4bdd-4de7-9845-74f77fe5e13a mesmos três;12:30 v1.5 msg454439cb-235e-4787-96c0-19a40f8c2b1d mais TF2_HUD_Visual_Comparison.html;13:12 v1.6 msge4b8944c-7916-4302-8016-463828ec503e mesmos três. URLs: https://chatgpt.com/c/6acfa42a-f8fc-83e8-b025-370fd5942d5b?messageId=ID . Não há rótulo1.3.1 nas mensagens visíveis, mas se ele consta literalmente no código recuperado, registre sua proveniência como estado de código e diferencie dos anúncios. Não descarte estados verificados do compartilhamento. Não foi fornecida galeria offline reparada. Confira inventário versus essa sequência e finalize correções. Estou aguardando usuário desbloquear Mac para tentar originais.'
}
jwrite(parent_evidence_path, parent_report)
jwrite('.provenance/attachment-references.json', {
    'counting_unit': 'unique message_id + attachment filename, not verified binary revisions',
    'unique_reference_count': 19, 'counts': counts, 'message_groups': groups, 'references': references,
    'audit_evidence': parent_evidence_path})

# Preserve and explicitly classify the literal 1.3.1 source state.
code_seq, code_msg = snapshot['5bd64030-9aa7-4890-8d69-d72572b6defb']
doc_seq, doc_msg = snapshot['2605ea9c-a8e4-4313-ab69-9b2de2883044']
assert code_seq == 451 and doc_seq == 458
code_text = code_msg['content']['text']; doc_text = doc_msg['content']['text']
literal_change = 's = s.replace("SCRIPT_VERSION = \'1.3.0\'", "SCRIPT_VERSION = \'1.3.1\'")'
assert literal_change in code_text
assert '# Centered TF2-style HUD option — installer v1.3.1' in doc_text
assert not any('1.3.1' in '\n'.join(p for p in (m.get('content') or {}).get('parts', []) if isinstance(p, str))
               for _, m in snapshot.values() if m.get('content', {}).get('content_type') == 'text')
state_event = next(event for event in events if event['sequence'] == 451)
state_write = next(write for write in state_event['writes'] if write['repo_path'] == installer)
jwrite('.provenance/code-version-states.json', [{
    'version': '1.3.1', 'classification': 'literal_code_state_not_a_visible_release_announcement',
    'literal_source_edit': literal_change,
    'source_code_message_id': code_msg['id'], 'source_code_sequence': 451,
    'source_code_message_url': f'https://chatgpt.com/c/{CONVERSATION}?messageId={code_msg["id"]}',
    'literal_readme_message_id': doc_msg['id'], 'literal_readme_sequence': 458,
    'literal_readme_heading': '# Centered TF2-style HUD option — installer v1.3.1',
    'reconstructed_installer_commit': state_event['commit'], 'reconstructed_installer_sha256': state_write['sha256'],
    'visible_release_announcement_present': False,
    'note': 'Retained from the shared snapshot as a recoverable code state. The later visible message announces v1.4.0; the intervening edit is not available. Neither evidence is discarded or treated as equivalent.'
}])

announcements = []
for group in groups:
    if group['announced_version'] is None:
        continue
    announcements.append({
        'version': group['announced_version'], 'source_message_id': group['message_id'],
        'source_message_url': group['message_url'], 'source_timestamp_utc': group['exact_source_timestamp_utc'],
        'artifact_filenames': group['filenames'], 'evidence': group['evidence'],
        'content_status': 'announcement_attachment_bytes_not_verified',
        'note': 'Recoverable literal bodies, reconstructed states and attachment announcements are separate inventories. Repeated version labels do not establish binary identity.'
    })
jwrite('.provenance/announced-revisions.json', announcements)

rows = ['| Horário UTC | Rótulo visível | Mensagem | Anexos distintos nessa mensagem |', '|---|---|---|---|']
for group in groups:
    label = group['announced_version'] or ('sem versão nova; relink' if group['kind'] == 'relink_without_new_version' else 'sem versão declarada')
    rows.append(f"| {group['parent_reported_time_utc_minute_precision']} | {label} | [{group['message_id']}]({group['message_url']}) | "
                + ', '.join('`' + name + '`' for name in group['filenames']) + ' |')
attachments_doc = (f'# Referências a anexos nas mensagens visíveis\n\n'
                   'A auditoria direta realizada no pai esgotou **3 páginas, 26 mensagens, sem `content_omitted`**. São **19 referências únicas de mensagem + nome de anexo**: **8 do instalador, 5 dos testes, 5 de README e 1 de HTML**. **Isso não confirma 19 revisões binárias distintas.** A repetição de um link também não comprova que seus bytes permaneceram iguais.\n\n'
                   'As sete primeiras mensagens e suas 16 referências únicas foram conferidas diretamente contra os textos da captura pública. A mensagem posterior v1.6.0 e suas três referências são evidência relatada pelo pai; o texto integral e os bytes não foram recebidos por este executor. A galeria HTML aparece duas vezes na mensagem v1.5.0, mas conta como um único par mensagem + anexo.\n\n'
                   + '\n'.join(rows) + '\n\n'
                   'O README de 03:34 usa `TF2_HUD_UPDATE_README.md`; a partir de 03:45, os anúncios usam `TF2_HUD_Update_README.md`. A diferença de maiúsculas foi preservada.\n\n'
                   '## Estado literal de código 1.3.1\n\n'
                   '`1.3.1` não é um rótulo de lançamento nas mensagens visíveis auditadas. É um estado literal do código recuperado: a mensagem de código 451 (`5bd64030-9aa7-4890-8d69-d72572b6defb`) contém `SCRIPT_VERSION` alterado de `1.3.0` para `1.3.1`; o README literal da mensagem 458 (`2605ea9c-a8e4-4313-ab69-9b2de2883044`) também identifica o instalador como v1.3.1. A reconstrução é preservada no histórico, com receita e hash próprios. O anúncio visível posterior usa v1.4.0; a divergência não foi corrigida por suposição.\n\n'
                   'A mensagem v1.6.0 confirma que os binários dos screenshots não foram baixados e que a galeria offline deveria ser construída no PC. Uma galeria já reparada não foi entregue como anexo.\n\n'
                   'Dados estruturados: `.provenance/attachment-references.json`, `.provenance/announced-revisions.json` e `.provenance/code-version-states.json`. O relato da auditoria está preservado em `.provenance/supplemental-evidence/complete-attachment-audit-parent-report.json`.\n')
(REPO / 'ATTACHMENTS.md').write_text(attachments_doc)

readme = (REPO / 'README.md').read_text()
readme = readme.replace('**2 commits de documentação/evidências** (**24 commits no total**)',
                        '**3 commits de documentação/evidências** (**25 commits no total**)')
anchor = 'Conteúdos literais vieram de heredocs/blocos fornecidos no chat;'
addition = ('A auditoria das mensagens visíveis registra **19 referências únicas de mensagem + anexo** (8 instalador, 5 testes, 5 README, 1 HTML), sem confirmar 19 revisões binárias. A sequência completa está em [ATTACHMENTS.md](ATTACHMENTS.md). **`1.3.1` é um estado literal de código e README recuperados, não um lançamento anunciado nas mensagens visíveis.** Ele permanece preservado com sua proveniência; os anúncios v1.3.0 e v1.4.0 são registrados separadamente.\n\n')
assert anchor in readme; readme = readme.replace(anchor, addition + anchor)
(REPO / 'README.md').write_text(readme)

gap_doc = (REPO / 'GAPS.md').read_text()
gap_doc += ('\nAuditoria final das mensagens visíveis: 26 mensagens em três páginas esgotadas, sem `content_omitted`, conforme relato do pai. As 19 referências únicas de mensagem + anexo estão em `ATTACHMENTS.md` e `.provenance/attachment-references.json`; elas não estabelecem 19 revisões binárias. Não há anúncio visível v1.3.1: esse rótulo é preservado como estado literal do código da mensagem 451 e do README da mensagem 458, separado dos anúncios de lançamento. Todos os estados anteriormente verificados foram mantidos.\n')
(REPO / 'GAPS.md').write_text(gap_doc)
revisions_doc = (REPO / 'REVISIONS.md').read_text()
revisions_doc += ('\n## Reconciliação com os links de anexos\n\n'
                  'A sequência completa de oito mensagens com links, incluindo o relink sem versão nova e os dois anúncios v1.3.0, está em [ATTACHMENTS.md](ATTACHMENTS.md). São 19 pares únicos mensagem + anexo, não 19 versões binárias confirmadas. `1.3.1` permanece como estado literal de código/README das mensagens 451 e 458; não foi promovido a anúncio de lançamento. Os 42 registros de revisão, 27 caminhos de artefatos e todos os commits anteriores foram preservados.\n')
(REPO / 'REVISIONS.md').write_text(revisions_doc)
gaps = json.loads((REPO / '.provenance/gaps.json').read_text())
for gap in gaps:
    if gap['id'] == 'version_1_4_0':
        gap['literal_code_state'] = '1.3.1 is directly present in recovered code and a literal README, not a visible release announcement.'
        gap['code_state_inventory'] = '.provenance/code-version-states.json'
gaps.append({'id': 'attachment_binary_identity', 'status': 'not_verified',
             'unique_message_attachment_references': 19, 'counts': counts,
             'detail': 'The complete direct-text audit reports no omitted text, but supplies no attachment bytes. 19 message+attachment references do not establish 19 distinct binary revisions.',
             'evidence': parent_evidence_path})
jwrite('.provenance/gaps.json', gaps)
capture = json.loads((REPO / '.provenance/capture.json').read_text())
capture['visible_message_audit'] = {
    'evidence': parent_evidence_path, 'reported_messages': 26, 'reported_pages_exhausted': 3,
    'reported_content_omitted': False, 'unique_message_attachment_references': 19,
    'counts': counts, 'verified_distinct_binary_revisions': None,
    'literal_code_version_1_3_1_distinct_from_visible_announcements': True}
jwrite('.provenance/capture.json', capture)
progress = (REPO / '.provenance/PROGRESS.md').read_text()
progress += (f'\n- {NOW}: auditoria completa do pai reconciliada: 26 mensagens, três páginas esgotadas, sem content_omitted; 19 pares únicos mensagem+anexo (8 instalador, 5 testes, 5 README, 1 HTML), sem confirmação de identidade binária.\n'
             '- Sete mensagens/16 pares conferidos contra a captura pública; v1.6.0/3 pares permanecem como relato suplementar.\n'
             '- Estado literal de código/README 1.3.1 diferenciado de anúncios visíveis. Nenhum estado recuperado removido; nenhuma galeria reparada alegada.\n')
(REPO / '.provenance/PROGRESS.md').write_text(progress)
(ROOT / 'PROGRESS.md').write_text(progress)
(REPO / '.provenance/tools/reconcile_attachment_audit.py').write_bytes(Path(__file__).read_bytes())
hashes = {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted(REPO.rglob('*')) if p.is_file() and '.git' not in p.relative_to(REPO).parts
          and p != REPO / '.provenance/final-files.sha256.json'}
jwrite('.provenance/final-files.sha256.json', hashes)
git('add', '--all')
git('commit', '--no-verify', '-m', 'docs: reconcile 19 attachment references and distinguish code state 1.3.1',
    '-m', 'Preserve all prior commits and recovered states. Match seven visible link messages to the public snapshot, retain the later v1.6.0 parent report, and avoid treating attachment references as verified binary revisions.')
new_commits = git('rev-list', '--reverse', 'HEAD').decode().splitlines()
assert new_commits[:len(prior_commits)] == prior_commits and len(new_commits) == 25
assert git('rev-parse', 'HEAD^').decode().strip() == OLD_HEAD
blob_checks = 0
for event in events:
    for write in event['writes']:
        data = git('show', event['commit'] + ':' + write['repo_path'])
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
           'parent_head_preserved': OLD_HEAD, 'prior_commits_preserved': 24, 'commits': 25,
           'artifact_paths': 27, 'revision_records': blob_checks,
           'unique_message_attachment_references': 19, 'reference_counts': counts,
           'matched_snapshot_messages': 7, 'matched_snapshot_reference_pairs': 16,
           'later_message_reported_only': 1, 'distinct_binary_revision_count': None,
           'version_1_3_1_classification': 'literal code/README state; no visible release announcement',
           'announced_latest_version': '1.6.0', 'version_1_6_original_bytes_available': False,
           'offline_repaired_gallery_attachment_delivered': False,
           'final_files_checked': len(hashes), 'tracked_files': len(git('ls-files').splitlines()),
           'status_porcelain': '', 'remotes': '', 'fsck': 'passed --full --strict',
           'source_author_dates': 'chronological', 'completed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
           'log': git('log', '--reverse', '--format=%h %aI %s').decode()}
(ROOT / 'verification-final.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in summary.items() if k != 'log'}, ensure_ascii=False, indent=2))
print(git('status', '--short', '--branch').decode())
print(git('log', '-3', '--format=%h %aI %s').decode())
