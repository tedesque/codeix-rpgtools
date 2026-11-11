"""Persistência em SQLite: mesas, notas, assets e o que está na tela de cada mesa."""

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS mesas (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    exibindo_asset_id INTEGER REFERENCES assets(id) ON DELETE SET NULL,
    criada_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notas (
    id INTEGER PRIMARY KEY,
    mesa_id INTEGER NOT NULL REFERENCES mesas(id) ON DELETE CASCADE,
    titulo TEXT NOT NULL,
    corpo TEXT NOT NULL DEFAULT '',
    atualizada_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY,
    mesa_id INTEGER NOT NULL REFERENCES mesas(id) ON DELETE CASCADE,
    nome TEXT NOT NULL,
    arquivo TEXT NOT NULL,
    largura INTEGER NOT NULL,
    altura INTEGER NOT NULL,
    criado_em TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class Mesa:
    id: int
    nome: str
    exibindo_asset_id: int | None


@dataclass(frozen=True)
class Nota:
    id: int
    mesa_id: int
    titulo: str
    corpo: str
    atualizada_em: str


@dataclass(frozen=True)
class Asset:
    id: int
    mesa_id: int
    nome: str
    arquivo: str
    largura: int
    altura: int


def _agora() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds")


class Repo:
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db_path = db_path
        with self._conn() as conn:
            conn.executescript(SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _run(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        conn = self._conn()
        try:
            with conn:
                return conn.execute(sql, params)
        finally:
            conn.close()

    def _all(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        conn = self._conn()
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()

    # Mesas

    def criar_mesa(self, nome: str) -> Mesa:
        cur = self._run("INSERT INTO mesas (nome, criada_em) VALUES (?, ?)", (nome, _agora()))
        return Mesa(id=cur.lastrowid, nome=nome, exibindo_asset_id=None)

    def listar_mesas(self) -> list[Mesa]:
        rows = self._all(
            "SELECT id, nome, exibindo_asset_id FROM mesas ORDER BY nome COLLATE NOCASE"
        )
        return [Mesa(**dict(r)) for r in rows]

    def obter_mesa(self, mesa_id: int) -> Mesa | None:
        rows = self._all("SELECT id, nome, exibindo_asset_id FROM mesas WHERE id = ?", (mesa_id,))
        return Mesa(**dict(rows[0])) if rows else None

    def renomear_mesa(self, mesa_id: int, nome: str) -> None:
        self._run("UPDATE mesas SET nome = ? WHERE id = ?", (nome, mesa_id))

    def excluir_mesa(self, mesa_id: int) -> list[Asset]:
        """Exclui a mesa com notas e assets. Devolve os assets, para apagar os arquivos."""
        assets = self.listar_assets(mesa_id)
        self._run("DELETE FROM mesas WHERE id = ?", (mesa_id,))
        return assets

    def exibir(self, mesa_id: int, asset_id: int | None) -> None:
        self._run("UPDATE mesas SET exibindo_asset_id = ? WHERE id = ?", (asset_id, mesa_id))

    # Notas

    def criar_nota(self, mesa_id: int, titulo: str, corpo: str) -> Nota:
        agora = _agora()
        cur = self._run(
            "INSERT INTO notas (mesa_id, titulo, corpo, atualizada_em) VALUES (?, ?, ?, ?)",
            (mesa_id, titulo, corpo, agora),
        )
        return Nota(
            id=cur.lastrowid, mesa_id=mesa_id, titulo=titulo, corpo=corpo, atualizada_em=agora
        )

    def listar_notas(self, mesa_id: int) -> list[Nota]:
        rows = self._all(
            "SELECT * FROM notas WHERE mesa_id = ? ORDER BY atualizada_em DESC, id DESC", (mesa_id,)
        )
        return [Nota(**dict(r)) for r in rows]

    def obter_nota(self, mesa_id: int, nota_id: int) -> Nota | None:
        rows = self._all("SELECT * FROM notas WHERE id = ? AND mesa_id = ?", (nota_id, mesa_id))
        return Nota(**dict(rows[0])) if rows else None

    def editar_nota(self, nota_id: int, titulo: str, corpo: str) -> None:
        self._run(
            "UPDATE notas SET titulo = ?, corpo = ?, atualizada_em = ? WHERE id = ?",
            (titulo, corpo, _agora(), nota_id),
        )

    def excluir_nota(self, nota_id: int) -> None:
        self._run("DELETE FROM notas WHERE id = ?", (nota_id,))

    # Assets

    def criar_asset(
        self, mesa_id: int, nome: str, arquivo: str, largura: int, altura: int
    ) -> Asset:
        cur = self._run(
            "INSERT INTO assets (mesa_id, nome, arquivo, largura, altura, criado_em)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (mesa_id, nome, arquivo, largura, altura, _agora()),
        )
        return Asset(cur.lastrowid, mesa_id, nome, arquivo, largura, altura)

    def listar_assets(self, mesa_id: int) -> list[Asset]:
        rows = self._all(
            "SELECT id, mesa_id, nome, arquivo, largura, altura FROM assets"
            " WHERE mesa_id = ? ORDER BY id",
            (mesa_id,),
        )
        return [Asset(**dict(r)) for r in rows]

    def obter_asset(self, mesa_id: int, asset_id: int) -> Asset | None:
        rows = self._all(
            "SELECT id, mesa_id, nome, arquivo, largura, altura FROM assets"
            " WHERE id = ? AND mesa_id = ?",
            (asset_id, mesa_id),
        )
        return Asset(**dict(rows[0])) if rows else None

    def renomear_asset(self, asset_id: int, nome: str) -> None:
        self._run("UPDATE assets SET nome = ? WHERE id = ?", (nome, asset_id))

    def excluir_asset(self, asset_id: int) -> None:
        self._run("DELETE FROM assets WHERE id = ?", (asset_id,))
