# La corsa al Nuovo Mondo — Campagna D&D 5e

Strumento privato del Dungeon Master per gestire la campagna *La corsa al Nuovo Mondo*: un'avventura D&D 5e ambientata in un Far West fantasy, dove pistole a revolver e magia coesistono, halfling e gnomi lavorano in catene nelle miniere di rame, e gli orchi delle Terre Selvagge difendono i loro territori dall'avanzata della Frontiera.

---

## Regole Cursor, skill e comandi

Il comportamento dell'AI è organizzato così:

| Meccanismo | Percorso | Ruolo |
|------------|----------|--------|
| **Regole** (sempre o via `globs`) | [`.cursor/rules/`](.cursor/rules/) | Due file `.mdc`: contesto permanente e formato schede PNG in modifica. |
| **Skill** (procedure lunghe) | [`.cursor/skills/`](.cursor/skills/) | Istruzioni dettagliate per resoconto, trascrizione, trascrizione VC, ingame, master e workflow immagini; l'agente deve leggerle quando usi un comando. |
| **Comandi** | [`.cursor/commands/`](.cursor/commands/) | Prompt brevi richiamabili con `/` nella chat: avviano il flusso e rimandano allo skill corretto. |

### Regole in `.cursor/rules/`

- **`campagna`** — `alwaysApply: true`. Contesto permanente: ambientazione, paralleli storici, struttura delle cartelle, convenzioni sui nomi dei file, immagini nei Markdown, lingua (italiano).
- **`png-scheda-gioco`** — `globs` su `png/*.md` e `sessione/png-*.md`. Sezione `## Scheda di gioco` compatta per il tavolo, livello obbligatorio, aggiornamenti additivi al cambio livello; riferimento MCP `dnd` per dati ufficiali 5e.

### Comandi DM (digitare `/` nella chat)

| Comando | Skill letto | Scopo sintetico |
|---------|----------------|-----------------|
| `/resoconto` | `campagna-resoconto` | Post-sessione: resoconto a fasi, aggiornamento schede, `sessione/`, pubblicazione player-safe se configurata. |
| `/trascrizione` | `campagna-trascrizione` | Pulizia STT → `sessione/trascrizione.md`, senza inventare. |
| `/trascrizione-vc` | `campagna-trascrizione-vc` | Pulizia STT dual-track (master + monitor VC) → `sessione/trascrizione.md`. |
| `/ingame` | `campagna-ingame` | Tavolo: risposte brevi, solo file sotto `sessione/` con prefissi. |
| `/master` | `campagna-master` | Appunti → documenti in `ambientazione/`. |
| `/prompt-immagine` | `campagna-immagini` (solo sezione *Prompt*) | Prompt in **inglese** per il modello immagine (eccezione all’italiano della rule `campagna`); stile **cinematically realistic**; blocco `text` copiabile. Sola lettura. |
| `/importa-immagine` | `campagna-immagini` (solo sezione *Import*) | Sposta/normalizza JPEG e aggiorna il Markdown (richiede Agent). |

I comandi **non sostituiscono** la rule `campagna`: resta attiva in background. Per le immagini non c'è più attivazione automatica via `globs`: usa `/prompt-immagine` o `/importa-immagine` quando serve.

---

## Registrazione e trascrizione (sessione in videoconferenza, Linux)

Flusso opzionale per catturare **due tracce** allineate nel tempo: microfono del DM (`master.wav`) e **monitor dell’uscita audio** del computer (`giocatori.wav`, tipicamente ciò che senti in cuffia: inclusa la videoconferenza).

### Prerequisiti

