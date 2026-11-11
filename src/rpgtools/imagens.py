"""Validação de imagens enviadas e geração das versões de miniatura e de tela."""

import io
import uuid
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_BYTES = 20 * 1024 * 1024
FORMATOS = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp", "GIF": "gif"}
LADO_MINIATURA = 360
LADO_TELA = 2560

# Mapas grandes são legítimos; o limite padrão do Pillow (~89 Mpx) acusaria falso positivo.
Image.MAX_IMAGE_PIXELS = 300_000_000


class ImagemInvalida(ValueError):
    """Arquivo recusado. A mensagem é mostrada ao usuário."""


@dataclass(frozen=True)
class ImagemSalva:
    arquivo: str
    largura: int
    altura: int


def caminho_original(assets_dir: Path, arquivo: str) -> Path:
    return assets_dir / arquivo


def caminho_miniatura(assets_dir: Path, arquivo: str) -> Path:
    return assets_dir / "miniaturas" / f"{Path(arquivo).stem}.webp"


def caminho_tela(assets_dir: Path, arquivo: str) -> Path:
    """Versão reduzida para a tela remota. GIFs usam o original para não perder a animação."""
    if arquivo.endswith(".gif"):
        return caminho_original(assets_dir, arquivo)
    return assets_dir / "tela" / f"{Path(arquivo).stem}.webp"


def salvar_imagem(dados: bytes, assets_dir: Path) -> ImagemSalva:
    """Valida o conteúdo e grava original, miniatura e versão de tela."""
    if len(dados) > MAX_BYTES:
        mb = len(dados) / (1024 * 1024)
        raise ImagemInvalida(f"arquivo tem {mb:.1f} MB; o limite é 20 MB")

    try:
        with Image.open(io.BytesIO(dados)) as img:
            formato = img.format
            img.verify()
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise ImagemInvalida("não é uma imagem PNG, JPEG, WebP ou GIF válida") from exc
    if formato not in FORMATOS:
        raise ImagemInvalida(f"formato {formato} não aceito; use PNG, JPEG, WebP ou GIF")

    arquivo = f"{uuid.uuid4().hex}.{FORMATOS[formato]}"
    try:
        with Image.open(io.BytesIO(dados)) as img:
            img.load()
            img = ImageOps.exif_transpose(img)
            largura, altura = img.size
            _gravar_reduzida(img, caminho_miniatura(assets_dir, arquivo), LADO_MINIATURA)
            if formato != "GIF":
                _gravar_reduzida(img, caminho_tela(assets_dir, arquivo), LADO_TELA)
    except (OSError, SyntaxError) as exc:
        apagar_imagem(assets_dir, arquivo)
        raise ImagemInvalida("imagem corrompida ou ilegível") from exc

    caminho_original(assets_dir, arquivo).parent.mkdir(parents=True, exist_ok=True)
    caminho_original(assets_dir, arquivo).write_bytes(dados)
    return ImagemSalva(arquivo=arquivo, largura=largura, altura=altura)


def _gravar_reduzida(img: Image.Image, destino: Path, lado: int) -> None:
    copia = img.copy()
    copia.thumbnail((lado, lado))
    if copia.mode not in ("RGB", "RGBA"):
        copia = copia.convert("RGBA")
    destino.parent.mkdir(parents=True, exist_ok=True)
    copia.save(destino, "WEBP", quality=88)


def apagar_imagem(assets_dir: Path, arquivo: str) -> None:
    for caminho in (
        caminho_original(assets_dir, arquivo),
        caminho_miniatura(assets_dir, arquivo),
        caminho_tela(assets_dir, arquivo),
    ):
        caminho.unlink(missing_ok=True)
