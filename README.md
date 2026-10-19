# TF2 Competitive Setup Linux — arquivo da conversa

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
git show 34220f09ebaae2b85b88fdc9e12a6285ca655ce5:setup_tf2_bazzite.py
```

[REVISIONS.md](REVISIONS.md) e `.provenance/revisions.json` registram commits, mensagens de origem, classificação e SHA-256. `.provenance/user-uploads/turn-1-v1.4.0/` preserva nomes recebidos, IDs Library do grupo, mensagem de envio, partes de transporte verificadas e versão declarada. Os nomes canônicos mantêm os nomes originais do chat; os sufixos dos uploads são metadados de recebimento.

As capturas públicas, incluindo duas rechecagens que retornaram os mesmos 615 nós e 89 mensagens de código, estão preservadas como dados. [REFRESH.md](REFRESH.md) explica seus limites. [BROWSER_ACCESS.md](BROWSER_ACCESS.md) registra o desbloqueio confirmado do Mac, a autenticação pendente no Safari e a recusa da ferramenta em controlar o app ChatGPT; essas tentativas não são a fonte dos arquivos recebidos.

O README `TF2_HUD_UPDATE_README.md` está em `case-variants/` para preservar a diferença de maiúsculas no macOS. O CFG opcional de Medic está em `alternatives/medic/`. Templates que dependem do estado de uma instalação TF2 não foram executados para produzir arquivos presumidos.

Nos commits iniciais de conteúdo, `AuthorDate` registra a data da mensagem da captura. Recuperações tardias por upload e commits de documentação usam a data de importação, preservando a data histórica da origem nos manifestos e sem reescrever o histórico existente. Não há remoto configurado e nada foi publicado. Este repositório é um arquivo histórico, não uma instalação ou configuração aplicada de TF2.
