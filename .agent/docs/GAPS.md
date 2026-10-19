# Lacunas remanescentes e recuperações concluídas

Os grupos originais **v1.4.0 (3 arquivos), v1.5.0 (4) e v1.6.0 (3)** foram recebidos por upload e seus dez hashes conferem. Isso resolve a ausência desses instaladores, suítes, READMEs e do corpo de `TF2_HUD_Visual_Comparison.html`. [UPLOADS.md](UPLOADS.md) registra nomes, origem e commits. Nenhum conteúdo desconhecido foi inventado.

## O que ainda impede afirmar recuperação integral

- **Originais dos anexos anteriores:** nove referências únicas de mensagem + anexo continuam sem bytes originais associados: o primeiro link do instalador, seu relink, v1.2.0 e os dois grupos v1.3.0. São cinco referências ao instalador, duas aos testes e duas a README. Conteúdos literais e reconstruções relacionados estão no Git, mas não comprovam os bytes originais desses anexos nem se os links repetidos correspondem a versões iguais ou distintas.
- **Resultados ocultos e artefatos do runtime:** 213 nós da captura redigem saídas de ferramentas. Permanecem indisponíveis corpos históricos de logs de testes, JSONs de consultas, downloads, ZIPs, imagens e alguns backups, conforme `.agent/provenance/references.json`. Por exemplo: `test_results.txt`, `test-results-final.txt`, `hud_test_output.txt`, `fetch-results.json`, `middlemann.zip` e `hud_gallery_work/centerhud.webp`. A disponibilidade do original v1.4.0 não prova, sozinha, a identidade byte a byte dos backups em `/mnt/data/previous/`.
- **Arquivos gerados a partir de entradas desconhecidas:** configurações finais, `setup_hook.cfg`, migrações de classes, manifests e fixtures dependem do ambiente ou da execução original. Seus templates ficam preservados nos scripts. Somente blocos CFG explicitamente disponíveis no guia foram extraídos; nenhum script foi executado para fabricar resultados históricos.
- **Cobertura da fonte:** as respostas públicas continuam contendo os mesmos 615 nós e 89 mensagens de código e não incluem a mensagem v1.6.0. Seus três arquivos foram recuperados pelo upload, mas esse recebimento não recupera saídas ocultas, edições intermediárias ou o texto integral posterior ausente da captura.

## Distinções preservadas

**Originais recebidos** são os dez arquivos fornecidos pelo usuário nos três grupos, com transporte e hashes finais verificados. A associação aos anúncios foi fornecida pelo pai e é corroborada por declarações de versão. Não houve download independente dos antigos endpoints de anexos, portanto não se presume equivalência entre todas as 19 referências históricas.

**Conteúdos literais** são corpos diretamente disponíveis na captura. **Reconstruções estáticas** resultam de operações de texto extraídas como dados, com receitas e hashes registrados. As duas variantes v1.3.0 exigem bases diferentes; essa inferência está documentada. `1.3.1` é estado literal de código/README, sem anúncio visível de lançamento.

**Candidatos incompletos históricos** são os dois arquivos em `.agent/reconstructions/incomplete-v1.5.0/`, produzidos quando a base v1.4.0 ainda estava ausente. Seus bytes de código foram preservados. Não foram convertidos em originais nem regenerados; os originais v1.5.0 estão no commit `618beb0913ab4670bdc0a035e4fa7fe376a99963`.

**Galeria:** o HTML original recebido contém 15 referências externas a imagens, não seus binários. `TF2_HUD_Gallery.html` é uma reconstrução estática anterior e permanece separado. O anúncio v1.6.0 informa que os screenshots não puderam ser baixados e que a galeria offline deveria ser construída no PC. Uma galeria já reparada não foi entregue como anexo; ela não é uma versão faltante a ser inventada.

As tentativas de acesso pelo navegador e a recusa de controle do app estão mantidas como evidências históricas em `BROWSER_ACCESS.md`. O Mac foi confirmado desbloqueado; essas limitações não impediram a recuperação por upload. Não é necessário repetir downloads dos dez arquivos já recebidos. Para resolver as ausências acima seriam necessários os bytes correspondentes ou evidência verificável de identidade; sua existência não é presumida.
