# La corsa al Nuovo Mondo — Campagna D&D 5e

Strumento privato del Dungeon Master per gestire la campagna *La corsa al Nuovo Mondo*: un'avventura D&D 5e ambientata in un Far West fantasy, dove pistole a revolver e magia coesistono, halfling e gnomi lavorano in catene nelle miniere di rame, e gli orchi delle Terre Selvagge difendono i loro territori dall'avanzata della Frontiera.

---

## Regole Cursor, skill e comandi

Il comportamento dell'AI è organizzato così:

| Meccanismo | Percorso | Ruolo |
|------------|----------|--------|
| **Regole** (sempre o via `globs`) | [`.cursor/rules/`](.cursor/rules/) | Due file `.mdc`: contesto permanente e formato schede PNG in modifica. |
| **Skill** (procedure lunghe) | [`.cursor/skills/`](.cursor/skills/) | Istruzioni dettagliate per resoconto, trascrizione, trascrizione VC, trascrizione Discord, ingame, master e workflow immagini; l'agente deve leggerle quando usi un comando. |
| **Comandi** | [`.cursor/commands/`](.cursor/commands/) | Prompt brevi richiamabili con `/` nella chat: avviano il flusso e rimandano allo skill corretto. |

### Regole in `.cursor/rules/`

- **`campagna`** — `alwaysApply: true`. Contesto permanente: ambientazione, paralleli storici, struttura delle cartelle, convenzioni sui nomi dei file, immagini nei Markdown, lingua (italiano).
- **`png-scheda-gioco`** — `globs` su `png/*.md` e `sessione/png-*.md`. Sezione `## Scheda di gioco` compatta per il tavolo, livello obbligatorio, aggiornamenti additivi al cambio livello; riferimento MCP `dnd` per dati ufficiali 5e.

### Comandi DM (digitare `/` nella chat)

| Comando | Skill letto | Scopo sintetico |
|---------|----------------|-----------------|
| `/resoconto` | `campagna-resoconto` | Post-sessione: resoconto a fasi; con `sessione/trascrizione.md` verificato come **fonte primaria** degli eventi quando presente; aggiornamento schede, `sessione/`, pubblicazione player-safe se configurata. |
| `/trascrizione` | `campagna-trascrizione` | Pulizia STT → `sessione/trascrizione.md`, senza inventare. |
| `/trascrizione-vc` | `campagna-trascrizione-vc` | Pulizia STT dual-track a **chunk** (~35–75 righe di segmento, target ~55): domande solo su gap non deducibili, verifica master per blocco, append in `sessione/trascrizione.md`; poi `/resoconto` usa quel file come fonte primaria. |
| `/trascrizione-discord` | `campagna-trascrizione-discord` | Pulizia grezzo Discord (`raw-merged.txt`, `[TIME] ACTOR: testo`) a **chunk** (stesse dimensioni VC); Fase 0 per ID numerici; marker `trascrizione-discord-chunk`; output in `sessione/trascrizione.md`. |
| `/ingame` | `campagna-ingame` | Tavolo: risposte brevi, solo file sotto `sessione/` con prefissi. |
| `/master` | `campagna-master` | Appunti → documenti in `ambientazione/`. |
| `/prompt-immagine` | `campagna-immagini` (solo sezione *Prompt*) | Prompt in **inglese** per il modello immagine (eccezione all’italiano della rule `campagna`); stile **cinematically realistic**; blocco `text` copiabile. Sola lettura. |
| `/importa-immagine` | `campagna-immagini` (solo sezione *Import*) | Sposta/normalizza JPEG e aggiorna il Markdown in modo **additivo** (append + path con suffisso se il canonico esiste); sostituzione solo se richiesta esplicita (richiede Agent). |

I comandi **non sostituiscono** la rule `campagna`: resta attiva in background. Per le immagini non c'è più attivazione automatica via `globs`: usa `/prompt-immagine` o `/importa-immagine` quando serve.

---

## Registrazione e trascrizione (sessione in videoconferenza, Linux)

Flusso opzionale per catturare **due tracce** allineate nel tempo: microfono del DM (`master.wav`) e **monitor dell’uscita audio** del computer (`giocatori.wav`, tipicamente ciò che senti in cuffia: inclusa la videoconferenza).

### Prerequisiti

