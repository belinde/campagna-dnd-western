# La corsa al Nuovo Mondo — Campagna D&D 5e

Strumento privato del Dungeon Master per gestire la campagna *La corsa al Nuovo Mondo*: un'avventura D&D 5e ambientata in un Far West fantasy, dove pistole a revolver e magia coesistono, halfling e gnomi lavorano in catene nelle miniere di rame, e gli orchi delle Terre Selvagge difendono i loro territori dall'avanzata della Frontiera.

---

## Regole Cursor

Il progetto usa tre **regole Cursor contestuali** (in `.cursor/rules/`) che modellano il comportamento dell'AI in base alla fase di lavoro. Nessuna si attiva automaticamente: vanno richiamate esplicitamente nella chat.

### `campagna` — Regola base (sempre attiva)

Definisce il contesto permanente della campagna: ambientazione, paralleli storici, struttura delle cartelle, convenzioni sui nomi dei file e lingua di output (italiano). È l'unica regola con `alwaysApply: true` e viene letta in background ad ogni interazione.

### `master` — Costruzione dell'ambientazione

Si usa quando si vogliono trasformare appunti grezzi del DM in documenti di ambientazione narrativi da salvare in `ambientazione/`. Il flusso è:

1. Il DM fornisce note libere (anche telegrafiche)
2. L'AI genera subito una bozza completa nel formato corretto (luogo, fazione, evento storico, lore, ecc.)
3. L'AI elenca domande di approfondimento per affinare il documento

Prima di scrivere, l'AI legge tutti i file in `ambientazione/` (incluse le sottocartelle `luoghi/`, `nazioni/`, `concetti/`) per garantire coerenza con il canon già stabilito. Il file viene salvato nella sottocartella corretta in base al tipo: `luoghi/` per luoghi specifici, `nazioni/` per entità politiche, `concetti/` per lore e sistemi del mondo. Se gli appunti toccano eventi storici o dinamiche sociali, l'AI cerca ispirazione su Wikipedia adattando al contesto fantasy.

**Attivazione:** `@master` nella chat, oppure chiedere esplicitamente di usare la "modalità master".

### `ingame` — Generazione rapida durante la sessione

Si usa *mentre* la sessione è in corso. Il DM ha bisogno di contenuti immediati da leggere direttamente ai giocatori: PNG al volo, descrizioni di luoghi, dialoghi in prima persona, incontri casuali, liste di nomi. Le risposte sono brevi, senza meta-commenti, senza ricerche web — al più l'AI consulta il server MCP `dnd` locale.

Tutti i file generati in questa modalità vanno in `sessione/` con prefisso di tipo (`png-`, `luogo-`, `nota-`, `incontro-`). La rifinitura avviene in fase resoconto.

**Attivazione:** `@ingame` nella chat, oppure "modalità ingame".

### `trascrizione` — Pulizia di una trascrizione grezza del master

Si usa quando si dispone di un file `.txt` prodotto da uno strumento di speech-to-text durante la sessione. La trascrizione grezza contiene narrazione utile mescolata a rumore: battute OOC, artefatti STT, discussioni di regole, logistica. La regola estrae solo la narrazione e la ricostruisce come prosa.

Il flusso è:

1. L'AI legge il file `.txt` su cui è applicata la regola
2. L'AI legge tutti i file di contesto: `ambientazione/` (incluse sottocartelle), `personaggi/`, `png/`, `sessione/` (esclusa la trascrizione), `spunti/`, l'ultimo file in `resoconti/`
3. L'AI scarta tutto ciò che non è narrazione (OOC, artefatti STT, logistica, correzioni in corsa, discussioni di regole)
4. Il contenuto conservato viene riscritto in prosa narrativa in terza persona, con nomi corretti usando i file di contesto
5. I punti incomprensibili o lacunosi vengono lasciati come marcatori espliciti `[lacuna: ...]` — **nessuna interpolazione creativa**
6. Il risultato viene salvato in `sessione/trascrizione.md`

**Attivazione:** aprire il file `.txt` di trascrizione nell'editor, poi `@trascrizione` nella chat o richiedere esplicitamente "applica la modalità trascrizione".

### `resoconto` — Archiviazione post-sessione

Si usa dopo una sessione di gioco per trasformare il racconto grezzo del DM in un resoconto narrativo strutturato. Il processo è **interattivo e a fasi sequenziali** — l'AI non procede senza conferma esplicita ad ogni passaggio:

| Fase | Cosa succede |
|------|--------------|
| 1 — Raccolta | L'AI legge i file in `sessione/`, l'ultimo resoconto, le schede PG e PNG. Poi chiede data, PG presenti e racconto libero degli eventi. |
| 2 — Chiarimenti | L'AI identifica ambiguità (PNG senza scheda, luoghi nuovi, riferimenti a personaggi non chiari) e fa domande mirate. |
| 3 — Titolo e riassunto | L'AI propone 2-3 titoli evocativi e un riassunto di 3-5 righe. Attende scelta e approvazione. |
| 4 — Bozza resoconto | L'AI scrive la bozza completa seguendo il template standard. La presenta in chiaro senza salvare. Salva solo dopo approvazione. |
| 5 — Aggiornamenti collaterali | Aggiorna schede PG e PNG (sezione `## Eventi interessanti`), propone nuovi file di ambientazione, integra i file temporanei di `sessione/`. |
| 6 — Pulizia | Riepilogo di tutto ciò che è stato fatto, poi elimina i file da `sessione/` dopo conferma. |

**Attivazione:** `@resoconto` nella chat, oppure "modalità resoconto".

---

## Server MCP `dnd`

La modalità ingame può interrogare un server MCP locale che espone dati ufficiali di D&D 5e (mostri, incantesimi, equipaggiamento, classi, razze, ecc.) tramite l'API pubblica [dnd5eapi.co](https://www.dnd5eapi.co/). Il server è già configurato in `.cursor/mcp.json`.

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
