from fastapi.testclient import TestClient


def test_mesa_criada_aparece_na_lista(client: TestClient, criar_mesa) -> None:
    criar_mesa("Tormenta")

    assert "Tormenta" in client.get("/").text


def test_nome_de_mesa_vazio_e_recusado(client: TestClient) -> None:
    resp = client.post("/mesas", data={"nome": "   "})

    assert resp.status_code == 422
    assert client.app.state.repo.listar_mesas() == []


def test_renomear_mesa(client: TestClient, criar_mesa) -> None:
    mesa = criar_mesa("Tormenta")

    client.post(f"/mesas/{mesa}/renomear", data={"nome": "Tormenta 20"})

    assert client.app.state.repo.obter_mesa(mesa).nome == "Tormenta 20"


def test_excluir_mesa_remove_notas_e_assets(client: TestClient, criar_mesa, enviar) -> None:
    mesa = criar_mesa()
    enviar(mesa)
    client.post(f"/mesas/{mesa}/notas", data={"titulo": "Sessão 1", "corpo": "x"})

    client.post(f"/mesas/{mesa}/excluir")

    repo = client.app.state.repo
    assert repo.obter_mesa(mesa) is None
    assert repo.listar_notas(mesa) == []
    assert repo.listar_assets(mesa) == []
    assert client.get(f"/mesas/{mesa}").status_code == 404


def test_nota_renderiza_markdown(client: TestClient, criar_mesa) -> None:
    mesa = criar_mesa()
    resp = client.post(
        f"/mesas/{mesa}/notas",
        data={"titulo": "Elenco", "corpo": "## NPCs\n\n- **Aldo**, taverneiro"},
    )

    assert "<h2>NPCs</h2>" in resp.text
    assert "<li><strong>Aldo</strong>, taverneiro</li>" in resp.text


def test_nota_nao_injeta_html_bruto(client: TestClient, criar_mesa) -> None:
    mesa = criar_mesa()
    resp = client.post(
        f"/mesas/{mesa}/notas", data={"titulo": "x", "corpo": "<script>alert(1)</script>"}
    )

    assert "<script>alert(1)</script>" not in resp.text


def test_nota_editada_vai_para_o_topo(client: TestClient, criar_mesa) -> None:
    mesa = criar_mesa()
    client.post(f"/mesas/{mesa}/notas", data={"titulo": "Antiga", "corpo": ""})
    client.post(f"/mesas/{mesa}/notas", data={"titulo": "Recente", "corpo": ""})
    repo = client.app.state.repo
    antiga = next(n for n in repo.listar_notas(mesa) if n.titulo == "Antiga")

    client.post(f"/mesas/{mesa}/notas/{antiga.id}", data={"titulo": "Antiga", "corpo": "editada"})

    assert [n.titulo for n in repo.listar_notas(mesa)] == ["Antiga", "Recente"]


def test_excluir_nota(client: TestClient, criar_mesa) -> None:
    mesa = criar_mesa()
    client.post(f"/mesas/{mesa}/notas", data={"titulo": "Rascunho", "corpo": ""})
    nota = client.app.state.repo.listar_notas(mesa)[0]

    client.post(f"/mesas/{mesa}/notas/{nota.id}/excluir")

    assert client.app.state.repo.listar_notas(mesa) == []


def test_nota_de_outra_mesa_nao_e_acessivel(client: TestClient, criar_mesa) -> None:
    a, b = criar_mesa("A"), criar_mesa("B")
    client.post(f"/mesas/{a}/notas", data={"titulo": "Segredo", "corpo": ""})
    nota = client.app.state.repo.listar_notas(a)[0]

    assert client.get(f"/mesas/{b}/notas/{nota.id}").status_code == 404
