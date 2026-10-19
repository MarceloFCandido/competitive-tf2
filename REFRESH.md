# Rechecagem do compartilhamento atualizado — 19/10/2026

O mesmo link foi baixado novamente às **14:57:17 UTC** e às **14:58:00 UTC**. A segunda requisição enviou `Cache-Control: no-cache` e `Pragma: no-cache`. Ambas retornaram **HTTP 200**; a segunda resposta informou `cf-cache-status: DYNAMIC`.

A atualização do compartilhamento está registrada nos metadados: `update_time` passou de **12:59:54 UTC** para **14:55:52 UTC**. O HTML bruto mudou, mas o conteúdo de mensagens retornado permaneceu igual:

- **615 nós**, com zero adições, remoções ou alterações.
- **89 mensagens de código**, todas iguais à captura original.
- Mesmo último nó, `6300a988-456c-4c43-bc20-c2eb770c75ad`, de **12:56:12 UTC**.
- Mesmas **331 URLs**, apenas em outra ordem; nenhum novo endereço.
- Mesmas **16 referências literais únicas de mensagem + anexo** no compartilhamento.
- Mensagem posterior `e4b8944c-7916-4302-8016-463828ec503e` e rótulo `1.6.0` ainda ausentes dessas respostas.

O hash canônico do mapa de mensagens é idêntico nas três capturas: `a54469380631e1e556eaaada3431768075d292dafca15bf7d0d68b09b85906df`.

## Efeito no inventário

| Item procurado | Resultado da rechecagem |
|---|---|
| Instalador v1.4.0 | Anúncio anterior continua presente; nenhum novo corpo completo ou alteração intermediária recuperada. |
| Instalador/testes v1.5.0 | Mesmos scripts de alteração e candidatos incompletos; nenhum novo byte original confirmado. |
| v1.6.0 e seus três anexos | Continuam conhecidos apenas pelo relato da leitura direta no pai; não estão na captura pública atual. |
| Testes e READMEs | Nenhuma mensagem de código ou referência nova; os registros já preservados continuam iguais. |
| `TF2_HUD_Visual_Comparison.html` | Corpo original continua indisponível; não foi inferido a partir de outro nome. |
| Galeria offline reparada | Não foi entregue como anexo, conforme esclarecimento de v1.6.0; deveria ser construída no PC. |

**Nenhuma revisão nova de artefato foi recuperada.** Permanecem 27 caminhos e 42 registros, além de 19 referências auditadas de mensagem + anexo (16 visíveis no compartilhamento, 3 da mensagem posterior relatada pelo pai). O novo commit registra somente as capturas, a comparação e a atualização de documentação.

As respostas brutas e os JSONs decodificados estão em `.provenance/source/refresh-20261019T145800Z/`; `comparison.json` contém horários, tamanhos, hashes, diferenças e cabeçalhos selecionados. A captura original e todos os commits anteriores foram preservados. Nenhum JavaScript da página, instalador, teste ou CFG recuperado foi executado. Não foi tentado acesso ao navegador e não foi presumido desbloqueio do Mac.

## Limitação remanescente

O servidor confirma a atualização dos metadados do link, mas as respostas públicas continuam expondo o mesmo recorte antigo de mensagens. A causa não pode ser determinada somente por essas respostas. Para avançar é necessário obter uma resposta compartilhada que inclua o conteúdo posterior ou recuperar os bytes dos anexos na conversa autenticada/exportação/backups. Não é possível presumir a existência de versões históricas substituídas ou expiradas.

Atualização de recuperação em 2026-10-19T17:35:13.566448+00:00: os grupos originais v1.4.0, v1.5.0 e v1.6.0 foram recebidos por upload e verificados. Os limites de acesso e de cobertura acima são históricos; não impediram essa via de transferência. As lacunas remanescentes estão em `GAPS.md`.
