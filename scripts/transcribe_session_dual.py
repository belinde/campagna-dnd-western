#!/usr/bin/env python3
"""
Trascrive due WAV (master + giocatori) con faster-whisper, unisce i segmenti per timestamp.

Uso (dalla root del repository):
  uv run python scripts/transcribe_session_dual.py sessione/audio/20250514_210530
  uv run python scripts/transcribe_session_dual.py --master a.wav --giocatori b.wav -o out.txt
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    speaker: str
    text: str


def format_time_range(t0: float, t1: float) -> str:
    """Intervallo in secondi, compatto e senza ambiguità per merge e debug."""
    return f"{t0:.2f}s–{t1:.2f}s"


def collect_segments(
    model,
    wav_path: Path,
    speaker: str,
    time_offset_s: float,
    language: str,
    beam_size: int,
    vad_filter: bool,
) -> list[Segment]:
    segments_gen, _info = model.transcribe(
        str(wav_path),
        language=language,
        beam_size=beam_size,
        vad_filter=vad_filter,
    )
    out: list[Segment] = []
    for seg in segments_gen:
        t0 = max(0.0, seg.start + time_offset_s)
        t1 = max(t0, seg.end + time_offset_s)
        text = (seg.text or "").strip()
        if not text:
            continue
        out.append(Segment(start=t0, end=t1, speaker=speaker, text=text))
    return out


def merge_segments(
    master: list[Segment],
    giocatori: list[Segment],
) -> list[Segment]:
    """
    Ordina per istante di inizio. A parità di start, MASTER prima (ordine lessicografico stabile).
    Sovrapposizioni: non fonde; mantiene tutti i segmenti come prodotti dallo STT.
    """
    order = {"MASTER": 0, "GIOCATORI": 1}
    combined = list(master) + list(giocatori)
    combined.sort(key=lambda s: (s.start, order.get(s.speaker, 9), s.end))
    return combined


def write_grezzo(path: Path, merged: list[Segment]) -> None:
    lines: list[str] = []
    lines.append(
        "# Trascrizione grezza dual-track (master + monitor uscita). "
        "Generata automaticamente; ogni riga è ricavabile dallo STT senza interpretazione."
    )
    lines.append("")
    for seg in merged:
        tag = f"[{seg.speaker}]"
        ts = format_time_range(seg.start, seg.end)
        lines.append(f"{ts} {tag} {seg.text}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def pick_compute_type(device: str, requested: str | None) -> str:
    if requested:
        return requested
    if device == "cuda":
        return "float16"
    return "int8"


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="STT locale dual-track (faster-whisper) + merge temporale."
    )
    p.add_argument(
        "session_dir",
        nargs="?",
        type=Path,
        help="Cartella con master.wav e giocatori.wav (output di session_record.sh start)",
    )
    p.add_argument("--master", type=Path, help="Percorso WAV microfono (override)")
    p.add_argument("--giocatori", type=Path, help="Percorso WAV monitor (override)")
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("sessione/trascrizione-grezza-doppia.txt"),
        help="File testo unificato (default: sessione/trascrizione-grezza-doppia.txt)",
    )
    p.add_argument(
        "--model",
        default="small",
        help="Nome modello Whisper (default: small)",
    )
    p.add_argument(
        "--device",
        default="auto",
        choices=("auto", "cpu", "cuda"),
        help="Dispositivo inferenza (default: auto)",
    )
    p.add_argument(
        "--compute-type",
        default=None,
        help="Override compute type ctranslate2 (es. int8, float16). Default in base al device.",
    )
    p.add_argument("--language", default="it", help="Lingua ISO (default: it)")
    p.add_argument(
        "--player-offset-ms",
        type=float,
        default=0.0,
        help="Offset in ms applicato solo al flusso giocatori (positivo = segmenti più tardi nel merge)",
    )
    p.add_argument("--beam-size", type=int, default=5)
    p.add_argument(
        "--no-vad-filter",
        action="store_true",
        help="Disattiva il filtro VAD interno di faster-whisper",
    )
    return p


def resolve_wavs(args: argparse.Namespace) -> tuple[Path, Path]:
    if args.master and args.giocatori:
        return args.master.resolve(), args.giocatori.resolve()
    if args.session_dir:
        d = args.session_dir.resolve()
        m = d / "master.wav"
        g = d / "giocatori.wav"
        if not m.is_file() or not g.is_file():
            raise SystemExit(
                f"Attesi file {m.name} e {g.name} in {d}. "
                "Usa --master e --giocatori oppure una cartella valida."
            )
        return m, g
    raise SystemExit(
        "Specifica session_dir (cartella con i due WAV) oppure --master e --giocatori."
    )


def resolve_device(requested: str) -> str:
    if requested != "auto":
        return requested
    try:
        import ctranslate2  # type: ignore

        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda"
    except Exception:
        pass
    return "cpu"


def main() -> None:
    args = build_arg_parser().parse_args()
    master_wav, gioc_wav = resolve_wavs(args)

    from faster_whisper import WhisperModel

    device = resolve_device(args.device)
    compute_type = pick_compute_type(device, args.compute_type)
    print(f"Device: {device}, compute_type: {compute_type}, modello: {args.model}", file=sys.stderr)

    model = WhisperModel(args.model, device=device, compute_type=compute_type)
    offset_s = args.player_offset_ms / 1000.0
    vad = not args.no_vad_filter

    print("Trascrizione MASTER...", file=sys.stderr)
    segs_m = collect_segments(
        model,
        master_wav,
        "MASTER",
        0.0,
        args.language,
        args.beam_size,
        vad,
    )
    print("Trascrizione GIOCATORI...", file=sys.stderr)
    segs_g = collect_segments(
        model,
        gioc_wav,
        "GIOCATORI",
        offset_s,
        args.language,
        args.beam_size,
        vad,
    )

    merged = merge_segments(segs_m, segs_g)
    out_path = args.output
    if not out_path.is_absolute():
        out_path = (Path.cwd() / out_path).resolve()
    write_grezzo(out_path, merged)
    print(f"Scritto {out_path} ({len(merged)} segmenti).", file=sys.stderr)


if __name__ == "__main__":
    main()
