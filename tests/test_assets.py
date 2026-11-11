import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from rpgtools import imagens


def test_envio_cria_asset_com_nome_do_arquivo(client: TestClient, criar_mesa, enviar) -> None:
    mesa = criar_mesa()

    asset_id = enviar(mesa, "mapa.png")

    painel = client.get(f"/mesas/{mesa}").text
    assert "mapa" in painel
    assert f"/mesas/{mesa}/assets/{asset_id}/miniatura" in painel
    assert client.get(f"/mesas/{mesa}/assets/{asset_id}/miniatura").status_code == 200


@pytest.mark.parametrize("formato", ["PNG", "JPEG", "WEBP", "GIF"])
def test_formatos_aceitos(client: TestClient, criar_mesa, enviar, imagem, formato) -> None:
    mesa = criar_mesa()

    enviar(mesa, f"img.{formato.lower()}", imagem(formato))

    assert len(client.app.state.repo.listar_assets(mesa)) == 1


@pytest.mark.parametrize(
    ("nome", "dados", "motivo"),
    [
        ("notas.pdf", b"%PDF-1.4 conteudo", "não é uma imagem"),
        ("falso.png", b"isto e texto, nao imagem", "não é uma imagem"),
        ("grande.png", b"\0" * (imagens.MAX_BYTES + 1), "limite é 20 MB"),
    ],
)
def test_arquivo_invalido_e_recusado(client: TestClient, criar_mesa, nome, dados, motivo) -> None:
    mesa = criar_mesa()

    resp = client.post(f"/mesas/{mesa}/assets", files=[("arquivos", (nome, dados, "image/png"))])

    assert resp.status_code == 422
    assert nome in resp.text and motivo in resp.text
    assert client.app.state.repo.listar_assets(mesa) == []


def test_formato_de_imagem_nao_aceito(client: TestClient, criar_mesa, imagem) -> None:
    mesa = criar_mesa()

    resp = client.post(
        f"/mesas/{mesa}/assets", files=[("arquivos", ("a.bmp", imagem("BMP"), "image/bmp"))]
    )

    assert resp.status_code == 422
    assert "formato BMP não aceito" in resp.text


def test_envio_multiplo_aceita_validos_e_reporta_invalidos(
    client: TestClient, criar_mesa, imagem
) -> None:
    mesa = criar_mesa()

    resp = client.post(
        f"/mesas/{mesa}/assets",
        files=[
            ("arquivos", ("a.png", imagem(), "image/png")),
            ("arquivos", ("b.pdf", b"%PDF", "application/pdf")),
            ("arquivos", ("c.jpg", imagem("JPEG"), "image/jpeg")),
        ],
    )

    assert resp.status_code == 200
    assert "b.pdf" in resp.text
    assert [a.nome for a in client.app.state.repo.listar_assets(mesa)] == ["a", "c"]


def test_nomes_repetidos_sao_permitidos(client: TestClient, criar_mesa, enviar) -> None:
    mesa = criar_mesa()

    enviar(mesa, "mapa.png")
    enviar(mesa, "mapa.png")

    assert [a.nome for a in client.app.state.repo.listar_assets(mesa)] == ["mapa", "mapa"]


def test_renomear_asset(client: TestClient, criar_mesa, enviar) -> None:
    mesa = criar_mesa()
    asset = enviar(mesa)

    client.post(f"/mesas/{mesa}/assets/{asset}/renomear", data={"nome": "Masmorra"})

    assert client.app.state.repo.obter_asset(mesa, asset).nome == "Masmorra"


def test_excluir_asset_apaga_arquivos(client: TestClient, criar_mesa, enviar, settings) -> None:
    mesa = criar_mesa()
    asset = enviar(mesa)
    arquivo = client.app.state.repo.obter_asset(mesa, asset).arquivo

    client.post(f"/mesas/{mesa}/assets/{asset}/excluir")

    assert client.app.state.repo.obter_asset(mesa, asset) is None
    assert not imagens.caminho_original(settings.assets_dir, arquivo).exists()
    assert not imagens.caminho_miniatura(settings.assets_dir, arquivo).exists()


def test_imagem_enorme_e_reduzida_para_a_tela(
    client: TestClient, criar_mesa, enviar, imagem
) -> None:
    mesa = criar_mesa()
    asset = enviar(mesa, "mundo.png", imagem("PNG", (8000, 8000)))

    resp = client.get(f"/mesas/{mesa}/assets/{asset}/tela")

    with Image.open(io.BytesIO(resp.content)) as tela:
        assert max(tela.size) == imagens.LADO_TELA
    assert client.app.state.repo.obter_asset(mesa, asset).largura == 8000
