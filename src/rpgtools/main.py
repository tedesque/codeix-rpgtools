"""Ponto de entrada: `rpgtools` sobe o servidor acessível na rede local."""

import logging

import uvicorn

from rpgtools import rede
from rpgtools.app import create_app
from rpgtools.config import load_settings


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = load_settings()
    url = settings.public_url or f"http://{rede.ip_rede_local()}:{settings.port}"
    logging.info("Painel do mestre: %s  (dados em %s)", url, settings.data_dir)
    uvicorn.run(create_app(settings), host="0.0.0.0", port=settings.port)


if __name__ == "__main__":
    main()
