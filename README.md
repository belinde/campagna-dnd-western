# La corsa al Nuovo Mondo — Campagna D&D 5e

Strumento privato del Dungeon Master per gestire la campagna *La corsa al Nuovo Mondo*: un'avventura D&D 5e ambientata in un Far West fantasy, dove pistole a revolver e magia coesistono, halfling e gnomi lavorano in catene nelle miniere di rame, e gli orchi delle Terre Selvagge difendono i loro territori dall'avanzata della Frontiera.

---

## Regole Cursor

Il progetto usa **otto regole Cursor** (in `.cursor/rules/`) che modellano il comportamento dell'AI in base alla fase di lavoro. Si attivano in tre modi diversi:

- **sempre attiva** — `campagna` ha `alwaysApply: true` e viene letta in background ad ogni interazione.
- **richiamate a mano** — `master`, `ingame`, `trascrizione`, `resoconto` vanno invocate esplicitamente in chat con `@nome-regola` o nominando la modalità corrispondente.
- **auto-applicate via `globs:`** — `png-scheda-gioco`, `importa-immagine`, `immagine` si attivano automaticamente quando si lavora su file che corrispondono al loro pattern (schede PNG, asset di immagini, ecc.).

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
| 7 — Pubblicazione pubblica | Se il progetto ha un export player-safe configurato, rigenera anche i contenuti pubblici e verifica che resoconto e immagini di scena vengano sincronizzati nel sito. |

**Attivazione:** `@resoconto` nella chat, oppure "modalità resoconto".

### `png-scheda-gioco` — Scheda di gioco 5e per i PNG

Regola **auto-applicata** ai file che corrispondono ai glob `png/*.md` e `sessione/png-*.md`. Garantisce che ogni scheda PNG (canonica o temporanea di sessione) contenga una sezione `## Scheda di gioco` compatta e leggibile al tavolo, con:

- **livello obbligatorio**: se manca, l'AI chiede esplicitamente al DM "Di che livello è questo PNG?" prima di completare la sezione
- ruolo tattico, CA/PF/velocità, caratteristiche, bonus competenza, attacchi, capacità o incantesimi distintivi
- aggiornamenti **additivi e non sostitutivi** quando il livello cambia: si conserva la build già canonizzata e si aggiungono solo i benefici coerenti con il nuovo livello

Il riferimento primario per regole, classi, incantesimi e mostri è il server MCP `dnd` (vedi sotto). Se un elemento non è nell'API, l'AI lo dichiara apertamente invece di presentarlo come dato ufficiale.

### `importa-immagine` — Archiviazione e normalizzazione di un asset immagine

Regola **auto-applicata** ai file in `personaggi/`, `png/`, `ambientazione/luoghi/`, `resoconti/` e `sessione/`. Si usa quando il DM ha già un file immagine pronto e vuole inserirlo nel repository nel posto corretto, collegandolo al Markdown giusto. Il flusso:

1. determina il tipo di immagine in base al file di destinazione (ritratto PG, ritratto PNG, veduta di luogo, scena di sessione)
2. sposta l'asset nel path previsto sotto `immagini/` (`immagini/personaggi/`, `immagini/png/`, `immagini/luoghi/`, `immagini/eventi/sessione-NNN/`)
3. lo **normalizza** a JPEG `.jpg` con lato lungo ≤ 1920 px e qualità ~85 (operazione idempotente) tramite `python3 scripts/normalize_image_assets.py`
4. aggiorna il Markdown collegato con il link `/immagini/...` corretto, popolando la sezione `## Immagine` (per personaggi, PNG e luoghi) o `## Immagini salienti` (per i resoconti)

Se il file immagine effettivo, il numero di sessione o il path di destinazione sono ambigui, la regola si ferma e chiede invece di indovinare.

### `immagine` — Generazione di prompt immagine

Regola **auto-applicata** agli stessi file della precedente, ma opera in **sola lettura**: non sposta asset né modifica il repository. Quando il DM ha aperta una scheda (PG, PNG, luogo) o un resoconto e chiede un prompt per generare l'immagine, restituisce solo testo pronto da incollare in un generatore esterno, con:

- soggetto, tratti fisici, abbigliamento, equipaggiamento, ambiente, luce, atmosfera coerenti con la lore già stabilita (mai inventata)
- regole specifiche per **proporzioni di razza** (nano, halfling, gnomo, mezzorco, orco, dragonide) e per il confronto di altezza nelle scene di gruppo, così da evitare che il modello uniformi tutti a umanoidi medi
- regole dedicate all'**aspetto degli orchi delle Terre Selvagge** (cromia grigia con toni verdastri, cultura materiale fantasy-prateria) basate su `ambientazione/concetti/orchi-aspetto-e-cultura-materiale.md`

L'output include sempre il percorso suggerito sotto `immagini/` in cui l'asset dovrà vivere, in modo da agganciarsi naturalmente al flusso di `importa-immagine`.

## Pubblicazione dei resoconti

Il repository include anche un piccolo flusso di pubblicazione player-safe descritto in `pubblicazione/README.md`.

- `pubblicazione/manifest.json` definisce il perimetro pubblico e la allowlist dei materiali ormai conosciuti dai giocatori (PNG, luoghi visitati, eventuali altre pagine player-safe)
- `scripts/build_public_site.py` genera una sorgente Jekyll filtrata e pronta per GitHub Pages
- `scripts/serve_public_site.py` rigenera la sorgente e la serve in locale tramite l'immagine Docker ufficiale di Jekyll (anteprima a `http://127.0.0.1:4000/`), utile per iterare su layout e CSS; dettagli in `pubblicazione/README.md`
- `.github/workflows/publish-public-site.yml` compila e pubblica il sito con GitHub Actions

Il sito pubblico usa solo contenuti filtrati: resoconti, pagine esplicitamente allowlistate e immagini canoniche realmente referenziate. Le sezioni DM (`## Note DM`, `## Note per la prossima sessione`, `## Ganci narrativi`, `## Segreti e obiettivi nascosti`) vengono rimosse automaticamente dall'export. Le schede in `png/` possono essere pubblicate con un profilo pubblico ridotto che mostra solo nome, immagine, descrizione ed eventi interessanti, mentre i luoghi allowlistati in `ambientazione/luoghi/` vengono esportati e linkati dai resoconti nella sezione `## Luoghi visitati`.

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
