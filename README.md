# TF2 Competitive Setup Linux — arquivo da conversa

Repositório Git **local** de preservação de [TF2 Competitive Setup Linux](https://chatgpt.com/share/6ad6143e-d894-83e9-a306-302b4fc65c66), recuperado em 2026-10-19T13:26:27.054350+00:00. Não é uma instalação de TF2.

Foram preservados **27 caminhos de artefatos**, com **42 registros de revisão** em **22 commits cronológicos de conteúdo** e **4 commits de documentação/evidências** (**26 commits no total**). Os registros se dividem em **18 conteúdos literais disponíveis**, **22 reconstruções estáticas** e **2 candidatos incompletos**. Cópias com bytes idênticos são identificadas pelos mesmos hashes; registros não significam 42 versões distintas.

O instalador na raiz possui **8 estados recuperáveis**: original sem `SCRIPT_VERSION`, ajuste inicial, v1.1.0, duas revisões v1.2.0, duas variantes v1.3.0 e v1.3.1. As oito revisões representam novos commits de importação. **Os bytes originais completos de v1.4.0, v1.5.0 e v1.6.0 não foram recuperados**, nem o HTML anunciado como `TF2_HUD_Visual_Comparison.html`. Veja [GAPS.md](GAPS.md).

Uma leitura posterior da conversa original, relatada pelo thread pai, identificou o [anúncio de v1.6.0](https://chatgpt.com/c/6acfa42a-f8fc-83e8-b025-370fd5942d5b?messageId=e4b8944c-7916-4302-8016-463828ec503e) em **19/10/2026 às 13:12:17 UTC**, com 103 testes relatados e as opções `--hud-info all`, `--fetch-hud middlemann --output` e `--build-gallery`. Essa mensagem **não consta nos 615 nós da captura pública**, que é um estado anterior da mesma conversa. A evidência suplementar é um relato identificado; o texto integral e os bytes dos anexos não foram recebidos aqui. O anúncio esclarece que os binários de screenshots não puderam ser baixados e que a galeria offline deveria ser construída no PC. **Não existe uma galeria já reparada a classificar como anexo faltante.**

A auditoria das mensagens visíveis registra **19 referências únicas de mensagem + anexo** (8 instalador, 5 testes, 5 README, 1 HTML), sem confirmar 19 revisões binárias. A sequência completa está em [ATTACHMENTS.md](ATTACHMENTS.md). **`1.3.1` é um estado literal de código e README recuperados, não um lançamento anunciado nas mensagens visíveis.** Ele permanece preservado com sua proveniência; os anúncios v1.3.0 e v1.4.0 são registrados separadamente.

Conteúdos literais vieram de heredocs/blocos fornecidos no chat; isso não equivale a verificar os bytes de um anexo original. Reconstruções usam somente extração de literais e edições de texto revisadas. **Nenhum instalador, script de alteração, teste ou CFG recuperado foi executado.** A validação verifica hashes e sintaxe por análise estática.

O compartilhamento atualizado foi consultado novamente às **14:57 e 14:58 UTC** de 19/10/2026, incluindo uma requisição com cabeçalhos de não usar cache. Embora `update_time` confirme a atualização do link às **14:55:52 UTC**, ambas as respostas mantêm exatamente os mesmos 615 nós, 89 mensagens de código e último nó de 12:56:12 UTC. **Nenhuma revisão nova foi recuperada.** Consulte [REFRESH.md](REFRESH.md) para a comparação e os hashes das novas capturas.

## Consultar o histórico

```bash
git status --short
git log --reverse --format='%h %aI %s'
git log --follow -- setup_tf2_bazzite.py
git show COMMIT:setup_tf2_bazzite.py
```

[REVISIONS.md](REVISIONS.md) lista os commits e arquivos. `.provenance/revisions.json` liga cada registro à mensagem, caminho original, SHA-256 e receita. `.provenance/source/` preserva a captura pública e os textos originais, como dados. O HTML bruto termina em `.txt` para evitar execução acidental da página. `.provenance/references.json` distingue arquivos arquivados de referências sem conteúdo disponível.

Os diretórios `/mnt/data/` da conversa foram mapeados relativamente à raiz, mantendo nomes e subpastas. Para preservar simultaneamente `TF2_HUD_UPDATE_README.md` e `TF2_HUD_Update_README.md` em um disco que pode ignorar diferenças de maiúsculas, o primeiro está em `case-variants/`, com o caminho original registrado no manifesto. O arquivo de Medic é uma alternativa opcional do guia; o candidato v1.5.0 permanece em diretório explicitamente incompleto.

O destino final foi inspecionado antes da criação. Nenhum trabalho anterior foi sobrescrito. Não há remoto configurado e nada foi publicado. `AuthorDate` registra o horário UTC da mensagem; `CommitDate` registra a importação. O conteúdo é preservado com suas inconsistências, sem correções funcionais ou alegação de compatibilidade com Bazzite.
