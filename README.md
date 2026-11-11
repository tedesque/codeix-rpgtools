# Escudo do mestre

Notas das mesas de RPG que você narra e uma **tela remota**: você escolhe uma imagem no painel e ela aparece na TV, no projetor ou no tablet da mesa em menos de 2 segundos.

Roda na sua máquina e é usado pela rede local. Não tem login.

## Instalação

```bash
python -m venv .venv
.venv/bin/pip install -r requirements-dev.txt -e .
```

## Uso

```bash
.venv/bin/rpgtools
# INFO Painel do mestre: http://192.168.18.203:8000
```

1. Abra o endereço mostrado no terminal, crie uma mesa e envie as imagens (PNG, JPEG, WebP ou GIF, até 20 MB cada).
2. Na TV ou no tablet, abra a URL da **Tela remota** que aparece no painel da mesa, ou leia o QR code. Toque na tela para entrar em tela cheia.
3. Clique numa miniatura para exibi-la. "Limpar tela" volta a mostrar só o nome da mesa.

Se a tela remota não abrir em outro dispositivo, libere a porta no firewall (ex.: `sudo ufw allow 8000/tcp`).

## Configuração

Por variáveis de ambiente (ver `.env.example`):

| Variável | Padrão | Para quê |
|---|---|---|
| `RPG_DATA_DIR` | `~/.local/share/rpgtools` | banco SQLite e imagens enviadas |
| `RPG_PORT` | `8000` | porta do servidor (escuta em todas as interfaces) |
| `RPG_PUBLIC_URL` | detecta o IP da rede | URL base da tela remota e do QR code, se a detecção errar a interface |

## Como funciona a tela remota

A página da tela consulta o estado da mesa a cada 1 s, com JavaScript ES5 e XHR. Isso funciona em navegador de smart TV antigo e se recupera sozinho se o servidor cair. Imagens grandes são reduzidas para no máximo 2560 px antes de ir para a tela. GIFs vão originais, para manter a animação.

## Desenvolvimento

```bash
.venv/bin/pytest
.venv/bin/ruff check . && .venv/bin/ruff format .
```

Specs em `specs/`, seguindo spec-driven development (spec aprovada antes de implementar).
