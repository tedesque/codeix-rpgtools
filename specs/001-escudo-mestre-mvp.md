# Spec: Escudo do mestre (MVP): mesas, notas e tela remota

**Número:** 001
**Status:** Implementada
**Data:** 2026-11-11

## 1. Contexto

O mestre precisa de um lugar só para as anotações das mesas que narra e para mostrar material aos jogadores durante a sessão. Hoje, para mostrar uma imagem (um mapa, um NPC, uma cena), ele precisa virar o notebook ou mandar arquivo no grupo. A ideia é o mestre escolher o asset no seu painel e ele aparecer na hora numa tela remota (TV, projetor ou tablet) aberta na mesa, como no Setlist.

## 2. Suposições

- Um único usuário (o mestre). Não há contas, login nem permissões no MVP.
- O app roda numa máquina da rede local (notebook do mestre ou servidor de casa). A tela remota é qualquer navegador na mesma rede que abre uma URL.
- Por estar em rede local confiável, a tela remota não exige autenticação. O painel do mestre também não, no MVP.
- Uma **mesa** é uma campanha ou grupo que o mestre narra (ex.: "Tormenta – quinta à noite"). Cada mesa tem as próprias notas, os próprios assets e a própria tela remota.
- No MVP, "asset" é uma imagem: PNG, JPEG, WebP ou GIF, com até 20 MB.
- Pode haver mais de um navegador abrindo a mesma tela remota ao mesmo tempo (TV e tablet, por exemplo), e todos mostram a mesma coisa.
- As notas são texto em Markdown, mostrado formatado no painel.
- A stack é Python (escolha do usuário). Os detalhes vão no plano técnico.

## 3. Requisitos funcionais

**Mesas**
- RF01: O sistema deve permitir criar, renomear e excluir uma mesa.
- RF02: O sistema deve listar as mesas existentes na página inicial do painel.

**Notas**
- RF03: O sistema deve permitir criar, editar e excluir notas dentro de uma mesa, cada uma com título e corpo em Markdown.
- RF04: O sistema deve mostrar o corpo da nota formatado (títulos, listas, negrito, links) quando ela é aberta para leitura.
- RF05: O sistema deve listar as notas de uma mesa, da editada mais recentemente para a mais antiga.

**Assets**
- RF06: O sistema deve permitir enviar uma ou mais imagens para uma mesa, cada uma com um nome (o padrão é o nome do arquivo).
- RF07: O sistema deve recusar arquivos que não sejam PNG, JPEG, WebP ou GIF, ou que passem de 20 MB, e informar o motivo.
- RF08: O sistema deve mostrar os assets da mesa numa grade de miniaturas, com o nome de cada um.
- RF09: O sistema deve permitir renomear e excluir um asset.

**Tela remota**
- RF10: Cada mesa deve ter uma URL de tela remota que pode ser aberta em outro dispositivo da rede local.
- RF11: O painel da mesa deve mostrar a URL da tela remota e um QR code dela, para abrir no tablet ou celular sem digitar.
- RF12: Quando o mestre escolhe "Exibir" num asset, a tela remota deve passar a mostrar essa imagem em até 2 segundos, sem ninguém tocar no dispositivo remoto.
- RF13: A tela remota deve mostrar a imagem centralizada, sem cortes e o maior possível, num fundo escuro, sem botões nem elementos do painel.
- RF14: O mestre deve poder "Limpar tela". A tela remota volta então para um estado neutro (fundo escuro com o nome da mesa), em até 2 segundos.
- RF15: O painel deve indicar qual asset está sendo exibido na tela remota naquele momento.
- RF16: Uma tela remota aberta ou recarregada depois que algo já foi exibido deve mostrar o que está sendo exibido agora, e não o estado neutro.
- RF17: A tela remota deve oferecer um modo tela cheia, ativado por um toque ou clique nela.
- RF18: Se a conexão com o servidor cair, a tela remota deve continuar mostrando a última imagem e voltar a se atualizar sozinha quando a conexão voltar.
- RF19: O que está sendo exibido deve sobreviver a um reinício do servidor.

## 4. Fora de escopo

