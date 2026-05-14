#!/usr/bin/env python3
"""
Trascrive due WAV (master + giocatori) con faster-whisper, unisce i segmenti per timestamp.
Opzionale: diarizzazione per burst (silenzi lunghi) sul canale giocatori con pyannote.

Uso (dalla root del repository):
  uv run python scripts/transcribe_session_dual.py sessione/audio/20250514_210530
  uv run python scripts/transcribe_session_dual.py --master a.wav --giocatori b.wav -o out.txt
"""

from __future__ import annotations

import argparse
import contextlib
import os
import re
import subprocess
import sys
import tempfile
import time
import warnings
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    speaker: str
    text: str


@dataclass(frozen=True)
class DiarEntry:
    """Intervallo di diarizzazione in timeline globale (dopo offset giocatori)."""

    start: float
    end: float
    burst_idx: int
    spk: str  # es. S00, S01


def format_time_range(t0: float, t1: float) -> str:
    """Intervallo in secondi, compatto e senza ambiguità per merge e debug."""
    return f"{t0:.2f}s–{t1:.2f}s"


def ffprobe_duration(wav_path: Path) -> float:
    r = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(wav_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(r.stdout.strip())


def ffmpeg_silence_intervals(
    wav_path: Path,
    noise_db: float,
    min_silence_s: float,
) -> list[tuple[float, float]]:
    """Intervalli di silenzio (start, end) rilevati da ffmpeg silencedetect."""
    af = f"silencedetect=noise={noise_db}dB:d={min_silence_s}"
    r = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(wav_path),
            "-af",
            af,
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg silencedetect fallito: {r.stderr[-2000:]}")

    stderr = r.stderr
    starts: list[float] = []
    ends: list[float] = []
    for m in re.finditer(r"silence_start:\s*([\d.]+)", stderr):
        starts.append(float(m.group(1)))
    for m in re.finditer(r"silence_end:\s*([\d.]+)", stderr):
        ends.append(float(m.group(1)))

    silences: list[tuple[float, float]] = []
    if len(starts) == len(ends):
        silences = list(zip(starts, ends, strict=True))
    else:
        # allinea per eccesso/deficit (file tronco o log anomalo)
        n = min(len(starts), len(ends))
        silences = [(starts[i], ends[i]) for i in range(n)]

    silences.sort(key=lambda x: x[0])
    merged: list[tuple[float, float]] = []
    for s, e in silences:
        if s >= e:
            continue
        if not merged or s > merged[-1][1]:
            merged.append((s, e))
        else:
            ps, pe = merged[-1]
            merged[-1] = (ps, max(pe, e))
    return merged


def silences_to_speech_bursts(
    silences: list[tuple[float, float]],
    duration: float,
) -> list[tuple[float, float]]:
    """Inverte i silenzi in intervalli di attività audio (speech / suono)."""
    bursts: list[tuple[float, float]] = []
    cur = 0.0
    for s, e in silences:
        if s > cur:
            bursts.append((cur, min(s, duration)))
        cur = max(cur, e)
    if cur < duration:
        bursts.append((cur, duration))
    return [(a, b) for a, b in bursts if b - a > 1e-6]


def merge_short_bursts(
    bursts: list[tuple[float, float]],
    min_duration_s: float,
) -> list[tuple[float, float]]:
    """Unisce burst più corti di min_duration_s al vicino (preferenza al precedente)."""
    if not bursts:
        return []
    work = [[a, b] for a, b in bursts]
    changed = True
    while changed:
        changed = False
        i = 0
        while i < len(work):
            dur = work[i][1] - work[i][0]
            if dur >= min_duration_s or len(work) == 1:
                i += 1
                continue
            changed = True
            if i > 0:
                work[i - 1][1] = max(work[i - 1][1], work[i][1])
                work.pop(i)
            elif i + 1 < len(work):
                work[i][1] = max(work[i][1], work[i + 1][1])
                work.pop(i + 1)
            else:
                i += 1
    return [(float(a), float(b)) for a, b in work]


def extract_wav_segment(
    src: Path,
    t0: float,
    t1: float,
    dst: Path,
) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(src),
            "-ss",
            f"{t0:.3f}",
            "-to",
            f"{t1:.3f}",
            "-ar",
            "16000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(dst),
        ],
        check=True,
        capture_output=True,
    )


