"""Reconcile original upload provenance, remaining gaps and append-only Git history."""
from pathlib import Path
import ast
import collections
import datetime as dt
import hashlib
import json

from import_uploaded_groups import ENV, OLD_HEAD, REPO, ROOT, git, jwrite

NOW = dt.datetime.now(dt.timezone.utc).isoformat()


def load(relative):
    return json.loads((REPO / relative).read_text())


def save(relative, value):
    jwrite(REPO / relative, value)


def text(relative, value):
    (REPO / relative).write_text(value)


def main():
    imported = json.loads((ROOT / 'uploaded-groups-import-result.json').read_text())
    groups = imported['groups']
    assert len(groups) == 2
    assert git('rev-parse', 'HEAD').decode().strip() == groups[-1]['event']['commit']
    assert not git('status', '--porcelain')
    prior = imported['prior_commits']
    assert len(prior) == 30 and prior[-1] == OLD_HEAD
    events = load('.provenance/revisions.json')
    assert len(events) == 23
    for group in groups:
        event = group['event']
        assert not any(e['sequence'] == event['sequence'] for e in events)
        events.append(event)
        save(f'.provenance/events/user-upload-turn-{group["group"]}.json', event)
        receipt_path = group['receipt_directory'] + '/receipt.json'
        receipt = load(receipt_path)
        receipt['content_commit'] = event['commit']
        save(receipt_path, receipt)
    writes = [w for e in events for w in e['writes']]
    paths = collections.Counter(w['repo_path'] for w in writes)
    types = collections.Counter(w['status'] for w in writes)
    assert len(events) == 25 and len(writes) == 52 and len(paths) == 28
    assert dict(types) == {'available_literal': 18, 'static_reconstruction': 22, 'partial_static_candidate': 2, 'original_user_upload': 10}
    syntax_count = 0
    for event in events:
        for write in event['writes']:
            raw = git('show', event['commit'] + ':' + write['repo_path'])
            assert len(raw) == write['bytes'] and hashlib.sha256(raw).hexdigest() == write['sha256']
            if write['repo_path'].endswith('.py'):
                ast.parse(raw.decode('utf-8'), filename=write['repo_path'])
                syntax_count += 1
    save('.provenance/revisions.json', events)
    chronological = sorted(events, key=lambda e: (e['source_timestamp'], str(e['sequence'])))
    save('.provenance/source-chronology.json', {
        'ordering': 'Original source timestamp; Git history remains append-only in acquisition order.',
        'events': [{'source_timestamp_utc': dt.datetime.fromtimestamp(e['source_timestamp'], dt.timezone.utc).isoformat(),
                    'sequence': e['sequence'], 'source_message_id': e['message_id'], 'commit': e['commit'],
                    'write_count': len(e['writes']), 'late_user_upload': isinstance(e['sequence'], str)} for e in chronological]})

    capture = load('.provenance/capture.json')
    for group in groups:
        event = group['event']
        capture['user_upload_groups'].append({'group': event['upload_label'], 'declared_version': group['version'],
            'files': len(event['writes']), 'upload_message_id': event['upload_message_id'],
            'receipt': group['receipt_directory'] + '/receipt.json', 'content_commit': event['commit'], 'all_hashes_verified': True})
    capture.update(revision_records=52, artifact_paths=28, classification=dict(types), total_commits=33,
                   content_commits=25, documentation_evidence_commits=8)
    capture['validation'].update(sha256_revision_checks=52, python_static_parses=syntax_count, recovered_code_executions=0, test_runs=0)
    capture['later_announced_version'].update(content_available=True, original_user_upload_receipt=groups[1]['receipt_directory'] + '/receipt.json',
                                             announcement_text_available_in_public_snapshot=False)
    capture['late_recovery_dates'] = 'All 30 earlier commits preserved. Original uploads v1.5.0 then v1.6.0 appended in acquisition order; Git dates record import. Original announcement dates are retained in source-chronology.json and receipts.'
    capture['current_canonical_versions'] = {'setup_tf2_bazzite.py': '1.6.0', 'test_setup_tf2_bazzite.py': '1.6.0',
        'TF2_HUD_Update_README.md': '1.6.0', 'TF2_HUD_Visual_Comparison.html': '1.5.0 upload group; no standalone semantic version in HTML'}
    save('.provenance/capture.json', capture)

    announcements = load('.provenance/announced-revisions.json')
    references = load('.provenance/references.json')
    attachment_refs = load('.provenance/attachment-references.json')
    code_states = load('.provenance/code-version-states.json')
    for group in groups:
        event = group['event']; receipt = group['receipt_directory'] + '/receipt.json'
        for item in announcements:
            if item['source_message_id'] == event['message_id']:
                item.update(content_status='original_user_uploads_received_and_hash_verified', receipt=receipt,
                            content_commit=event['commit'], note='Original user uploads associated with this version group by the parent; version declarations match. No byte identity across other historical links inferred.')
        for write in event['writes']:
            ref = next(r for r in references if r['original_path'] == '/mnt/data/' + write['repo_path'])
            ref['revisions'].append({'sequence': event['sequence'], 'commit': event['commit'], 'repo_path': write['repo_path'],
                                    'status': 'original_user_upload', 'sha256': write['sha256'], 'upload_name': write['upload_name'],
                                    'original_source_path_independently_known': write['original_path'] is not None})
            ref['status'] = 'archived'
            for attachment in attachment_refs['references']:
                if attachment['message_id'] == event['message_id'] and attachment['filename'] == write['repo_path']:
                    attachment.update(user_uploaded_bytes_verified=True, uploaded_sha256=write['sha256'],
                        upload_name=write['upload_name'], user_upload_receipt=receipt, content_commit=event['commit'],
                        binary_revision_identity=f'Original user-uploaded v{group["version"]} bytes verified. Other historical links are not inferred to share or differ in bytes.')
        installer = next(w for w in event['writes'] if w['repo_path'] == 'setup_tf2_bazzite.py')
        code_states.append({'version': group['version'], 'classification': 'original_user_upload', 'receipt': receipt,
                            'content_commit': event['commit'], 'installer_sha256': installer['sha256'],
                            'literal_SCRIPT_VERSION': group['version'], 'source_announcement_message_id': event['message_id']})
    attachment_refs.update(verified_user_upload_group_count=3, verified_user_uploaded_file_count=10)
    attachment_refs['verification_semantics'] = {
        'user_uploaded_bytes_verified': 'Received original file bytes match the supplied SHA-256; version group association is supplied by the user/parent and corroborated by file text.',
        'original_attachment_bytes_verified': 'Independent byte retrieval from the historical attachment endpoint; not performed. This field remains false.',
        'reference_count_is_not_binary_revision_count': True}
    unmatched = [r for r in attachment_refs['references'] if not r.get('user_uploaded_bytes_verified')]
    assert len(unmatched) == 9
    attachment_refs['references_without_associated_original_upload'] = len(unmatched)
    for ref in references:
        if ref['original_path'] in ['/mnt/data/previous/setup_tf2_bazzite_v1_4_0.py', '/mnt/data/previous/test_setup_tf2_bazzite_v1_4_0.py']:
            ref['related_available_original_upload'] = '.provenance/user-uploads/turn-1-v1.4.0/receipt.json'
            ref['identity_note'] = 'Related v1.4.0 original is now available, but byte identity of this historical backup path is not independently proven; no copy fabricated.'
    save('.provenance/announced-revisions.json', announcements)
    save('.provenance/references.json', references)
    save('.provenance/attachment-references.json', attachment_refs)
    save('.provenance/code-version-states.json', code_states)

    gaps = load('.provenance/gaps.json')
    by_version = {g['version']: g for g in groups}
    for gap in gaps:
        if gap['id'] in ['version_1_5_0', 'version_1_6_0', 'visual_comparison']:
            group = by_version['1.6.0' if gap['id'] == 'version_1_6_0' else '1.5.0']
            gap.update(status='resolved_by_original_user_upload',
                detail='Original user-uploaded contents received and final hashes verified; historical candidates and source limitations remain recorded.',
                resolution={'receipt': group['receipt_directory'] + '/receipt.json', 'commit': group['event']['commit'],
                            'files': [w['repo_path'] for w in group['event']['writes']]})
            if gap['id'] == 'version_1_5_0':
                gap['historical_unmatched_replacement_still_recorded'] = True
                gap['incomplete_candidate_status'] = 'Retained unchanged as historical reconstruction; superseded in canonical paths by verified originals.'
        elif gap['id'] == 'sandbox_attachments':
            gap.update(detail='Ten original files from v1.4.0/v1.5.0/v1.6.0 received via user uploads. Earlier historical attachment endpoints and internal runtime artifacts remain unavailable.',
                       user_upload_recovery={'groups': capture['user_upload_groups'], 'verified_file_count': 10})
        elif gap['id'] == 'attachment_binary_identity':
            gap.update(verified_original_user_uploads=10, references_without_associated_original_upload=9,
                       detail='There are 19 message+attachment references, with ten associated original user uploads in three release groups. Earlier nine references have no associated original attachment bytes. Reference counts do not prove distinct binary revisions.',
                       identity_note='No independent byte-level historical endpoint identity claimed; no equivalence or distinctness inferred across repeated links.')
        elif gap['id'] == 'snapshot_coverage':
            gap.update(later_v1_6_original_upload_received=True, public_snapshot_still_earlier=True,
                       detail='The public snapshot still excludes the v1.6.0 announcement; its three original file bodies are now recovered through the third user upload group.')
        elif gap['id'] == 'updated_share_still_serves_same_message_content':
            gap['received_version_groups_no_longer_blocked'] = ['1.4.0', '1.5.0', '1.6.0']
        elif gap['id'] in ['authenticated_browser_requires_chatgpt_login', 'native_chatgpt_app_control_denied', 'original_context_access']:
            gap['received_version_groups_recovered_by_upload'] = ['1.4.0', '1.5.0', '1.6.0']
            gap['current_recovery_note'] = 'Access attempt retained as historical evidence. No repeat download or app-control attempt required for files already received.'
            if 'next_step' in gap:
                gap['next_step'] = 'Received groups are archived. Earlier unresolved bytes require corresponding originals or evidence; app-control denial was not retried.'
        elif gap['id'] == 'redacted_tool_results':
            gap.update(redacted_node_count=213, tool_text_node_count=222,
                       detail='213 source nodes explicitly redact tool results. Logs, fetch JSON, image downloads, ZIPs and historical test output cannot be recovered or verified from the visible text.')
    gaps.append({'id': 'earlier_attachment_originals', 'status': 'original_bytes_unavailable',
        'unique_message_attachment_references': 9, 'counts': dict(collections.Counter(r['category'] for r in unmatched)),
        'references': [{'message_id': r['message_id'], 'filename': r['filename'], 'announced_version': r['announced_version']} for r in unmatched],
        'detail': 'Initial link, relink, v1.2.0 and both v1.3.0 groups remain unverified as original attachment bytes. Related literal and reconstructed source states are already preserved.'})
    save('.provenance/gaps.json', gaps)

    upload_groups = []
    for meta in capture['user_upload_groups']:
        receipt = load(meta['receipt'])
        methods = 56 if meta['declared_version'] == '1.4.0' else next(g['static_test_methods'] for g in groups if g['version'] == meta['declared_version'])
        upload_groups.append((meta, receipt, methods))
    upload_doc = ['# Originais recebidos por upload', '',
        '**Dez arquivos originais**, em três grupos, foram preservados byte a byte sob nomes canônicos. Os sufixos dos nomes recebidos são metadados de upload e não números de revisão. Todos os hashes das partes e dos arquivos completos conferem.', '',
        'A raiz contém instalador, testes e README **v1.6.0**, além do HTML do grupo **v1.5.0**. As versões anteriores permanecem nos commits abaixo. A associação aos anúncios vem do usuário/pai e das declarações de versão; ela não comprova identidade binária com outros links históricos.', '']
    for meta, receipt, methods in upload_groups:
        upload_doc += [f'## {meta["group"]} — v{meta["declared_version"]}', '',
            f'Commit `{meta["content_commit"]}`. Mensagem de envio `{meta["upload_message_id"]}`. Anúncio de origem `{receipt.get("user_indicated_origin_message_id", receipt.get("associated_announcement_message_id"))}`, em {receipt["origin_announcement_timestamp_utc"]}.', '',
            '| Nome recebido | Nome canônico no Git | Bytes | SHA-256 |', '|---|---|---:|---|']
        upload_doc += [f'| `{w["upload_name"]}` | `{w["repo_path"]}` | {w["bytes"]} | `{w["sha256"]}` |' for w in receipt['files']]
        upload_doc += ['', f'Instalador, docstring da suíte e título do README identificam v{meta["declared_version"]}. Foram contados **{methods} métodos de teste por AST**, sem executá-los. Comprovantes: `{str(Path(meta["receipt"]).parent)}/`.', '']
    upload_doc += ['Os IDs Library dos grupos 1 e 2 foram fornecidos como conjuntos, sem correspondência individual entre ID e arquivo. O grupo 3 inclui essa correspondência, preservada no recibo. Os nomes canônicos vêm dos nomes usados na conversa; para v1.6.0, a URL sandbox exata não foi fornecida e nenhum caminho absoluto original foi inventado.', '',
        'O HTML original contém 15 referências externas a imagens e não incorpora os respectivos binários. Foi lido como texto, sem renderização, execução de scripts ou acesso às URLs. Nenhuma galeria offline reparada foi recebida; o chat orienta construí-la no PC.', '',
        'Os commits de recuperação tardia foram acrescentados em ordem v1.4.0 → v1.5.0 → v1.6.0, preservando todos os commits anteriores. Suas datas Git registram a importação; as datas históricas dos anúncios estão nos recibos e em `.provenance/source-chronology.json`.', '',
        '**Nenhum código, teste ou configuração recuperado foi executado.** Os candidatos antigos de v1.5.0 permanecem identificados como incompletos. [GAPS.md](GAPS.md) registra as ausências remanescentes.', '']
    text('UPLOADS.md', '\n'.join(upload_doc))

    text('README.md', f'''# TF2 Competitive Setup Linux — arquivo da conversa

Repositório Git local da [conversa compartilhada](https://chatgpt.com/share/6ad6143e-d894-83e9-a306-302b4fc65c66), em `/Users/marcelofcandido/git/personal/games/competitive-tf2`, no `NEBULOSA-2.local`.

**Os originais v1.4.0, v1.5.0 e v1.6.0 recebidos por upload estão arquivados.** Na raiz, `setup_tf2_bazzite.py`, `test_setup_tf2_bazzite.py` e `TF2_HUD_Update_README.md` são v1.6.0; `TF2_HUD_Visual_Comparison.html` é o HTML original do grupo v1.5.0. As versões anteriores estão no histórico. Nomes recebidos, hashes e commits: [UPLOADS.md](UPLOADS.md).

São **33 commits**, com **25 importações de conteúdo** e **8 de documentação/evidências**. Os **28 caminhos de artefatos** possuem **52 registros de revisão**: **18 conteúdos literais da captura, 22 reconstruções estáticas, 2 candidatos históricos incompletos e 10 originais recebidos por upload**. Os 30 commits anteriores a estes dois grupos foram preservados. Registros e links repetidos não significam versões binárias distintas.

O instalador possui 11 estados arquivados em seu caminho canônico. `1.3.1` permanece como estado literal de código/README, sem anúncio visível de lançamento. As duas implementações v1.3.0 foram preservadas. Os candidatos incompletos v1.5.0 continuam separados, com seus bytes originais de reconstrução e limitação histórica registrados.

**Ainda não é possível declarar recuperadas todas as versões de todos os arquivos.** Das 19 referências de mensagem + anexo, nove referências anteriores aos grupos recebidos continuam sem bytes originais associados. Logs, JSONs de consultas, ZIPs, imagens e arquivos gerados dependentes da execução também têm lacunas. Veja [GAPS.md](GAPS.md) e [ATTACHMENTS.md](ATTACHMENTS.md).

**Nenhum instalador, script de alteração, teste ou CFG recuperado foi executado.** A validação usa hashes, comparação de bytes e análise sintática estática. Foram contados 56, 75 e 103 métodos de teste nas suítes v1.4.0, v1.5.0 e v1.6.0; esses números não são resultados de execução. O HTML externo foi preservado sem baixar imagens; uma galeria offline reparada não foi entregue no chat.

## Consultar o histórico

```bash
git status --short
git log --reverse --format='%h %aI %s'
git log --follow -- setup_tf2_bazzite.py
git show {groups[0]['event']['commit']}:setup_tf2_bazzite.py
```

[REVISIONS.md](REVISIONS.md) e `.provenance/revisions.json` registram commits, mensagens, nomes originais, classificação e SHA-256. `.provenance/source-chronology.json` ordena os eventos pela data da fonte. Os commits iniciais preservam essas datas em `AuthorDate`; recuperações tardias e documentação usam a data de importação, mantendo as datas históricas nos manifestos e sem reescrever o Git.

As capturas públicas e rechecagens estão arquivadas como dados; [REFRESH.md](REFRESH.md) explica seus limites. [BROWSER_ACCESS.md](BROWSER_ACCESS.md) registra tentativas históricas de acesso. Os sete novos arquivos vieram dos uploads transferidos pelo pai, não dessas tentativas.

O README `TF2_HUD_UPDATE_README.md` permanece em `case-variants/` para preservar maiúsculas no macOS. O CFG opcional de Medic está em `alternatives/medic/`. Templates de arquivos dependentes da instalação TF2 permanecem dentro dos scripts. Não há remoto configurado e nada foi publicado.
''')

    text('GAPS.md', f'''# Lacunas remanescentes e recuperações concluídas

Os grupos originais **v1.4.0 (3 arquivos), v1.5.0 (4) e v1.6.0 (3)** foram recebidos por upload e seus dez hashes conferem. Isso resolve a ausência desses instaladores, suítes, READMEs e do corpo de `TF2_HUD_Visual_Comparison.html`. [UPLOADS.md](UPLOADS.md) registra nomes, origem e commits. Nenhum conteúdo desconhecido foi inventado.

## O que ainda impede afirmar recuperação integral

- **Originais dos anexos anteriores:** nove referências únicas de mensagem + anexo continuam sem bytes originais associados: o primeiro link do instalador, seu relink, v1.2.0 e os dois grupos v1.3.0. São cinco referências ao instalador, duas aos testes e duas a README. Conteúdos literais e reconstruções relacionados estão no Git, mas não comprovam os bytes originais desses anexos nem se os links repetidos correspondem a versões iguais ou distintas.
- **Resultados ocultos e artefatos do runtime:** 213 nós da captura redigem saídas de ferramentas. Permanecem indisponíveis corpos históricos de logs de testes, JSONs de consultas, downloads, ZIPs, imagens e alguns backups, conforme `.provenance/references.json`. Por exemplo: `test_results.txt`, `test-results-final.txt`, `hud_test_output.txt`, `fetch-results.json`, `middlemann.zip` e `hud_gallery_work/centerhud.webp`. A disponibilidade do original v1.4.0 não prova, sozinha, a identidade byte a byte dos backups em `/mnt/data/previous/`.
- **Arquivos gerados a partir de entradas desconhecidas:** configurações finais, `setup_hook.cfg`, migrações de classes, manifests e fixtures dependem do ambiente ou da execução original. Seus templates ficam preservados nos scripts. Somente blocos CFG explicitamente disponíveis no guia foram extraídos; nenhum script foi executado para fabricar resultados históricos.
- **Cobertura da fonte:** as respostas públicas continuam contendo os mesmos 615 nós e 89 mensagens de código e não incluem a mensagem v1.6.0. Seus três arquivos foram recuperados pelo upload, mas esse recebimento não recupera saídas ocultas, edições intermediárias ou o texto integral posterior ausente da captura.

## Distinções preservadas

**Originais recebidos** são os dez arquivos fornecidos pelo usuário nos três grupos, com transporte e hashes finais verificados. A associação aos anúncios foi fornecida pelo pai e é corroborada por declarações de versão. Não houve download independente dos antigos endpoints de anexos, portanto não se presume equivalência entre todas as 19 referências históricas.

**Conteúdos literais** são corpos diretamente disponíveis na captura. **Reconstruções estáticas** resultam de operações de texto extraídas como dados, com receitas e hashes registrados. As duas variantes v1.3.0 exigem bases diferentes; essa inferência está documentada. `1.3.1` é estado literal de código/README, sem anúncio visível de lançamento.

**Candidatos incompletos históricos** são os dois arquivos em `reconstructions/incomplete-v1.5.0/`, produzidos quando a base v1.4.0 ainda estava ausente. Seus bytes de código foram preservados. Não foram convertidos em originais nem regenerados; os originais v1.5.0 estão no commit `{groups[0]['event']['commit']}`.

**Galeria:** o HTML original recebido contém 15 referências externas a imagens, não seus binários. `TF2_HUD_Gallery.html` é uma reconstrução estática anterior e permanece separado. O anúncio v1.6.0 informa que os screenshots não puderam ser baixados e que a galeria offline deveria ser construída no PC. Uma galeria já reparada não foi entregue como anexo; ela não é uma versão faltante a ser inventada.

As tentativas de acesso pelo navegador e a recusa de controle do app estão mantidas como evidências históricas em `BROWSER_ACCESS.md`. O Mac foi confirmado desbloqueado; essas limitações não impediram a recuperação por upload. Não é necessário repetir downloads dos dez arquivos já recebidos. Para resolver as ausências acima seriam necessários os bytes correspondentes ou evidência verificável de identidade; sua existência não é presumida.
''')

    doc = ['# Revisões recuperadas', '',
        '**52 registros em 28 caminhos de artefatos.** Classificação: 18 literais, 22 reconstruções estáticas, dois candidatos incompletos e dez originais recebidos por upload. São 25 commits de conteúdo e oito de documentação/evidências, totalizando 33. Os 30 commits anteriores aos grupos 2 e 3 permanecem intactos.', '',
        'A tabela segue a data da fonte. Recuperações tardias aparecem em commits acrescentados ao final do Git; seus recibos preservam a data histórica, sem reescrever o histórico existente.', '',
        '| Fonte/grupo | Data da fonte UTC | Commit de conteúdo | Arquivos |', '|---|---|---|---|']
    for e in chronological:
        label = f'{e["sequence"]:04d}' if isinstance(e['sequence'], int) else e.get('upload_label', str(e['sequence']))
        date = dt.datetime.fromtimestamp(e['source_timestamp'], dt.timezone.utc).isoformat()
        doc.append(f'| {label} | {date} | `{e["commit"]}` | ' + ', '.join('`' + w['repo_path'] + '`' for w in e['writes']) + ' |')
    doc += ['', '| Caminho no repositório | Registros de revisão |', '|---|---:|']
    doc += [f'| `{name}` | {count} |' for name, count in paths.items()]
    doc += ['', 'Os detalhes de cada revisão, inclusive classificação, nome recebido, caminho original quando conhecido, receita e SHA-256, estão em `.provenance/revisions.json`. A contagem mede registros de preservação e não afirma que cada registro ou link representa bytes distintos.', '',
        'O instalador canônico possui 11 estados. As duas implementações v1.3.0 e o estado literal 1.3.1 foram mantidos. Os candidatos incompletos v1.5.0 continuam classificados como tal; não substituem o grupo original recebido.', '',
        'A raiz agora apresenta o grupo v1.6.0 para instalador, testes e README e o HTML original do grupo v1.5.0. As suítes originais têm 56, 75 e 103 métodos de teste contados estaticamente, sem execução. O corpo do HTML foi recebido; os screenshots externos e uma galeria offline já reparada não foram entregues.', '',
        'As rechecagens públicas não acrescentaram conteúdo à captura. Os originais posteriores vieram por upload. A auditoria de 19 referências históricas, com nove ainda sem originais associados, permanece em [ATTACHMENTS.md](ATTACHMENTS.md). [GAPS.md](GAPS.md) descreve por que a recuperação integral ainda não pode ser declarada.', '']
    text('REVISIONS.md', '\n'.join(doc))
    attachment_doc = (REPO / 'ATTACHMENTS.md').read_text()
    attachment_doc = attachment_doc.replace('a mensagem posterior v1.6.0 e suas três referências são evidência relatada pelo pai; o texto integral e os bytes não foram recebidos por este executor.', 'a mensagem posterior v1.6.0 e suas três referências são evidência relatada pelo pai; seus bytes foram recebidos posteriormente por upload, enquanto o texto integral permanece ausente da captura pública.')
    attachment_doc = attachment_doc.replace('A mensagem posterior v1.6.0 e suas três referências são evidência relatada pelo pai; o texto integral e os bytes não foram recebidos por este executor.', 'A mensagem posterior v1.6.0 e suas três referências são evidência relatada pelo pai; seus bytes foram recebidos posteriormente por upload, enquanto o texto integral permanece ausente da captura pública.')
    attachment_doc += f'''\n## Recuperação posterior dos grupos 2 e 3

O grupo “2o turno” acrescentou os quatro originais v1.5.0 no commit `{groups[0]['event']['commit']}`, incluindo `TF2_HUD_Visual_Comparison.html`. O grupo “3o turno” acrescentou os três originais v1.6.0 no commit `{groups[1]['event']['commit']}`. Os sete hashes finais e as 28 partes de transporte conferem.

Há agora **dez conteúdos originais recebidos por upload, em três grupos**, associados aos anúncios v1.4.0/v1.5.0/v1.6.0. **Nove referências anteriores** continuam sem originais associados: cinco do instalador, duas dos testes e duas de README. As 19 referências continuam não sendo uma contagem de revisões binárias distintas; o vínculo entre grupos recebidos e anúncios não equivale a download independente de cada endpoint histórico. Nomes, hashes, Library IDs e recibos estão em [UPLOADS.md](UPLOADS.md).
'''
    text('ATTACHMENTS.md', attachment_doc)
    text('reconstructions/incomplete-v1.5.0/README.md', f'''# Candidato histórico incompleto, não um anexo original

Estes arquivos resultam das alterações de texto das mensagens 544 e 548 aplicadas à reconstrução v1.3.1 e seus testes. À época, a base v1.4.0 esperada estava ausente; a troca `1.4.0 → 1.5.0` não correspondia ao texto e nenhum número foi inventado.

Os originais v1.4.0 e v1.5.0 foram recebidos posteriormente. O grupo original v1.5.0 está no commit `{groups[0]['event']['commit']}`; o grupo v1.6.0 está na raiz. Veja `../../UPLOADS.md`. Os bytes de código deste candidato antigo foram preservados, sem nova reconstrução ou promoção a original. Nenhum destes scripts ou testes foi executado.
''')
    for path in ['BROWSER_ACCESS.md', 'REFRESH.md']:
        note = f'\nAtualização de recuperação em {NOW}: os grupos originais v1.4.0, v1.5.0 e v1.6.0 foram recebidos por upload e verificados. Os limites de acesso e de cobertura acima são históricos; não impediram essa via de transferência. As lacunas remanescentes estão em `GAPS.md`.\n'
        text(path, (REPO / path).read_text() + note)
    progress = (REPO / '.provenance/PROGRESS.md').read_text()
    progress += f'\n- {NOW}: recebidas e verificadas todas as 12 partes do grupo 2 e 16 do grupo 3; sete hashes finais conferem. Nenhuma parte pendente ou divergente.\n'
    for group in groups:
        progress += f'- Grupo {group["group"]}: v{group["version"]}, {len(group["event"]["writes"])} originais, commit {group["event"]["commit"]}, {group["static_test_methods"]} métodos de teste contados por AST; sem execução.\n'
    progress += '- Inventário reconciliado: 52 registros, 28 caminhos, dez originais recebidos. Trinta commits anteriores preservados; nove referências históricas anteriores continuam sem bytes originais associados. Candidatos incompletos preservados; nenhum script, teste ou CFG recuperado executado.\n'
    text('.provenance/PROGRESS.md', progress)
    (ROOT / 'PROGRESS.md').write_text(progress)
    for name in ['import_uploaded_groups.py', 'reconcile_uploaded_groups.py', 'receive_transfer_turn_2.py']:
        (REPO / '.provenance/tools' / name).write_bytes((ROOT / name).read_bytes())
    summary = {'recorded_at_utc': NOW, 'full_recovery_claimed': False, 'prior_commits_preserved': 30,
        'artifact_paths': 28, 'revision_records': 52, 'classification': dict(types),
        'original_user_upload_groups': 3, 'original_user_uploaded_files': 10,
        'new_transfer_parts_verified': 28, 'new_original_files_verified': 7, 'source_code_executions': 0, 'test_runs': 0,
        'historical_attachment_references': 19, 'references_without_associated_original_upload': 9,
        'remaining_reference_counts': dict(collections.Counter(r['category'] for r in unmatched)),
        'hash_checked_revision_records': 52, 'python_revision_AST_parses': syntax_count,
        'new_content_commits': [g['event']['commit'] for g in groups],
        'canonical_versions': capture['current_canonical_versions'],
        'remaining_gaps': ['Earlier original attachment bodies and binary identity', 'Redacted runtime logs, fetch JSON, ZIPs, images and backup identity', 'Generated outputs depending on missing original inputs or execution', 'Later full message text and intermediate source changes not present in public snapshot'],
        'not_a_missing_attachment': 'An already repaired offline gallery was never delivered.'}
    save('.provenance/upload-recovery-audit.json', summary)
    hashes = {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(REPO.rglob('*')) if p.is_file() and '.git' not in p.relative_to(REPO).parts
              and p != REPO / '.provenance/final-files.sha256.json'}
    save('.provenance/final-files.sha256.json', hashes)
    git('add', '--all')
    git('commit', '--no-verify', '-m', 'docs: reconcile original v1.5.0 v1.6.0 uploads and remaining archive gaps')
    history = git('rev-list', '--reverse', 'HEAD').decode().splitlines()
    assert len(history) == 33 and history[:30] == prior
    assert history[30:32] == [g['event']['commit'] for g in groups]
    for name, sha in hashes.items():
        assert hashlib.sha256((REPO / name).read_bytes()).hexdigest() == sha
    for write in groups[-1]['event']['writes']:
        assert hashlib.sha256((REPO / write['repo_path']).read_bytes()).hexdigest() == write['sha256']
    assert not git('status', '--porcelain') and not git('remote')
    git('fsck', '--full', '--strict')
    dates = [int(d) for d in git('log', '--reverse', '--format=%at').splitlines()]
    assert dates == sorted(dates)
    summary.update(repository=str(REPO), head=git('rev-parse', 'HEAD').decode().strip(), commits=33,
                   final_files_checked=len(hashes), tracked_files=len(git('ls-files').splitlines()),
                   status_porcelain='', remotes='', fsck='passed --full --strict',
                   log=git('log', '--reverse', '--format=%h %aI %s').decode(),
                   completed_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    jwrite(ROOT / 'verification-groups-2-3-final.json', summary)
    jwrite(ROOT / 'verification-final.json', summary)
    for group in groups:
        p = ROOT / f'pending-user-upload-turn-{group["group"]}.json'
        pending = json.loads(p.read_text())
        pending.update(status='imported_and_verified', inventory_commit=summary['head'])
        jwrite(p, pending)
    print(json.dumps({k: v for k, v in summary.items() if k != 'log'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
