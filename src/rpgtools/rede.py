"""Endereço da máquina na rede local e QR code da tela remota."""

import socket

import segno


def ip_rede_local() -> str:
    """IP pelo qual outros dispositivos da rede alcançam esta máquina.

    Conectar um socket UDP não envia pacotes; só faz o sistema escolher a interface de saída.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"


def qr_svg(texto: str) -> str:
    return segno.make(texto, error="m").svg_inline(scale=5, dark="#111", light="#fff")
