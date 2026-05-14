#!/usr/bin/env bash
# Registrazione dual-track: microfono (master) + monitor uscita audio (videoconferenza / sistema).
# Richiede: ffmpeg con supporto pulse (PipeWire fornisce il backend pulse su Debian).
#
# Variabili d'ambiente (opzionali):
#   SESSION_MIC_DEVICE       Nome sorgente Pulse per il microfono (default: default)
#   SESSION_MONITOR_DEVICE   Nome sorgente Pulse per il monitor del sink (default: <sink predefinito>.monitor)
#
# Uso dalla root del repository:
#   ./scripts/session_record.sh list
#   ./scripts/session_record.sh start
#   ./scripts/session_record.sh stop

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
AUDIO_ROOT="$REPO_ROOT/sessione/audio"
ACTIVE_FILE="$AUDIO_ROOT/.active_session"
PID_MIC="master.pid"
PID_GIO="giocatori.pid"

usage() {
  echo "Uso: $0 list | start | stop" >&2
  echo "  list  — elenca sorgenti Pulse utili (pactl) e suggerisce SESSION_MONITOR_DEVICE" >&2
  echo "  start — avvia due ffmpeg (master.wav + giocatori.wav) in una nuova cartella timestamp" >&2
  echo "  stop  — termina la registrazione avviata da start (legge $ACTIVE_FILE)" >&2
}

require_ffmpeg() {
  if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "Errore: ffmpeg non trovato nel PATH." >&2
    exit 1
  fi
}

default_monitor_device() {
  local sink
  sink="$(pactl get-default-sink 2>/dev/null || true)"
  if [[ -z "$sink" ]]; then
    echo ""
    return
  fi
  # Convenzione comune PipeWire/Pulse: la sorgente monitor ha suffisso .monitor
  echo "${sink}.monitor"
}

cmd_list() {
  echo "=== Sink di uscita predefinito (pactl) ==="
  pactl get-default-sink 2>/dev/null || echo "(pactl non disponibile)"
  echo
  echo "=== Sorgenti Pulse (nome — per -f pulse -i NOME) ==="
  if command -v pactl >/dev/null 2>&1; then
    pactl list short sources || true
  else
    echo "pactl non trovato; installa pulseaudio-utils o pipewire-pulse."
  fi
  echo
  echo "Suggerimento monitor (tutto ciò che senti in cuffia/casse):"
  local m
  m="$(default_monitor_device)"
  if [[ -n "$m" ]]; then
    echo "  export SESSION_MONITOR_DEVICE='$m'"
  else
    echo "  Imposta SESSION_MONITOR_DEVICE al nome esatto della sorgente .monitor dalla lista sopra."
  fi
  echo
  echo "Microfono (se 'default' non va bene, scegli un nome dalla colonna di pactl):"
  echo "  export SESSION_MIC_DEVICE='default'"
}

cmd_start() {
  require_ffmpeg
  mkdir -p "$AUDIO_ROOT"
  local stamp mic_dev mon_dev session_dir
  stamp="$(date +%Y%m%d_%H%M%S)"
  session_dir="$AUDIO_ROOT/$stamp"
  mkdir -p "$session_dir"

  mic_dev="${SESSION_MIC_DEVICE:-default}"
  mon_dev="${SESSION_MONITOR_DEVICE:-}"
  if [[ -z "$mon_dev" ]]; then
    mon_dev="$(default_monitor_device)"
  fi
  if [[ -z "$mon_dev" ]]; then
    echo "Errore: impossibile dedurre il monitor audio. Esegui '$0 list' e imposta SESSION_MONITOR_DEVICE." >&2
    exit 1
  fi

  echo "Cartella sessione: $session_dir"
  echo "Microfono (Pulse): $mic_dev"
  echo "Monitor uscita (Pulse): $mon_dev"

  # -thread_queue_size riduce warning di overrun su carico CPU
  ffmpeg -loglevel warning -nostats \
    -f pulse -thread_queue_size 4096 -i "$mic_dev" \
    -ac 1 -ar 48000 -c:a pcm_s16le \
    "$session_dir/master.wav" &
  echo $! >"$session_dir/$PID_MIC"

  ffmpeg -loglevel warning -nostats \
    -f pulse -thread_queue_size 4096 -i "$mon_dev" \
    -ac 1 -ar 48000 -c:a pcm_s16le \
    "$session_dir/giocatori.wav" &
  echo $! >"$session_dir/$PID_GIO"

  printf '%s\n' "$session_dir" >"$ACTIVE_FILE"
  {
    echo "SESSION_DIR=$session_dir"
    echo "SESSION_MIC_DEVICE=$mic_dev"
    echo "SESSION_MONITOR_DEVICE=$mon_dev"
    echo "STARTED=$(date -Iseconds)"
  } >"$session_dir/meta.env"

  echo "Registrazione avviata. PID microfono: $(cat "$session_dir/$PID_MIC"), PID monitor: $(cat "$session_dir/$PID_GIO")"
  echo "Per fermare: $0 stop"
}

stop_one_pidfile() {
  local f="$1"
  local name="$2"
  if [[ ! -f "$f" ]]; then
    return 0
  fi
  local pid
  pid="$(tr -d ' \n' <"$f" || true)"
  if [[ -z "$pid" ]]; then
    return 0
  fi
  if kill -0 "$pid" 2>/dev/null; then
    echo "Invio SIGINT a $name (PID $pid)..."
    kill -INT "$pid" 2>/dev/null || true
    local waited=0
    while kill -0 "$pid" 2>/dev/null && [[ $waited -lt 30 ]]; do
      sleep 1
      waited=$((waited + 1))
    done
    if kill -0 "$pid" 2>/dev/null; then
      echo "PID $pid ancora attivo: SIGKILL."
      kill -KILL "$pid" 2>/dev/null || true
    fi
  fi
}

cmd_stop() {
  if [[ ! -f "$ACTIVE_FILE" ]]; then
    echo "Nessuna registrazione attiva (manca $ACTIVE_FILE)." >&2
    exit 1
  fi
  local session_dir
  session_dir="$(tr -d '\n' <"$ACTIVE_FILE")"
  if [[ ! -d "$session_dir" ]]; then
    echo "Cartella sessione non trovata: $session_dir" >&2
    rm -f "$ACTIVE_FILE"
    exit 1
  fi
  stop_one_pidfile "$session_dir/$PID_MIC" "microfono (master)"
  stop_one_pidfile "$session_dir/$PID_GIO" "monitor (giocatori)"
  rm -f "$ACTIVE_FILE"
  echo "Registrazione terminata. File:"
  ls -la "$session_dir"/*.wav 2>/dev/null || true
  echo "Trascrizione (dalla root repo): uv run python scripts/transcribe_session_dual.py \"$session_dir\""
}

main() {
  local sub="${1:-}"
  case "$sub" in
    list) cmd_list ;;
    start) cmd_start ;;
    stop) cmd_stop ;;
    -h|--help|help) usage ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