- `ffmpeg` con input Pulse (`-f pulse`), disponibile di solito su Debian con PipeWire tramite il layer di compatibilità Pulse.
- `pactl` (pacchetto `pulseaudio-utils` o equivalente) per elencare le sorgenti e suggerire il nome del monitor.
- [`uv`](https://github.com/astral-sh/uv) e Python 3.11+ (nel repo viene usato `uv` per installare **faster-whisper**, **pyannote.audio** e **torch** CPU in `.venv/`; vedi [`pyproject.toml`](pyproject.toml) e l’indice `pytorch-cpu`).

### 1. Individuare i dispositivi (una tantum o se cambiano)

Dalla root del repository:

```bash
./tools/scripts/session_record.sh list
```

Il microfono di solito funziona con il default Pulse. Per il **monitor** (tutto ciò che va al sink di riproduzione), lo script suggerisce `export SESSION_MONITOR_DEVICE='…'` in base a `pactl get-default-sink`. Se il nome non funziona, scegliere manualmente una riga `…monitor` dall’elenco di `pactl list short sources`.

**Limite:** il monitor registra **tutto** l’audio di sistema (notifiche, altre app, musica), non solo la VC. Per isolare un’app serve routing avanzato (es. sink dedicato in PipeWire).

### 2. Registrazione durante la sessione

```bash
./tools/scripts/session_record.sh start
# … gioco in videoconferenza …
./tools/scripts/session_record.sh stop
```

I file vengono salvati in `sessione/audio/<YYYYMMDD_HHMMSS>/` (`master.wav`, `giocatori.wav`, `meta.env`).

### 3. Token Hugging Face (opzionale, consigliato)

I modelli usati da `faster-whisper` passano da Hugging Face Hub. Con **piano gratuito** conviene creare un token in [Impostazioni token](https://huggingface.co/settings/tokens) e salvarlo **solo in locale**:

1. Copia il modello di file: `cp .env.example .env`
2. Incolla il token nella riga `HF_TOKEN=...` dentro `.env` (il file `.env` è in **`.gitignore`** e non va committato).

Lo script `tools/scripts/transcribe_session_dual.py` carica automaticamente `.env` dalla root del repository prima del download, così `huggingface_hub` usa il token (rate limit più alti, modelli con gated access se applicabile).

Per la **diarizzazione** (`pyannote/speaker-diarization-community-1`): su Hugging Face apri la scheda del modello e **accetta le condizioni d’uso** (User Access Request / gated), altrimenti il download fallisce con errore 401/403. Il repo della pipeline include i sotto-modelli necessari.

### 4. Speech-to-text locale, diarizzazione per burst e merge temporale

Dalla root del repository (sostituisci la cartella con quella creata allo `stop`):

```bash
uv sync   # la prima volta, o dopo cambi dipendenze
uv run python tools/scripts/transcribe_session_dual.py sessione/audio/20250514_210530
```

Comportamento predefinito: **Whisper** su `master.wav` e `giocatori.wav`; sul canale giocatori, **diarizzazione pyannote per burst** separati da silenzi lunghi (`ffmpeg silencedetect`), poi etichette anonime nei segmenti STT.

Opzioni utili:

- `--model tiny|base|small|…`, `--device cpu|cuda` (Whisper / ctranslate2)
- `--player-offset-ms N` per spostare avanti (`N` > 0) o indietro (`N` < 0) nel tempo solo i segmenti del flusso giocatori nel merge
- `--no-diarize-giocatori` per disattivare pyannote e usare solo `[GIOCATORI]`
- `--silence-split-min-duration` (default `1.5`), `--silence-noise-db` (default `-40`), `--min-burst-duration` (default `0.4`)
- `--stt-progress-every N` (default `20`) e `--stt-progress-interval-s SEC` (default `5`): frequenza delle righe di avanzamento STT su stderr

**Torch GPU:** il `pyproject.toml` punta a wheel **CPU** (`pytorch-cpu`). Per eseguire pyannote su GPU NVIDIA serve un ambiente con PyTorch CUDA (rimuovi o adatta `[tool.uv.sources]` e reinstalla).

Output: `sessione/trascrizione-grezza-doppia.txt` (timestamp, `[MASTER]`, e sul canale giocatori `[GIOC_Bxx_Syy]` o `[GIOC_Bxx_S?]` / `[GIOCATORI]` se la diarizzazione non basta).

### 5. Pulizia con Cursor (a chunk, verifica master)

Dopo aver generato il file grezzo, in chat: **`/trascrizione-vc`** (skill `campagna-trascrizione-vc`). L’agente elabora la grezza in **blocchi ampi ma verificabili** (circa **35–75** righe di segmento per chunk, target **~55**; overlap analitico di **4** righe tra chunk consecutivi), pone **domande al DM solo** dove manca evidenza testuale, e attende **approvazione o correzione** del blocco prima di **appendere** a `sessione/trascrizione.md`. Si può **riprendere** un giro interrotto usando lo stato in `## Note di elaborazione` e i marker `<!-- trascrizione-vc-chunk:K -->`. Principio: **non inventare** contenuti. Il passo successivo è in genere **`/resoconto`**, che tratta `sessione/trascrizione.md` come **fonte primaria** degli eventi quando completo.

### 5b. Pulizia grezzo Discord (a chunk, verifica master)

Se la sessione è trascritta da un bot o export Discord in [`sessione/raw-merged.txt`](sessione/raw-merged.txt) (formato `[HH:MM:SS] ACTOR: testo`, con `ACTOR` = nickname o ID numerico snowflake), in chat: **`/trascrizione-discord`** (skill `campagna-trascrizione-discord`, che eredita chunk e fasi da `campagna-trascrizione-vc`). Prima del primo chunk l’agente chiede al DM l’attribuzione di ogni **ID numerico** (master narratore, PG, altro). Marker di ripresa: `<!-- trascrizione-discord-chunk:K -->`. Stesso output canonico `sessione/trascrizione.md` e stesso passo successivo **`/resoconto`**. Non c’è script in `tools/` per generare `raw-merged.txt`: il file va prodotto esternamente.

## Pubblicazione dei resoconti

Il repository include anche un piccolo flusso di pubblicazione player-safe descritto in `tools/pubblicazione/README.md`.

- `tools/pubblicazione/manifest.json` definisce il perimetro pubblico e la allowlist dei materiali ormai conosciuti dai giocatori (PNG, luoghi visitati, eventuali altre pagine player-safe)
- `tools/scripts/build_public_site.py` genera una sorgente Jekyll filtrata e pronta per GitHub Pages
- `tools/scripts/serve_public_site.py` rigenera la sorgente e la serve in locale tramite l'immagine Docker ufficiale di Jekyll (anteprima a `http://127.0.0.1:4000/`), utile per iterare su layout e CSS; dettagli in `tools/pubblicazione/README.md`
- `.github/workflows/publish-public-site.yml` compila e pubblica il sito con GitHub Actions

Il sito pubblico usa solo contenuti filtrati: resoconti, pagine esplicitamente allowlistate e immagini canoniche realmente referenziate. Le sezioni DM (`## Note DM`, `## Note per la prossima sessione`, `## Ganci narrativi`, `## Segreti e obiettivi nascosti`) vengono rimosse automaticamente dall'export. Le schede in `png/` hanno metadati obbligatori (**Regione**, **Ambito**, **Promemoria**) e un indice generato in `png/INDICE.md` (`tools/scripts/rebuild_png_index.py`, incluso nella build del sito). Possono essere pubblicate con profilo `public-png` (nome, metadati in testa, immagine, descrizione, eventi interessanti); l'hub `/png/` è raggruppato per regione con ricerca e filtro. I luoghi allowlistati in `ambientazione/luoghi/` vengono esportati e linkati dai resoconti nella sezione `## Luoghi visitati`.

---

## Server MCP `dnd`

Il command `/ingame` (skill `campagna-ingame`) può interrogare un server MCP locale che espone dati ufficiali di D&D 5e (mostri, incantesimi, equipaggiamento, classi, razze, ecc.) tramite l'API pubblica [dnd5eapi.co](https://www.dnd5eapi.co/). Il server è già configurato in `.cursor/mcp.json`.

La cartella `tools/dnd-mcp/` è un **git submodule**: non è inclusa direttamente in questo repository, ma punta a un commit specifico di un repository esterno. Quando si clona il progetto per la prima volta, la cartella risulta vuota finché non viene inizializzata.

### Prerequisiti

- Python 3.13+
- [`uv`](https://github.com/astral-sh/uv) installato e disponibile nel PATH (su Linux/macOS: `curl -Lsf https://astral.sh/uv/install.sh | sh`)

### Clonare il progetto con il submodule

Se si clona il repository da zero, usare il flag `--recurse-submodules` per scaricare anche `tools/dnd-mcp/` in automatico:

```bash
git clone --recurse-submodules <url-repository>
```

Se il repository è già stato clonato senza quel flag e `tools/dnd-mcp/` è vuota, inizializzare e scaricare il submodule con:

```bash
git submodule update --init --recursive
```

Per aggiornare il submodule all'ultimo commit del branch remoto in futuro:

```bash
git submodule update --remote dnd-mcp
```

### Installazione delle dipendenze

```bash
cd tools/dnd-mcp
uv pip install -r requirements.txt
```

In alternativa, con pip standard:

```bash
cd tools/dnd-mcp
pip install .
```

### Avvio manuale (opzionale)

Il server viene avviato automaticamente da Cursor quando serve. Per avviarlo manualmente a scopo di test:

```bash
cd tools/dnd-mcp
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
        "tools/dnd-mcp",
        "run",
        "dnd_mcp_server.py"
      ]
    }
  }
}
```

Se `uv` è installato in un percorso diverso, aggiornare il campo `command` di conseguenza (`which uv` per trovarlo).