def _pipeline_output_to_annotation(diar_out) -> object:
    """
    pyannote.audio: Annotation diretto (3.x), oppure DiarizeOutput (4.x).
    Con DiarizeOutput si preferisce exclusive_speaker_diarization (allineamento STT),
    con fallback a speaker_diarization.
    """
    if hasattr(diar_out, "itertracks"):
        return diar_out
    excl = getattr(diar_out, "exclusive_speaker_diarization", None)
    if excl is not None:
        return excl
    ann = getattr(diar_out, "speaker_diarization", None)
    if ann is not None:
        return ann
    raise TypeError(
        f"Output diarizzazione non supportato: {type(diar_out).__name__!r} "
        "(atteso Annotation o DiarizeOutput)."
    )


@contextlib.contextmanager
def _suppress_numpy_edge_case_runtime_warnings() -> None:
    """
    Maschera solo RuntimeWarning noti da numpy su slice vuote / divide,
    tipici di pyannote su burst molto corti: non indicano errore di inferenza.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"^Mean of empty slice$",
            category=RuntimeWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message=r"^invalid value encountered in divide$",
            category=RuntimeWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message=r"^invalid value encountered in scalar divide$",
            category=RuntimeWarning,
        )
        yield


def _diar_burst_speaker_line(n: int) -> str:
    """Riga leggibile per stderr dopo un burst di diarizzazione."""
    if n <= 0:
        return "Trovate 0 persone (nessun cluster voce nel burst)."
    if n == 1:
        return "Trovata 1 persona."
    return f"Trovate {n} persone."


def _renumber_speakers(annotation) -> dict[str, str]:
    """Ordine di prima apparizione: SPEAKER_xx -> S00, S01, ..."""
    turns: list[tuple[float, str]] = []
    for segment, _track, label in annotation.itertracks(yield_label=True):
        turns.append((float(segment.start), str(label)))
    turns.sort(key=lambda x: x[0])
    mapping: dict[str, str] = {}
    out_idx = 0
    for _t, lab in turns:
        if lab not in mapping:
            mapping[lab] = f"S{out_idx:02d}"
            out_idx += 1
    return mapping


def diarize_burst(
    pipeline,
    giocatori_wav: Path,
    burst_idx: int,
    t0: float,
    t1: float,
) -> tuple[list[DiarEntry], int]:
    """Esegue pyannote sul segmento [t0,t1] e restituisce (DiarEntry, numero cluster speaker)."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        extract_wav_segment(giocatori_wav, t0, t1, tmp_path)
        with _suppress_numpy_edge_case_runtime_warnings():
            diarization = pipeline(
                str(tmp_path),
                min_speakers=1,
                max_speakers=8,
            )
    finally:
        tmp_path.unlink(missing_ok=True)

    with _suppress_numpy_edge_case_runtime_warnings():
        annotation = _pipeline_output_to_annotation(diarization)
        mapping = _renumber_speakers(annotation)
        entries: list[DiarEntry] = []
        for segment, _track, label in annotation.itertracks(yield_label=True):
            gs = float(segment.start) + t0
            ge = float(segment.end) + t0
            if ge <= gs:
                continue
            spk = mapping.get(str(label), "S?")
            entries.append(DiarEntry(start=gs, end=ge, burst_idx=burst_idx, spk=spk))
    entries.sort(key=lambda d: (d.start, d.end))
    return entries, len(mapping)