- `ffmpeg` con input Pulse (`-f pulse`), disponibile di solito su Debian con PipeWire tramite il layer di compatibilità Pulse.
- `pactl` (pacchetto `pulseaudio-utils` o equivalente) per elencare le sorgenti e suggerire il nome del monitor.
- [`uv`](https://github.com/astral-sh/uv) e Python 3.11+ (nel repo viene usato `uv` per installare **faster-whisper** in `.venv/`).

### 1. Individuare i dispositivi (una tantum o se cambiano)

Dalla root del repository:

```bash
./scripts/session_record.sh list
```

Il microfono di solito funziona con il default Pulse. Per il **monitor** (tutto ciò che va al sink di riproduzione), lo script suggerisce `export SESSION_MONITOR_DEVICE='…'` in base a `pactl get-default-sink`. Se il nome non funziona, scegliere manualmente una riga `…monitor` dall’elenco di `pactl list short sources`.

**Limite:** il monitor registra **tutto** l’audio di sistema (notifiche, altre app, musica), non solo la VC. Per isolare un’app serve routing avanzato (es. sink dedicato in PipeWire).

### 2. Registrazione durante la sessione

```bash
./scripts/session_record.sh start
# … gioco in videoconferenza …
./scripts/session_record.sh stop
```

I file vengono salvati in `sessione/audio/<YYYYMMDD_HHMMSS>/` (`master.wav`, `giocatori.wav`, `meta.env`).

### 3. Speech-to-text locale e merge temporale

Dalla root del repository (sostituisci la cartella con quella creata allo `stop`):

```bash
uv sync   # la prima volta, o dopo cambi dipendenze
uv run python scripts/transcribe_session_dual.py sessione/audio/20250514_210530
```

Opzioni utili: `--model tiny|base|small|…`, `--device cpu|cuda`, `--player-offset-ms N` per spostare avanti (`N` > 0) o indietro (`N` < 0) nel tempo solo i segmenti del flusso giocatori nel merge.

Output: `sessione/trascrizione-grezza-doppia.txt` (segmenti con timestamp e etichette `[MASTER]` / `[GIOCATORI]` nel senso del merge).

### 4. Pulizia con Cursor

Dopo aver generato il file grezzo, in chat: **`/trascrizione-vc`** (skill `campagna-trascrizione-vc`) per produrre `sessione/trascrizione.md` senza inventare contenuti.

## Pubblicazione dei resoconti

Il repository include anche un piccolo flusso di pubblicazione player-safe descritto in `pubblicazione/README.md`.

- `pubblicazione/manifest.json` definisce il perimetro pubblico e la allowlist dei materiali ormai conosciuti dai giocatori (PNG, luoghi visitati, eventuali altre pagine player-safe)
- `scripts/build_public_site.py` genera una sorgente Jekyll filtrata e pronta per GitHub Pages
- `scripts/serve_public_site.py` rigenera la sorgente e la serve in locale tramite l'immagine Docker ufficiale di Jekyll (anteprima a `http://127.0.0.1:4000/`), utile per iterare su layout e CSS; dettagli in `pubblicazione/README.md`
- `.github/workflows/publish-public-site.yml` compila e pubblica il sito con GitHub Actions

Il sito pubblico usa solo contenuti filtrati: resoconti, pagine esplicitamente allowlistate e immagini canoniche realmente referenziate. Le sezioni DM (`## Note DM`, `## Note per la prossima sessione`, `## Ganci narrativi`, `## Segreti e obiettivi nascosti`) vengono rimosse automaticamente dall'export. Le schede in `png/` possono essere pubblicate con un profilo pubblico ridotto che mostra solo nome, immagine, descrizione ed eventi interessanti, mentre i luoghi allowlistati in `ambientazione/luoghi/` vengono esportati e linkati dai resoconti nella sezione `## Luoghi visitati`.

---

## Server MCP `dnd`

Il command `/ingame` (skill `campagna-ingame`) può interrogare un server MCP locale che espone dati ufficiali di D&D 5e (mostri, incantesimi, equipaggiamento, classi, razze, ecc.) tramite l'API pubblica [dnd5eapi.co](https://www.dnd5eapi.co/). Il server è già configurato in `.cursor/mcp.json`.

La cartella `dnd-mcp/` è un **git submodule**: non è inclusa direttamente in questo repository, ma punta a un commit specifico di un repository esterno. Quando si clona il progetto per la prima volta, la cartella risulta vuota finché non viene inizializzata.

### Prerequisiti

- Python 3.13+
- [`uv`](https://github.com/astral-sh/uv) installato e disponibile nel PATH (su Linux/macOS: `curl -Lsf https://astral.sh/uv/install.sh | sh`)

### Clonare il progetto con il submodule

Se si clona il repository da zero, usare il flag `--recurse-submodules` per scaricare anche `dnd-mcp/` in automatico:

```bash
git clone --recurse-submodules <url-repository>
```

Se il repository è già stato clonato senza quel flag e `dnd-mcp/` è vuota, inizializzare e scaricare il submodule con:

```bash
git submodule update --init --recursive
```

Per aggiornare il submodule all'ultimo commit del branch remoto in futuro:

```bash
git submodule update --remote dnd-mcp
```

### Installazione delle dipendenze

```bash
cd dnd-mcp
uv pip install -r requirements.txt
```

In alternativa, con pip standard:

```bash
cd dnd-mcp
pip install .
```

### Avvio manuale (opzionale)

Il server viene avviato automaticamente da Cursor quando serve. Per avviarlo manualmente a scopo di test:

```bash
cd dnd-mcp
uv run python dnd_mcp_server.py
```

### Configurazione Cursor

Il file `.cursor/mcp.json` già presente nel progetto contiene la configurazione corretta:

```json
{
  "mcpServers": {
    "dnd": {
      "command": "/local/bin/uv",
      "args": [
        "--directory",
        "dnd-mcp",
        "run",
        "dnd_mcp_server.py"
      ]
    }
  }
}
```

Se `uv` è installato in un percorso diverso, aggiornare il campo `command` di conseguenza (`which uv` per trovarlo).
