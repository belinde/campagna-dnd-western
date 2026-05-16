from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PageEntry:
    source_path: Path
    relative_path: Path
    route: str
    title: str
    label: str
    kind: str
    profile: str | None = None
    aliases: tuple[str, ...] = ()
    featured: bool = False


@dataclass(frozen=True)
class PreparedPage:
    entry: PageEntry
    title: str
    body: str


@dataclass
class HubCardInfo:
    """Metadati per le card delle pagine indice (export pubblico)."""

    subtitle: str = ""
    session_num: int | None = None
    episode_title: str = ""
    excerpt: str = ""
    regione: str = ""
    ambito: str = ""
    promemoria: str = ""


@dataclass(frozen=True)
class SessionNavLink:
    route: str