def load_diarization_pipeline(
    hf_token: str | None,
    torch_device: str,
):
    from pyannote.audio import Pipeline
    import torch

    if not hf_token:
        raise SystemExit(
            "Diarizzazione attiva: imposta HF_TOKEN in `.env` (vedi .env.example) e accetta le "
            "condizioni su Hugging Face per `pyannote/speaker-diarization-community-1` "
            "(include i sotto-modelli necessari)."
        )
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-community-1",
        token=hf_token,
    )
    if torch_device == "cuda" and torch.cuda.is_available():
        pipeline.to(torch.device("cuda"))
    else:
        if torch_device == "cuda" and not torch.cuda.is_available():
            print(
                "Avviso: --diarize-device cuda richiesto ma CUDA non disponibile (torch CPU?). "
                "Uso CPU per pyannote.",
                file=sys.stderr,
            )
        pipeline.to(torch.device("cpu"))
    return pipeline


def build_burst_diarization(
    giocatori_wav: Path,
    silence_noise_db: float,
    silence_min_s: float,
    min_burst_s: float,
    hf_token: str | None,
    diarize_device: str,
) -> list[DiarEntry]:
    duration = ffprobe_duration(giocatori_wav)
    silences = ffmpeg_silence_intervals(
        giocatori_wav,
        noise_db=silence_noise_db,
        min_silence_s=silence_min_s,
    )
    bursts = silences_to_speech_bursts(silences, duration)
    bursts = merge_short_bursts(bursts, min_burst_s)
    if not bursts:
        return []

    pipeline = load_diarization_pipeline(hf_token, diarize_device)
    all_entries: list[DiarEntry] = []
    total_bursts = len(bursts)
    for bi, (bs, be) in enumerate(bursts):
        print(
            f"Diarizzazione burst {bi + 1:03d}/{total_bursts:03d} ({bs:.1f}s–{be:.1f}s)...",
            file=sys.stderr,
        )
        try:
            entries, n_speakers = diarize_burst(pipeline, giocatori_wav, bi, bs, be)
        except Exception as ex:
            print(f"Avviso: diarizzazione burst {bi + 1}/{total_bursts} fallita ({ex}).", file=sys.stderr)
            continue
        print(f"  → {_diar_burst_speaker_line(n_speakers)}", file=sys.stderr)
        all_entries.extend(entries)
    all_entries.sort(key=lambda d: (d.start, d.end, d.burst_idx))
    if not all_entries:
        print(
            f"Avviso: nessun turno di diarizzazione da {total_bursts} burst "
            "(file troppo corto, errori pyannote o burst vuoti). "
            "I segmenti giocatori resteranno [GIOCATORI] dove previsto.",
            file=sys.stderr,
        )
    return all_entries


