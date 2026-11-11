"""Rotas do painel do mestre e da tela remota."""

from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markdown_it import MarkdownIt

from rpgtools import imagens, rede
from rpgtools.config import PACKAGE_DIR, Settings, load_settings
from rpgtools.repo import Asset, Mesa, Repo

_markdown = MarkdownIt("commonmark", {"html": False, "linkify": False}).enable("table")

Texto = Annotated[str, Form()]


def _nome(valor: str) -> str:
    nome = valor.strip()
    if not nome:
        raise HTTPException(status_code=422, detail="O nome não pode ficar vazio.")
    return nome[:200]


def _volta(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    repo = Repo(settings.db_path)
    assets_dir = settings.assets_dir
    templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")

    app = FastAPI(title="Escudo do mestre", docs_url=None, redoc_url=None)
    app.state.repo = repo
    app.mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static")

    def base_url() -> str:
        return settings.public_url or f"http://{rede.ip_rede_local()}:{settings.port}"

    def mesa_ou_404(mesa_id: int) -> Mesa:
        mesa = repo.obter_mesa(mesa_id)
        if mesa is None:
            raise HTTPException(status_code=404, detail="Mesa não encontrada.")
        return mesa

    def asset_ou_404(mesa_id: int, asset_id: int) -> Asset:
        asset = repo.obter_asset(mesa_id, asset_id)
        if asset is None:
            raise HTTPException(status_code=404, detail="Asset não encontrado.")
        return asset

    def render_painel(
        request: Request, mesa: Mesa, erros: list[str] | None = None, status_code: int = 200
    ) -> HTMLResponse:
        url_tela = f"{base_url()}/tela/{mesa.id}"
        return templates.TemplateResponse(
            request,
            "mesa.html",
            {
                "mesa": mesa,
                "assets": repo.listar_assets(mesa.id),
                "notas": repo.listar_notas(mesa.id),
                "url_tela": url_tela,
                "qr": rede.qr_svg(url_tela),
                "erros": erros or [],
            },
            status_code=status_code,
        )

    @app.exception_handler(HTTPException)
    async def erro_http(request: Request, exc: HTTPException) -> Response:
        if request.url.path.endswith("/estado"):
            return JSONResponse({"erro": exc.detail}, status_code=exc.status_code)
        return templates.TemplateResponse(
            request, "erro.html", {"mensagem": exc.detail}, status_code=exc.status_code
        )

    # Mesas

    @app.get("/", response_class=HTMLResponse)
    def inicio(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "inicio.html", {"mesas": repo.listar_mesas()})

    @app.post("/mesas")
    def criar_mesa(nome: Texto) -> RedirectResponse:
        mesa = repo.criar_mesa(_nome(nome))
        return _volta(f"/mesas/{mesa.id}")

    @app.get("/mesas/{mesa_id}", response_class=HTMLResponse)
    def painel(request: Request, mesa_id: int) -> HTMLResponse:
        return render_painel(request, mesa_ou_404(mesa_id))

    @app.post("/mesas/{mesa_id}/renomear")
    def renomear_mesa(mesa_id: int, nome: Texto) -> RedirectResponse:
        mesa_ou_404(mesa_id)
        repo.renomear_mesa(mesa_id, _nome(nome))
        return _volta(f"/mesas/{mesa_id}")

    @app.post("/mesas/{mesa_id}/excluir")
    def excluir_mesa(mesa_id: int) -> RedirectResponse:
        mesa_ou_404(mesa_id)
        for asset in repo.excluir_mesa(mesa_id):
            imagens.apagar_imagem(assets_dir, asset.arquivo)
        return _volta("/")

    # Notas

    @app.get("/mesas/{mesa_id}/notas/nova", response_class=HTMLResponse)
    def nova_nota(request: Request, mesa_id: int) -> HTMLResponse:
        mesa = mesa_ou_404(mesa_id)
        return templates.TemplateResponse(request, "nota_form.html", {"mesa": mesa, "nota": None})

    @app.post("/mesas/{mesa_id}/notas")
    def criar_nota(mesa_id: int, titulo: Texto, corpo: Texto = "") -> RedirectResponse:
        mesa_ou_404(mesa_id)
        nota = repo.criar_nota(mesa_id, _nome(titulo), corpo)
        return _volta(f"/mesas/{mesa_id}/notas/{nota.id}")

    @app.get("/mesas/{mesa_id}/notas/{nota_id}", response_class=HTMLResponse)
    def ver_nota(request: Request, mesa_id: int, nota_id: int) -> HTMLResponse:
        mesa = mesa_ou_404(mesa_id)
        nota = repo.obter_nota(mesa_id, nota_id)
        if nota is None:
            raise HTTPException(status_code=404, detail="Nota não encontrada.")
        return templates.TemplateResponse(
            request, "nota.html", {"mesa": mesa, "nota": nota, "html": _markdown.render(nota.corpo)}
        )

    @app.get("/mesas/{mesa_id}/notas/{nota_id}/editar", response_class=HTMLResponse)
    def editar_nota_form(request: Request, mesa_id: int, nota_id: int) -> HTMLResponse:
        mesa = mesa_ou_404(mesa_id)
        nota = repo.obter_nota(mesa_id, nota_id)
        if nota is None:
            raise HTTPException(status_code=404, detail="Nota não encontrada.")
        return templates.TemplateResponse(request, "nota_form.html", {"mesa": mesa, "nota": nota})

    @app.post("/mesas/{mesa_id}/notas/{nota_id}")
    def editar_nota(
        mesa_id: int, nota_id: int, titulo: Texto, corpo: Texto = ""
    ) -> RedirectResponse:
        if repo.obter_nota(mesa_id, nota_id) is None:
            raise HTTPException(status_code=404, detail="Nota não encontrada.")
        repo.editar_nota(nota_id, _nome(titulo), corpo)
        return _volta(f"/mesas/{mesa_id}/notas/{nota_id}")

    @app.post("/mesas/{mesa_id}/notas/{nota_id}/excluir")
    def excluir_nota(mesa_id: int, nota_id: int) -> RedirectResponse:
        if repo.obter_nota(mesa_id, nota_id) is None:
            raise HTTPException(status_code=404, detail="Nota não encontrada.")
        repo.excluir_nota(nota_id)
        return _volta(f"/mesas/{mesa_id}")

    # Assets

    @app.post("/mesas/{mesa_id}/assets", response_model=None)
    async def enviar_assets(
        request: Request, mesa_id: int, arquivos: Annotated[list[UploadFile], File()]
    ) -> Response:
        mesa = mesa_ou_404(mesa_id)
        erros: list[str] = []
        enviados = 0
        for upload in arquivos:
            nome_arquivo = upload.filename or "imagem"
            # Lê um byte além do limite: basta para saber se passou, sem carregar tudo.
            dados = await upload.read(imagens.MAX_BYTES + 1)
            try:
                salva = imagens.salvar_imagem(dados, assets_dir)
            except imagens.ImagemInvalida as exc:
                erros.append(f"{nome_arquivo}: {exc}")
                continue
            nome = Path(nome_arquivo).stem.strip() or "imagem"
            repo.criar_asset(mesa_id, nome[:200], salva.arquivo, salva.largura, salva.altura)
            enviados += 1
        if erros:
            return render_painel(request, mesa, erros, status_code=200 if enviados else 422)
        return _volta(f"/mesas/{mesa_id}#assets")

    @app.post("/mesas/{mesa_id}/assets/{asset_id}/renomear")
    def renomear_asset(mesa_id: int, asset_id: int, nome: Texto) -> RedirectResponse:
        asset_ou_404(mesa_id, asset_id)
        repo.renomear_asset(asset_id, _nome(nome))
        return _volta(f"/mesas/{mesa_id}#assets")

    @app.post("/mesas/{mesa_id}/assets/{asset_id}/excluir")
    def excluir_asset(mesa_id: int, asset_id: int) -> RedirectResponse:
        asset = asset_ou_404(mesa_id, asset_id)
        repo.excluir_asset(asset_id)
        imagens.apagar_imagem(assets_dir, asset.arquivo)
        return _volta(f"/mesas/{mesa_id}#assets")

    @app.get("/mesas/{mesa_id}/assets/{asset_id}/{versao}")
    def arquivo_asset(mesa_id: int, asset_id: int, versao: str) -> FileResponse:
        asset = asset_ou_404(mesa_id, asset_id)
        caminhos = {
            "miniatura": imagens.caminho_miniatura,
            "tela": imagens.caminho_tela,
            "original": imagens.caminho_original,
        }
        if versao not in caminhos:
            raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
        caminho = caminhos[versao](assets_dir, asset.arquivo)
        if not caminho.exists():
            raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
        # O nome do arquivo é único por upload, então o conteúdo nunca muda.
        return FileResponse(caminho, headers={"Cache-Control": "public, max-age=31536000"})

    # Tela remota

    @app.post("/mesas/{mesa_id}/assets/{asset_id}/exibir")
    def exibir(mesa_id: int, asset_id: int) -> RedirectResponse:
        asset_ou_404(mesa_id, asset_id)
        repo.exibir(mesa_id, asset_id)
        return _volta(f"/mesas/{mesa_id}#assets")

    @app.post("/mesas/{mesa_id}/limpar")
    def limpar(mesa_id: int) -> RedirectResponse:
        mesa_ou_404(mesa_id)
        repo.exibir(mesa_id, None)
        return _volta(f"/mesas/{mesa_id}#assets")

    @app.get("/tela/{mesa_id}", response_class=HTMLResponse)
    def tela(request: Request, mesa_id: int) -> HTMLResponse:
        return templates.TemplateResponse(request, "tela.html", {"mesa_id": mesa_id})

    @app.get("/tela/{mesa_id}/estado")
    def estado_tela(mesa_id: int) -> JSONResponse:
        mesa = mesa_ou_404(mesa_id)
        exibindo = None
        if mesa.exibindo_asset_id is not None:
            asset = repo.obter_asset(mesa_id, mesa.exibindo_asset_id)
            if asset is not None:
                exibindo = {
                    "id": asset.id,
                    "nome": asset.nome,
                    "url": f"/mesas/{mesa_id}/assets/{asset.id}/tela",
                }
        return JSONResponse(
            {"mesa": mesa.nome, "exibindo": exibindo}, headers={"Cache-Control": "no-store"}
        )

    return app
