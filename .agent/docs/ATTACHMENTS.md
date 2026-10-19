# Referências a anexos nas mensagens visíveis

A auditoria direta realizada no pai esgotou **3 páginas, 26 mensagens, sem `content_omitted`**. São **19 referências únicas de mensagem + nome de anexo**: **8 do instalador, 5 dos testes, 5 de README e 1 de HTML**. **Isso não confirma 19 revisões binárias distintas.** A repetição de um link também não comprova que seus bytes permaneceram iguais.

As sete primeiras mensagens e suas 16 referências únicas foram conferidas diretamente contra os textos da captura pública. A mensagem posterior v1.6.0 e suas três referências são evidência relatada pelo pai; seus bytes foram recebidos posteriormente por upload, enquanto o texto integral permanece ausente da captura pública. A galeria HTML aparece duas vezes na mensagem v1.5.0, mas conta como um único par mensagem + anexo.

| Horário UTC | Rótulo visível | Mensagem | Anexos distintos nessa mensagem |
|---|---|---|---|
| 2026-10-18 00:37 UTC | sem versão declarada | [2c2ebc16-741c-48e5-84fb-c2023c643341](https://chatgpt.com/c/6acfa42a-f8fc-83e8-b025-370fd5942d5b?messageId=2c2ebc16-741c-48e5-84fb-c2023c643341) | `setup_tf2_bazzite.py` |
| 2026-10-18 00:46 UTC | sem versão nova; relink | [3d1026f5-29a5-4318-8091-2f5a8b143c83](https://chatgpt.com/c/6acfa42a-f8fc-83e8-b025-370fd5942d5b?messageId=3d1026f5-29a5-4318-8091-2f5a8b143c83) | `setup_tf2_bazzite.py` |
| 2026-10-19 02:43 UTC | 1.2.0 | [b59710b3-be3f-4531-bef4-76ec764c8ec3](https://chatgpt.com/c/6acfa42a-f8fc-83e8-b025-370fd5942d5b?messageId=b59710b3-be3f-4531-bef4-76ec764c8ec3) | `setup_tf2_bazzite.py` |
| 2026-10-19 03:34 UTC | 1.3.0 | [49a6cc70-733a-44f2-be7d-384c1382ae26](https://chatgpt.com/c/6acfa42a-f8fc-83e8-b025-370fd5942d5b?messageId=49a6cc70-733a-44f2-be7d-384c1382ae26) | `setup_tf2_bazzite.py`, `TF2_HUD_UPDATE_README.md`, `test_setup_tf2_bazzite.py` |
| 2026-10-19 03:45 UTC | 1.3.0 | [62fc5fff-4c15-45a9-b7cd-a332d4e886ac](https://chatgpt.com/c/6acfa42a-f8fc-83e8-b025-370fd5942d5b?messageId=62fc5fff-4c15-45a9-b7cd-a332d4e886ac) | `setup_tf2_bazzite.py`, `TF2_HUD_Update_README.md`, `test_setup_tf2_bazzite.py` |
| 2026-10-19 12:00 UTC | 1.4.0 | [5ee4f90d-4bdd-4de7-9845-74f77fe5e13a](https://chatgpt.com/c/6acfa42a-f8fc-83e8-b025-370fd5942d5b?messageId=5ee4f90d-4bdd-4de7-9845-74f77fe5e13a) | `setup_tf2_bazzite.py`, `TF2_HUD_Update_README.md`, `test_setup_tf2_bazzite.py` |
| 2026-10-19 12:30 UTC | 1.5.0 | [454439cb-235e-4787-96c0-19a40f8c2b1d](https://chatgpt.com/c/6acfa42a-f8fc-83e8-b025-370fd5942d5b?messageId=454439cb-235e-4787-96c0-19a40f8c2b1d) | `setup_tf2_bazzite.py`, `TF2_HUD_Update_README.md`, `test_setup_tf2_bazzite.py`, `TF2_HUD_Visual_Comparison.html` |
| 2026-10-19 13:12 UTC | 1.6.0 | [e4b8944c-7916-4302-8016-463828ec503e](https://chatgpt.com/c/6acfa42a-f8fc-83e8-b025-370fd5942d5b?messageId=e4b8944c-7916-4302-8016-463828ec503e) | `setup_tf2_bazzite.py`, `TF2_HUD_Update_README.md`, `test_setup_tf2_bazzite.py` |

O README de 03:34 usa `TF2_HUD_UPDATE_README.md`; a partir de 03:45, os anúncios usam `TF2_HUD_Update_README.md`. A diferença de maiúsculas foi preservada no histórico Git e nos metadados de origem. Na árvore atual, os guias históricos usam nomes descritivos sem README; [layout.json](../manifests/layout.json) registra a correspondência.

## Estado literal de código 1.3.1

`1.3.1` não é um rótulo de lançamento nas mensagens visíveis auditadas. É um estado literal do código recuperado: a mensagem de código 451 (`5bd64030-9aa7-4890-8d69-d72572b6defb`) contém `SCRIPT_VERSION` alterado de `1.3.0` para `1.3.1`; o README literal da mensagem 458 (`2605ea9c-a8e4-4313-ab69-9b2de2883044`) também identifica o instalador como v1.3.1. A reconstrução é preservada no histórico, com receita e hash próprios. O anúncio visível posterior usa v1.4.0; a divergência não foi corrigida por suposição.

A mensagem v1.6.0 confirma que os binários dos screenshots não foram baixados e que a galeria offline deveria ser construída no PC. Uma galeria já reparada não foi entregue como anexo.

Dados estruturados: `.agent/provenance/attachment-references.json`, `.agent/provenance/announced-revisions.json` e `.agent/provenance/code-version-states.json`. O relato da auditoria está preservado em `.agent/provenance/supplemental-evidence/complete-attachment-audit-parent-report.json`.

Rechecagem de 19/10/2026 às 14:57/14:58 UTC: o link atualizado ainda contém as mesmas 16 referências literais das sete primeiras mensagens. A mensagem v1.6.0 e suas três referências continuam ausentes da resposta pública e fundamentadas no relato do pai. Nenhuma nova referência ou identidade binária foi confirmada.

## Bytes recebidos para o grupo v1.4.0

O usuário forneceu os três arquivos do grupo associado à mensagem `5ee4f90d-4bdd-4de7-9845-74f77fe5e13a` como “1o turno”. Os hashes conferem e instalador, testes e README identificam v1.4.0. Foram importados em `34220f09ebaae2b85b88fdc9e12a6285ca655ce5`; nomes de upload e hashes constam em [UPLOADS.md](UPLOADS.md). A associação é fornecida pelo usuário e compatível com o conteúdo; não se deduz identidade binária para os demais links. O total permanece 19 referências de mensagem + anexo, agora com três conteúdos originais fornecidos por upload verificados.

## Recuperação posterior dos grupos 2 e 3

O grupo “2o turno” acrescentou os quatro originais v1.5.0 no commit `618beb0913ab4670bdc0a035e4fa7fe376a99963`, incluindo `TF2_HUD_Visual_Comparison.html`. O grupo “3o turno” acrescentou os três originais v1.6.0 no commit `8f781c29adfd62533057c4f87b28af3adb478c8b`. Os sete hashes finais e as 28 partes de transporte conferem.

Há agora **dez conteúdos originais recebidos por upload, em três grupos**, associados aos anúncios v1.4.0/v1.5.0/v1.6.0. **Nove referências anteriores** continuam sem originais associados: cinco do instalador, duas dos testes e duas de README. As 19 referências continuam não sendo uma contagem de revisões binárias distintas; o vínculo entre grupos recebidos e anúncios não equivale a download independente de cada endpoint histórico. Nomes, hashes, Library IDs e recibos estão em [UPLOADS.md](UPLOADS.md).
