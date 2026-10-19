# Acesso ao navegador e anexos originais

O **Mac foi confirmado visualmente como desbloqueado**. O Safari está acessível. A navegação para a conversa original redirecionou ao ChatGPT sem sessão autenticada; o diálogo **“Log in or sign up”** está aberto.

O bloqueio atual é **login no ChatGPT**, não a tela de bloqueio do macOS. O próximo passo é entrar na janela aberta do Safari com a mesma conta da conversa original. Não é necessário enviar senha ao assistente.

O Zen também foi inspecionado. Sua primeira leitura excedeu o tempo limite; depois a janela ficou legível, mas a navegação não foi confirmada e um clique retornou `windowNotFoundAtPosition`. Nenhum conteúdo autenticado ou anexo foi obtido por essa via.

**Nenhum anexo foi baixado nesta etapa e nenhuma revisão binária nova foi confirmada.** A identidade de versões antigas que compartilham o mesmo caminho continuará sendo verificada por evidência de conteúdo, sem suposição a partir do nome ou do rótulo do link.

Os 26 commits anteriores e os 42 registros de revisão foram preservados. Este commit acrescenta somente o estado de acesso e o bloqueio restante. Nenhum instalador, teste ou CFG recuperado foi executado. Não houve publicação remota.

A evidência textual está em `.provenance/browser-access-attempts/unlocked-authentication-required.json`. Capturas de tela, credenciais, cookies e conteúdo de outras abas não foram arquivados.

## Tentativa pelo app ChatGPT

A pedido do usuário, foi tentada a seleção do app nativo. A ferramenta recusou a operação antes de inspecionar a janela:

> Computer Use is not allowed to use the app 'com.openai.codex' for safety reasons.

Os metadados de `/Applications/ChatGPT.app/Contents/Info.plist` confirmam que o app se chama **ChatGPT**, usa o identificador **`com.openai.codex`** e está na versão **26.1013.40934**. Nos dois diretórios padrão verificados (`/Applications` e `~/Applications`), não foi encontrada outra instalação com nome ChatGPT/Codex. Foram lidos somente esses metadados; não foram extraídos credenciais, cookies, tokens ou dados internos de sessão.

**A sessão do app e sua capacidade de baixar anexos não puderam ser verificadas.** A recusa é da ferramenta de controle; ela não demonstra que o app seja incapaz de fornecer os arquivos. A operação negada não foi repetida por outro nome nem contornada por outra automação.

Nenhum anexo foi baixado pelo app. Para usar o app autenticado como fonte, o menor passo é o usuário baixar o instalador, os testes e o README atuais para `Downloads`. Os bytes recebidos poderão então ser conferidos e versionados. Links antigos com o mesmo caminho não serão tratados como versões históricas distintas sem evidência de conteúdo. O HTML e eventuais versões antigas continuam dependendo de sua disponibilidade efetiva.

Evidência: `.provenance/browser-access-attempts/native-chatgpt-app-denied.json`.

Atualização de recuperação em 2026-10-19T17:35:13.566448+00:00: os grupos originais v1.4.0, v1.5.0 e v1.6.0 foram recebidos por upload e verificados. Os limites de acesso e de cobertura acima são históricos; não impediram essa via de transferência. As lacunas remanescentes estão em `GAPS.md`.
