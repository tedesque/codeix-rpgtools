import io
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from rpgtools.app import create_app
from rpgtools.config import Settings


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "dados", public_url="http://192.168.0.10:8000")


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings))


@pytest.fixture
def imagem() -> Callable[..., bytes]:
    def _make(formato: str = "PNG", tamanho: tuple[int, int] = (64, 48)) -> bytes:
        buf = io.BytesIO()
        Image.new("RGB", tamanho, (120, 40, 200)).save(buf, formato)
        return buf.getvalue()

    return _make


@pytest.fixture
def criar_mesa(client: TestClient) -> Callable[[str], int]:
    def _make(nome: str = "Tormenta") -> int:
        resp = client.post("/mesas", data={"nome": nome}, follow_redirects=False)
        assert resp.status_code == 303
        return int(resp.headers["location"].rsplit("/", 1)[1])

    return _make


@pytest.fixture
def enviar(client: TestClient, imagem: Callable[..., bytes]) -> Callable[..., int]:
    """Envia uma imagem e devolve o id do asset criado."""

    def _make(mesa_id: int, nome_arquivo: str = "mapa.png", dados: bytes | None = None) -> int:
        dados = dados if dados is not None else imagem()
        resp = client.post(
            f"/mesas/{mesa_id}/assets",
            files=[("arquivos", (nome_arquivo, dados, "image/png"))],
            follow_redirects=False,
        )
        assert resp.status_code == 303, resp.text
        app = client.app
        repo_assets = app.state.repo.listar_assets(mesa_id)
        return repo_assets[-1].id

    return _make