- Login, contas de usuário e vários mestres.
- Acesso pela internet, hospedagem e jogadores remotos.
- Assets que não sejam imagem (áudio, vídeo, PDF, texto para os jogadores).
- Ferramentas sobre a imagem: zoom remoto, névoa de guerra, desenho, marcadores, revelar parte do mapa.
- Fichas de personagem, rolagem de dados, iniciativa, tabelas e outras ferramentas de escudo. Ficam para specs futuras.
- Organizar assets em pastas ou com tags, e buscar notas ou assets.
- Fila ou "setlist" de assets pré-ordenados para a sessão.
- Exportar e importar mesas.

## 5. Critérios de aceite

- [ ] Dado o painel vazio, quando crio a mesa "Tormenta", então ela aparece na lista de mesas.
- [ ] Dada uma mesa, quando crio uma nota com `## NPCs` e `- **Aldo**, taverneiro`, então, ao abri-la, vejo um título e um item de lista com "Aldo" em negrito.
- [ ] Dadas duas notas, quando edito a mais antiga, então ela passa a ser a primeira da lista.
- [ ] Dada uma mesa, quando envio `mapa.png` (2 MB), então aparece uma miniatura com o nome "mapa".
- [ ] Dada uma mesa, quando envio `notas.pdf` ou uma imagem de 25 MB, então o envio é recusado com mensagem dizendo o motivo e nenhum asset é criado.
- [ ] Dada uma tela remota aberta em outro dispositivo da rede, quando clico "Exibir" em "mapa", então a imagem aparece nela em até 2 segundos, inteira e centralizada.
- [ ] Dada uma imagem em exibição, quando clico "Exibir" em outro asset, então a tela remota troca para o novo em até 2 segundos.
- [ ] Dada uma imagem em exibição, quando clico "Limpar tela", então a tela remota mostra só o nome da mesa em fundo escuro em até 2 segundos.
- [ ] Dadas duas telas remotas abertas da mesma mesa, quando exibo um asset, então as duas mostram a mesma imagem.
- [ ] Dada uma imagem em exibição, quando abro a URL da tela remota num dispositivo novo, então ela já abre mostrando essa imagem.
- [ ] Dada uma imagem em exibição na mesa A, quando abro a tela remota da mesa B, então ela não mostra a imagem da mesa A.
- [ ] Dada uma imagem em exibição, quando o servidor reinicia, então a tela remota volta a mostrar a mesma imagem sem eu fazer nada no painel.
- [ ] Dado o painel da mesa, então vejo a URL da tela remota e um QR code que, lido no celular, abre essa URL.
- [ ] Dada a tela remota, quando toco nela, então ela entra em tela cheia.
- [ ] Dado o painel da mesa com algo em exibição, então o asset exibido aparece destacado como "na tela".

## 6. Casos de borda / erros

- Excluir o asset que está em exibição: a tela remota volta para o estado neutro.
- Excluir uma mesa: as notas e os assets dela também são excluídos, e a tela remota dela passa a mostrar "Mesa não encontrada". O painel pede confirmação antes.
- Abrir a URL de tela remota de uma mesa que não existe: mostra "Mesa não encontrada", sem erro técnico.
- Arquivo com extensão de imagem mas conteúdo inválido (ex.: `.png` que é texto): é recusado como formato inválido.
- Dois assets com o mesmo nome na mesma mesa: é permitido. O nome não precisa ser único.
- Imagens muito grandes em pixels (ex.: mapa 8000×8000): a tela remota mostra a imagem inteira reduzida, sem travar o navegador da TV.
- Servidor fora do ar quando a tela remota é aberta: mostra um aviso discreto de "reconectando…" e tenta de novo sozinha.

## 7. Dependências e riscos

- A máquina do mestre precisa estar acessível na rede local (firewall liberado na porta do app). O painel deve mostrar uma URL com o IP da rede, não `localhost`, senão o QR code não funciona em outro dispositivo.
- Navegadores de smart TV podem ser antigos e não suportar alguns recursos (tela cheia, conexões em tempo real). Risco: RF12 e RF17 falharem em TVs antigas. Mitigação a definir no plano: alternativa de atualização compatível e teste num navegador de TV real.
- Os arquivos enviados ocupam disco local. Não há limite total no MVP.

---
*Esta spec não deve conter decisões de implementação (nomes de classes, queries, arquitetura). Isso vai no plano técnico, etapa 3 do fluxo.*