def overlap_len(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def assign_gioc_speakers(
    segments: list[Segment],
    diar_entries: list[DiarEntry],
    min_overlap_s: float,
) -> list[Segment]:
    """Assegna etichette GIOC_Bxx_Syy in base a massima sovrapposizione temporale."""
    if not diar_entries:
        return [Segment(s.start, s.end, "GIOCATORI", s.text) for s in segments]

    out: list[Segment] = []
    for seg in segments:
        ws, we = seg.start, seg.end
        burst_ov: dict[int, float] = {}
        for d in diar_entries:
            burst_ov[d.burst_idx] = burst_ov.get(d.burst_idx, 0.0) + overlap_len(
                ws, we, d.start, d.end
            )

        if not burst_ov or max(burst_ov.values()) < 1e-6:
            out.append(Segment(ws, we, "GIOCATORI", seg.text))
            continue

        best_burst = max(burst_ov.items(), key=lambda kv: kv[1])[0]
        # pareggio su overlap burst: burst con inizio più vicino a ws
        max_ovl = max(burst_ov.values())
        candidates = [b for b, o in burst_ov.items() if abs(o - max_ovl) < 1e-9]
        if len(candidates) > 1:
            burst_starts: dict[int, float] = {}
            for d in diar_entries:
                burst_starts[d.burst_idx] = min(d.start, burst_starts.get(d.burst_idx, d.start))
            best_burst = min(candidates, key=lambda b: abs(burst_starts.get(b, 0.0) - ws))

        spk_ov: dict[str, float] = {}
        for d in diar_entries:
            if d.burst_idx != best_burst:
                continue
            ovl = overlap_len(ws, we, d.start, d.end)
            if ovl <= 0:
                continue
            spk_ov[d.spk] = spk_ov.get(d.spk, 0.0) + ovl

        if not spk_ov or max(spk_ov.values()) < min_overlap_s:
            tag = f"GIOC_B{best_burst:02d}_S?"
        else:
            best_spk = max(spk_ov.items(), key=lambda kv: kv[1])[0]
            tag = f"GIOC_B{best_burst:02d}_{best_spk}"

        out.append(Segment(ws, we, tag, seg.text))
    return out


def collect_segments(
    model,
    wav_path: Path,
    speaker: str,
    time_offset_s: float,
    language: str,
    beam_size: int,
    vad_filter: bool,
    *,
    progress_every: int = 20,
    progress_min_interval_s: float = 5.0,
) -> list[Segment]:
    segments_gen, info = model.transcribe(
        str(wav_path),
        language=language,
        beam_size=beam_size,
        vad_filter=vad_filter,
    )
    total_dur = float(getattr(info, "duration", 0.0) or 0.0)
    if total_dur <= 0.0:
        total_dur = ffprobe_duration(wav_path)

    out: list[Segment] = []
    n_kept = 0
    last_print_mono = time.monotonic()
    for seg in segments_gen:
        t0 = max(0.0, seg.start + time_offset_s)
        t1 = max(t0, seg.end + time_offset_s)
        text = (seg.text or "").strip()
        if not text:
            continue
        out.append(Segment(start=t0, end=t1, speaker=speaker, text=text))
        n_kept += 1
        now = time.monotonic()
        if (
            n_kept % progress_every == 0
            or (now - last_print_mono) >= progress_min_interval_s
        ):
            last_print_mono = now
            end_in_file = float(seg.end)
            if total_dur > 1e-6:
                pct = min(100.0, 100.0 * max(0.0, end_in_file) / total_dur)
                print(
                    f"STT {speaker}  {pct:.0f}% ({end_in_file:.1f}s/{total_dur:.1f}s, {n_kept} segmenti)...",
                    file=sys.stderr,
                )
            else:
                print(
                    f"STT {speaker}  … ({n_kept} segmenti, t={end_in_file:.1f}s)...",
                    file=sys.stderr,
                )

    if total_dur > 1e-6:
        print(
            f"STT {speaker}  100% ({total_dur:.1f}s/{total_dur:.1f}s, {n_kept} segmenti).",
            file=sys.stderr,
        )
    else:
        print(f"STT {speaker}  fine ({n_kept} segmenti).", file=sys.stderr)
    return out


def merge_segments(master: list[Segment], giocatori: list[Segment]) -> list[Segment]:
    """
    Ordina per istante di inizio. A parità di start, MASTER prima; poi canale giocatori.
    """
    def sort_key(s: Segment) -> tuple:
        if s.speaker == "MASTER":
            group = 0
        elif s.speaker.startswith("GIOC"):
            group = 1
        else:
            group = 2
        return (s.start, group, s.speaker, s.end)

    combined = list(master) + list(giocatori)
    combined.sort(key=sort_key)
    return combined


def write_grezzo(path: Path, merged: list[Segment]) -> None:
    lines: list[str] = []
    lines.append(
        "# Trascrizione grezza dual-track (master + monitor uscita). "
        "Canale giocatori: etichette GIOC_Bxx_Syy = burst (silenzi lunghi) e cluster voce locale; "
        "non equivalgono ai PG. Generata automaticamente."
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
        description="STT locale dual-track (faster-whisper) + merge temporale; "
        "diarizzazione opzionale per burst sul canale giocatori (pyannote)."
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
        help="Dispositivo inferenza Whisper (default: auto)",
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
    p.add_argument(
        "--no-diarize-giocatori",
        action="store_true",
        help="Disattiva diarizzazione pyannote; tutti i segmenti giocatori come [GIOCATORI].",
    )
    p.add_argument(
        "--silence-split-min-duration",
        type=float,
        default=1.5,
        help="Durata minima (s) di silenzio per spezzare in burst (ffmpeg silencedetect d=).",
    )
    p.add_argument(
        "--silence-noise-db",
        type=float,
        default=-40.0,
        help="Soglia silenzio in dB per silencedetect (default: -40).",
    )
    p.add_argument(
        "--min-burst-duration",
        type=float,
        default=0.4,
        help="Durata minima di un burst dopo merge di segmenti troppo corti (s).",
    )
    p.add_argument(
        "--diarize-min-overlap",
        type=float,
        default=0.05,
        help="Soglia minima (s) di overlap STT–diar per assegnare uno speaker; altrimenti S?.",
    )
    p.add_argument(
        "--diarize-device",
        default="auto",
        choices=("auto", "cpu", "cuda"),
        help="Dispositivo pyannote (default: auto = cuda se disponibile, altrimenti cpu).",
    )
    p.add_argument(
        "--stt-progress-every",
        type=int,
        default=20,
        metavar="N",
        help="Stampa una riga di avanzamento STT ogni N segmenti trascritti (default: 20).",
    )
    p.add_argument(
        "--stt-progress-interval-s",
        type=float,
        default=5.0,
        metavar="SEC",
        help="Stampa comunque una riga STT se sono passati almeno SEC secondi dall'ultima (default: 5).",
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


def resolve_diarize_device(requested: str) -> str:
    if requested != "auto":
        return requested
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


def _load_dotenv_from_repo_root() -> None:
    """Carica `.env` dalla root del repo (non in git) così HF_TOKEN vale per huggingface_hub."""
    repo_root = Path(__file__).resolve().parent.parent
    env_path = repo_root / ".env"
    if not env_path.is_file():
        return
    from dotenv import load_dotenv

    load_dotenv(env_path, override=False)


def _hf_token() -> str | None:
    return os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")


def main() -> None:
    args = build_arg_parser().parse_args()
    _load_dotenv_from_repo_root()
    master_wav, gioc_wav = resolve_wavs(args)

    from faster_whisper import WhisperModel

    device = resolve_device(args.device)
    compute_type = pick_compute_type(device, args.compute_type)
    print(f"Device Whisper: {device}, compute_type: {compute_type}, modello: {args.model}", file=sys.stderr)

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
        progress_every=args.stt_progress_every,
        progress_min_interval_s=args.stt_progress_interval_s,
    )
    print("Trascrizione GIOCATORI...", file=sys.stderr)
    segs_g_raw = collect_segments(
        model,
        gioc_wav,
        "GIOCATORI",
        offset_s,
        args.language,
        args.beam_size,
        vad,
        progress_every=args.stt_progress_every,
        progress_min_interval_s=args.stt_progress_interval_s,
    )

    if args.no_diarize_giocatori:
        segs_g = segs_g_raw
    else:
        diar_dev = resolve_diarize_device(args.diarize_device)
        print(f"Diarizzazione giocatori (pyannote), device: {diar_dev}...", file=sys.stderr)
        diar_entries = build_burst_diarization(
            gioc_wav,
            silence_noise_db=args.silence_noise_db,
            silence_min_s=args.silence_split_min_duration,
            min_burst_s=args.min_burst_duration,
            hf_token=_hf_token(),
            diarize_device=diar_dev,
        )
        segs_g = assign_gioc_speakers(
            segs_g_raw,
            diar_entries,
            min_overlap_s=args.diarize_min_overlap,
        )

    merged = merge_segments(segs_m, segs_g)
    out_path = args.output
    if not out_path.is_absolute():
        out_path = (Path.cwd() / out_path).resolve()
    write_grezzo(out_path, merged)
    print(f"Scritto {out_path} ({len(merged)} segmenti).", file=sys.stderr)


if __name__ == "__main__":
    main()
