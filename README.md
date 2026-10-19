# TF2 Competitive Setup Linux — arquivo da conversa

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
git show 618beb0913ab4670bdc0a035e4fa7fe376a99963:setup_tf2_bazzite.py
```

[REVISIONS.md](REVISIONS.md) e `.provenance/revisions.json` registram commits, mensagens, nomes originais, classificação e SHA-256. `.provenance/source-chronology.json` ordena os eventos pela data da fonte. Os commits iniciais preservam essas datas em `AuthorDate`; recuperações tardias e documentação usam a data de importação, mantendo as datas históricas nos manifestos e sem reescrever o Git.

As capturas públicas e rechecagens estão arquivadas como dados; [REFRESH.md](REFRESH.md) explica seus limites. [BROWSER_ACCESS.md](BROWSER_ACCESS.md) registra tentativas históricas de acesso. Os sete novos arquivos vieram dos uploads transferidos pelo pai, não dessas tentativas.

O README `TF2_HUD_UPDATE_README.md` permanece em `case-variants/` para preservar maiúsculas no macOS. O CFG opcional de Medic está em `alternatives/medic/`. Templates de arquivos dependentes da instalação TF2 permanecem dentro dos scripts. Não há remoto configurado e nada foi publicado.
