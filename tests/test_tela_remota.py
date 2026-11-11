from fastapi.testclient import TestClient

from rpgtools.app import create_app


def _estado(client: TestClient, mesa: int) -> dict:
    return client.get(f"/tela/{mesa}/estado").json()


def test_tela_comeca_neutra_com_nome_da_mesa(client: TestClient, criar_mesa) -> None:
    mesa = criar_mesa("Tormenta")

    assert _estado(client, mesa) == {"mesa": "Tormenta", "exibindo": None}


def test_exibir_asset_aparece_no_estado(client: TestClient, criar_mesa, enviar) -> None:
    mesa = criar_mesa()
    asset = enviar(mesa, "mapa.png")

    client.post(f"/mesas/{mesa}/assets/{asset}/exibir")

    exibindo = _estado(client, mesa)["exibindo"]
    assert exibindo["id"] == asset and exibindo["nome"] == "mapa"
    assert client.get(exibindo["url"]).headers["content-type"].startswith("image/")


def test_exibir_outro_asset_troca_a_tela(client: TestClient, criar_mesa, enviar) -> None:
    mesa = criar_mesa()
    a, b = enviar(mesa, "a.png"), enviar(mesa, "b.png")
    client.post(f"/mesas/{mesa}/assets/{a}/exibir")

    client.post(f"/mesas/{mesa}/assets/{b}/exibir")

    assert _estado(client, mesa)["exibindo"]["id"] == b


def test_limpar_tela_volta_ao_neutro(client: TestClient, criar_mesa, enviar) -> None:
    mesa = criar_mesa("Tormenta")
    client.post(f"/mesas/{mesa}/assets/{enviar(mesa)}/exibir")

    client.post(f"/mesas/{mesa}/limpar")

    assert _estado(client, mesa) == {"mesa": "Tormenta", "exibindo": None}


def test_telas_sao_isoladas_por_mesa(client: TestClient, criar_mesa, enviar) -> None:
    a, b = criar_mesa("A"), criar_mesa("B")
    client.post(f"/mesas/{a}/assets/{enviar(a)}/exibir")

    assert _estado(client, b)["exibindo"] is None


def test_nao_exibe_asset_de_outra_mesa(client: TestClient, criar_mesa, enviar) -> None:
    a, b = criar_mesa("A"), criar_mesa("B")
    asset_de_a = enviar(a)

    resp = client.post(f"/mesas/{b}/assets/{asset_de_a}/exibir")

    assert resp.status_code == 404
    assert _estado(client, b)["exibindo"] is None


def test_exibicao_sobrevive_a_reinicio(client: TestClient, criar_mesa, enviar, settings) -> None:
    mesa = criar_mesa()
    asset = enviar(mesa)
    client.post(f"/mesas/{mesa}/assets/{asset}/exibir")

    reiniciado = TestClient(create_app(settings))

    assert _estado(reiniciado, mesa)["exibindo"]["id"] == asset


def test_excluir_asset_em_exibicao_volta_ao_neutro(client: TestClient, criar_mesa, enviar) -> None:
    mesa = criar_mesa()
    asset = enviar(mesa)
    client.post(f"/mesas/{mesa}/assets/{asset}/exibir")

    client.post(f"/mesas/{mesa}/assets/{asset}/excluir")

    assert _estado(client, mesa)["exibindo"] is None


def test_mesa_inexistente_informa_nao_encontrada(client: TestClient, criar_mesa) -> None:
    resp = client.get("/tela/999/estado")

    assert resp.status_code == 404
    assert resp.json() == {"erro": "Mesa não encontrada."}
    assert client.get("/tela/999").status_code == 200  # a página carrega e mostra o aviso


def test_estado_nao_e_cacheado(client: TestClient, criar_mesa) -> None:
    mesa = criar_mesa()

    assert client.get(f"/tela/{mesa}/estado").headers["cache-control"] == "no-store"


def test_pagina_da_tela_nao_tem_elementos_do_painel(client: TestClient, criar_mesa) -> None:
    mesa = criar_mesa()

    html = client.get(f"/tela/{mesa}").text

    assert f"/tela/{mesa}/estado" in html
    assert "<button" not in html and "<form" not in html and "painel.css" not in html


def test_painel_mostra_url_e_qr_da_tela(client: TestClient, criar_mesa) -> None:
    mesa = criar_mesa()

    html = client.get(f"/mesas/{mesa}").text

    assert f"http://192.168.0.10:8000/tela/{mesa}" in html
    assert "<svg" in html


def test_painel_destaca_asset_na_tela(client: TestClient, criar_mesa, enviar) -> None:
    mesa = criar_mesa()
    enviar(mesa, "a.png")
    b = enviar(mesa, "b.png")
    client.post(f"/mesas/{mesa}/assets/{b}/exibir")

    html = client.get(f"/mesas/{mesa}").text

    assert html.count('aria-current="true"') == 1
    destacado = html.split('aria-current="true"')[1]
    assert f"/assets/{b}/" in destacado.split("</li>")[0]
