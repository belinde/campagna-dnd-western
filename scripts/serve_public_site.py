#!/usr/bin/env python3
"""Anteprima locale del sito pubblico: build + serve via Docker/Jekyll."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
BUILD_SCRIPT = REPO_ROOT / "scripts" / "build_public_site.py"
DEFAULT_SOURCE = REPO_ROOT / "build" / "public-site"
DEFAULT_IMAGE = "jekyll/jekyll:4"
DEFAULT_PORT = 4000
DEFAULT_BIND = "127.0.0.1"
DEFAULT_NETWORK = "host"
CONTAINER_NAME = "campagna-public-site"
CONTAINER_PORT = 4000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rigenera la sorgente Jekyll del sito pubblico e la serve in locale "
            "tramite l'immagine Docker jekyll/jekyll."
        )
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Non rigenerare la sorgente: usa quella gia` presente in build/public-site.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Porta locale a cui esporre l'anteprima (default: {DEFAULT_PORT}).",
    )
    parser.add_argument(
        "--bind",
        default=DEFAULT_BIND,
        help=(
            "Indirizzo locale a cui legare la porta "
            f"(default: {DEFAULT_BIND}; usare 0.0.0.0 per esporre alla LAN)."
        ),
    )
    parser.add_argument(
        "--image",
        default=DEFAULT_IMAGE,
        help=f"Immagine Docker da usare (default: {DEFAULT_IMAGE}).",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Cartella sorgente Jekyll (default: build/public-site).",
    )
    parser.add_argument(
        "--network",
        default=DEFAULT_NETWORK,
        help=(
            "Modalita` rete del container Docker "
            f"(default: {DEFAULT_NETWORK}; usare 'bridge' per port mapping classico, "
            "richiede che il container possa risolvere rubygems.org)."
        ),
    )
    return parser.parse_args()


def run_build() -> None:
    print("Rigenero la sorgente Jekyll...", flush=True)
    subprocess.run(
        [sys.executable, str(BUILD_SCRIPT)],
        check=True,
        cwd=REPO_ROOT,
    )


def docker_available() -> bool:
    return shutil.which("docker") is not None


def serve(source: Path, image: str, bind: str, port: int, network: str) -> int:
    if not docker_available():
        print(
            "ERRORE: docker non trovato sul PATH. Installa Docker per usare l'anteprima locale.",
            file=sys.stderr,
        )
        return 1

    source = source.resolve()
    if not source.is_dir():
        print(
            f"ERRORE: sorgente Jekyll non trovata: {source}. "
            "Lancia prima la build (oppure rimuovi --skip-build).",
            file=sys.stderr,
        )
        return 1

    use_host_network = network == "host"
    # Con --network=host il container condivide lo stack di rete dell'host:
    # nessun port mapping serve e Jekyll puo` legarsi direttamente al bind richiesto.
    # Inoltre il DNS del container coincide con quello dell'host: utile in reti
    # aziendali dove la rete bridge di Docker non riesce a raggiungere rubygems.org.
    jekyll_host = bind if use_host_network else "0.0.0.0"
    jekyll_port = port if use_host_network else CONTAINER_PORT

    # Ruby 3.0+ non include piu` webrick nella stdlib; Jekyll serve lo richiede ancora.
    inner = (
        f"gem install webrick -N && "
        f"jekyll serve --no-watch --host {jekyll_host} --port {jekyll_port}"
    )
    cmd = [
        "docker",
        "run",
        "--rm",
        "-it",
        "--name",
        CONTAINER_NAME,
        "-v",
        f"{source}:/srv/jekyll",
    ]
    if use_host_network:
        cmd.extend(["--network", "host"])
    else:
        cmd.extend(["--network", network, "-p", f"{bind}:{port}:{CONTAINER_PORT}"])
    cmd.extend([image, "sh", "-c", inner])

    print("Installo la gem webrick nel container (necessaria con Ruby 3.x)...", flush=True)
    print(f"Anteprima disponibile su http://{bind}:{port}/", flush=True)
    print("Premi Ctrl+C per fermare il container.", flush=True)
    try:
        return subprocess.call(cmd)
    except KeyboardInterrupt:
        return 130


def main() -> None:
    args = parse_args()
    if not args.skip_build:
        try:
            run_build()
        except subprocess.CalledProcessError as exc:
            print(
                f"ERRORE: la build della sorgente Jekyll e` fallita (exit {exc.returncode}).",
                file=sys.stderr,
            )
            sys.exit(exc.returncode)

    sys.exit(serve(args.source, args.image, args.bind, args.port, args.network))


if __name__ == "__main__":
    main()
