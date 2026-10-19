# TF2 Competitive Setup Linux — arquivo da conversa

Repositório Git **local** de preservação de [TF2 Competitive Setup Linux](https://chatgpt.com/share/6ad6143e-d894-83e9-a306-302b4fc65c66), recuperado em 2026-10-19T13:26:27.054350+00:00. Não é uma instalação de TF2.

Foram preservados **27 caminhos de artefatos**, com **42 registros de revisão** em **22 commits cronológicos de conteúdo** e um commit final de documentação/evidências. Os registros se dividem em **18 conteúdos literais disponíveis**, **22 reconstruções estáticas** e **2 candidatos incompletos**. Cópias com bytes idênticos são identificadas pelos mesmos hashes; registros não significam 42 versões distintas.

O instalador na raiz possui **8 estados recuperáveis**: original sem `SCRIPT_VERSION`, ajuste inicial, v1.1.0, duas revisões v1.2.0, duas variantes v1.3.0 e v1.3.1. As oito revisões representam novos commits de importação. **A fonte não permite recuperar exatamente v1.4.0 e v1.5.0**, nem o HTML anunciado como `TF2_HUD_Visual_Comparison.html`. Veja [GAPS.md](GAPS.md).

Conteúdos literais vieram de heredocs/blocos fornecidos no chat; isso não equivale a verificar os bytes de um anexo original. Reconstruções usam somente extração de literais e edições de texto revisadas. **Nenhum instalador, script de alteração, teste ou CFG recuperado foi executado.** A validação verifica hashes e sintaxe por análise estática.

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
