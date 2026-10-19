# Lacunas da fonte

Este arquivo registra ausências; nenhum arquivo vazio foi criado para representar conteúdo desconhecido.

- **v1.4.0:** anunciada na resposta 468, mas a última edição de código disponível define `1.3.1`. Não há bytes completos de v1.4.0 nem a alteração intermediária correspondente.
- **v1.5.0:** a alteração 544 depende dessa base v1.4.0. Foi preservado um candidato em `reconstructions/incomplete-v1.5.0/`, obtido aplicando somente os trechos disponíveis à última base recuperável. A substituição de versão não encontra correspondência; o código conserva `1.3.1`. O candidato e seus testes não representam anexos originais verificados.
- **Duas variantes v1.3.0:** as mensagens 325 e 398 alteram uma base v1.2.0 de formas diferentes. Ambas estão no histórico. A escolha da base de 398 é uma inferência documentada, sustentada pelos textos antigos exigidos e pelo nome do backup em 359.
- **Galeria:** há gerador para `TF2_HUD_Gallery.html`, reconstruído estaticamente. O link da resposta usa `TF2_HUD_Visual_Comparison.html`, cujo conteúdo e eventual renomeação não estão disponíveis. Não foi criado um arquivo com esse nome por suposição.
- **Reparo das imagens:** aparecem a reclamação e uma tentativa de buscar imagens, mas os bytes baixados e a galeria reparada estão ausentes. URLs atuais não foram usadas para inventar cópias históricas.
- **Anexos e resultados ocultos:** há 213 mensagens com resultados de ferramentas redigidos. Links `sandbox:/mnt/data/...` não fornecem os bytes de anexos pela página pública. Logs, JSONs de consultas, ZIPs, imagens e backups cujo conteúdo não está visível constam em `.provenance/references.json` como indisponíveis.
- **Arquivos gerados:** configurações finais `autoexec.cfg`, `modules.cfg`, `setup_hook.cfg`, migrações de classes, manifests e fixtures dependem dos arquivos de entrada ou da execução original. Os templates permanecem no código; somente os blocos explicitamente fornecidos no guia foram extraídos como CFGs. O bloco opcional de Medic está em `alternatives/medic/`.
- **Pedido final:** a conversa termina com a solicitação de tratar dependências externas dos HUDs e uma intenção de atualizar. Nenhuma nova revisão concluída está disponível.

O Mac estava bloqueado, impedindo acesso ao navegador autenticado. A recuperação usou somente o link público explicitamente fornecido. Após a autorização decorrente da habilitação de memória, uma consulta de contexto restrita à conversa original retornou `Personal context is unavailable for this conversation.` neste executor; nenhum conteúdo foi recuperado por essa via. A API paginada `read_conversation_context` não está exposta aqui. Os IDs do compartilhamento e da conversa original não foram confundidos.

O menor próximo passo é recuperar os anexos na conversa original autenticada, após desbloquear o Mac, ou extrair o histórico integral pela API disponível no thread pai. Se os anexos estiverem expirados ou substituídos, serão necessários os arquivos originais/exportação/backups correspondentes; a existência desses bytes não pode ser presumida.
