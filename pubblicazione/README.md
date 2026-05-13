# Pubblicazione player-safe

Questa cartella definisce il perimetro del sito pubblico generato dal repository privato della campagna.

## Cosa viene pubblicato in v1

- tutte le schede in `personaggi/` (collection nel manifest), **intere** dopo la sanificazione: restano aspetto, background, equipaggiamento, eventi in sessione, ecc.; spariscono solo le sezioni private elencate sotto `stripSections` (in pratica soprattutto `## Note DM` sulle schede PG)
- tutti i file in `resoconti/`
- `ambientazione/ambientazione-giocatori.md`
- i materiali inseriti esplicitamente nella allowlist di `manifest.json`
- le schede dei `png/` gia` noti ai giocatori, ma in **profilo pubblico ridotto** (non equivalente alle schede PG: vedi sotto)
- i luoghi di `ambientazione/luoghi/` che sono gia` stati visitati o comunque rivelati ai giocatori e sono entrati in allowlist
- solo le immagini realmente referenziate dalle pagine pubbliche, incluse le scene in `immagini/eventi/`

## Navigazione nell'export

Lo script genera una **sidebar** con le sezioni Personaggi, Resoconti, PNG e Luoghi; la **home** (`/`) si raggiunge dal **logo** in intestazione. Le pagine indice `/personaggi/`, `/resoconti/`, `/png/` e `/luoghi/` mostrano **griglie di card** (thumbnail a bassa risoluzione, titolo, metadati brevi). Per i PG le card usano **Razza** e **Classe** dai campi in testa alla scheda; per i PNG il campo **Ruolo**; per i luoghi **Regione** e **Tipo**. Per i resoconti: badge «Sessione N», titolo dell'episodio (parte dopo `—` nel titolo), excerpt tratto da `## Riassunto` e thumbnail dalla prima immagine della pagina. La **pagina singola** di una sessione (`resoconti/sessione-NNN.md` esportato) **non include più** la sezione `## Riassunto` (resta nel repository privato e nell'indice come anteprima). La **home** (`/`) mostra solo le pagine che non rientrano nelle categorie a sidebar. Il link «Guida giocatori» non compare nell'header accanto al logo: resta nelle liste della home o tra i contenuti player-safe dell'archivio.

### Immagini nell'export

Per ogni immagine referenziata nelle pagine pubbliche, lo script:

1. **copia** nell'output l'asset cosi` com'e` nel repository (formato canonico: JPEG `.jpg`, lato lungo gia` limitato a 1920 px in fase di import/normalizzazione);
2. genera una **miniatura** in `immagini/thumbs/` (stessa gerarchia relativa, JPEG, max ~320px sul lato lungo) usata dalle card degli indici.

### Asset statici del sito (`pubblicazione/assets/`)

File in **`pubblicazione/assets/`** (es. `header.png` con trasparenza per l'intestazione) vengono copiati in **`assets/`** nell'output Jekyll **senza** passare dalla generazione di thumbnail e **senza** alcuna conversione: vanno usati per grafica UI del sito che deve restare in PNG o altro formato non toccato dalla pipeline di `immagini/`.

Serve **Pillow** (`scripts/requirements-public-site.txt`); se manca in locale, la build stampa un avviso: le immagini a piena risoluzione vengono comunque copiate, ma **nessuna thumbnail** viene generata e le card useranno un segnaposto.

## Cosa non viene mai pubblicato direttamente

Il sito non usa i file grezzi del repository cosi` come sono. Ogni pagina passa da una fase di sanificazione che rimuove automaticamente le sezioni private elencate in `manifest.json`, in particolare:

- `## Note DM`
- `## Note per la prossima sessione`
- `## Ganci narrativi`
- `## Segreti e obiettivi nascosti`

Le cartelle `sessione/`, `spunti/`, `.cursor/` e `dnd-mcp/` restano fuori dal perimetro pubblico.

## Manifest

Il file `manifest.json` definisce:

- i metadati del sito pubblico
- le pagine pubbliche esplicite
- la allowlist dei materiali ormai conosciuti dai giocatori
- le collection pubbliche
- le sezioni da rimuovere in fase di export
- la cartella di output generata

La v1 pubblica la collection `personaggi/`, l'intera collection `resoconti/`, una singola pagina fissa (`ambientazione/ambientazione-giocatori.md`) e una allowlist di materiali gia` emersi al tavolo. I PG non passano dall'allowlist: ogni `personaggi/*.md` e` incluso automaticamente dalla collection. In particolare, `allowlist.entries` contiene i file da aggiungere al sito quando diventano di conoscenza dei giocatori (PNG, luoghi, altro).

### Personaggi giocanti (`personaggi/`)

Le schede PG non usano `profile: "public-png"`. Dopo la rimozione delle sezioni in `stripSections`, il corpo pubblicato coincide con la scheda nel repository privato (stat in testa, immagine, sezioni descrittive, `## Eventi interessanti`, ecc.).

### Profilo pubblico dei PNG

Le schede in `png/` non vengono pubblicate integralmente. Se un file `png/*.md` entra nella allowlist con `profile: "public-png"`, il sito mostra solo:

- nome del PNG
- sezione `## Immagine`
- descrizione pubblica ricavata da `## Aspetto`
- sezione `## Eventi interessanti`

Tutte le altre parti della scheda restano private, anche se non sono marcate come `## Note DM`.

### Aggiornamento della allowlist in fase resoconto

Alla finalizzazione di un nuovo resoconto, l'AI deve valutare quali materiali sono diventati ormai noti ai giocatori e aggiornare di conseguenza `allowlist.entries` nel manifest (i PG in `personaggi/` non vanno elencati qui: restano coperti dalla collection dedicata):

- `png/*.md` per i PNG conosciuti al tavolo
- `ambientazione/luoghi/*.md` per i luoghi visitati o identificati dai giocatori
- eventuali file di `ambientazione/` o altre pagine player-safe emerse in sessione

L'aggiornamento della allowlist fa parte della finalizzazione del resoconto e precede la rigenerazione del sito pubblico.

## Link automatici nei resoconti

Durante l'export, il sito aggiunge link interni in tre casi:

- i riferimenti `[Sessione NNN]` dentro `## Eventi interessanti`
- i nomi in `## Personaggi non giocanti incontrati` quando il PNG e` pubblicato
- i nomi in `## Luoghi visitati` quando il luogo e` pubblicato

In questo modo i resoconti pubblici diventano una piccola rete navigabile senza dover modificare a mano i file canonici del repository privato.

## Build locale

Installare la dipendenza per le thumbnail (consigliato anche in locale per avere le card complete):

```bash
pip install -r scripts/requirements-public-site.txt
```

Poi generare la sorgente del sito pubblico:

```bash
python3 scripts/build_public_site.py
```

Per scegliere una cartella diversa:

```bash
python3 scripts/build_public_site.py --output build/public-site
```

L'output e` una piccola sorgente Jekyll in `build/public-site/`, pronta per essere compilata e pubblicata da GitHub Pages.

## Anteprima locale con Docker

Per iterare sul lato grafico (CSS in `pubblicazione/assets/site.css`, layout HTML in `write_layout` dentro `scripts/build_public_site.py`) senza dover passare da un deploy su GitHub Pages, c'e` uno script che rigenera la sorgente Jekyll e la serve in locale tramite l'immagine Docker ufficiale di Jekyll. Non serve installare Ruby/Jekyll sulla macchina, basta avere Docker funzionante.

```bash
python3 scripts/serve_public_site.py
```

Lo script:

1. lancia `scripts/build_public_site.py` per rigenerare `build/public-site/`;
2. avvia un container effimero `jekyll/jekyll:4` che monta quella cartella e serve l'anteprima su `http://127.0.0.1:4000/`.

L'immagine usa Ruby 3.x, dove `webrick` non e` piu` incluso di default: lo script installa la gem `webrick` nel container prima di `jekyll serve` (richiede rete solo per quel passaggio, di solito pochi secondi). Per evitare problemi di DNS in reti aziendali (dove la rete bridge di Docker non vede il resolver dell'host) il container viene avviato di default con `--network=host`: condivide lo stack di rete della macchina, Jekyll si lega direttamente al `--bind` scelto e non serve port mapping.

Apri quell'URL nel browser; quando vuoi vedere le modifiche fatte ai template o al CSS, fermi il container con `Ctrl+C` e rilanci il comando. La prima esecuzione scarica l'immagine Docker (qualche centinaio di MB), le successive partono in pochi secondi grazie alla cache locale.

Flag utili:

- `--skip-build`: salta la rigenerazione e serve direttamente la sorgente gia` presente in `build/public-site/`;
- `--port 4001`: cambia la porta locale (utile se la 4000 e` occupata);
- `--bind 0.0.0.0`: espone l'anteprima alla LAN (di default e` legata a `127.0.0.1`);
- `--image <tag>`: forza un'immagine Docker diversa (es. `jekyll/jekyll:3` per avvicinarsi al runtime di GitHub Pages);
- `--network bridge`: torna alla rete `bridge` di Docker con port mapping classico (richiede che il container riesca a risolvere `rubygems.org` per installare `webrick`).

L'output di Jekyll (`_site/`, `.jekyll-cache/`) viene scritto dentro `build/public-site/` ed e` gia` ignorato da git.

## GitHub Pages

Il workflow `.github/workflows/publish-public-site.yml`:

1. installa le dipendenze Python dello script (`scripts/requirements-public-site.txt`)
2. genera la sorgente player-safe con lo script Python
3. compila il sito con Jekyll
4. pubblica l'artefatto su GitHub Pages

Per attivarlo nel repository GitHub:

1. apri `Settings > Pages`
2. scegli `GitHub Actions` come source
3. lascia che il workflow faccia deploy su ogni push a `main` o `master`, oppure avvialo manualmente

## Cloudflare Pages come fallback

Se in futuro vorrai spostare l'hosting, il punto di riuso resta lo stesso: `scripts/build_public_site.py` produce una sorgente player-safe stabile e ripetibile. Cloudflare Pages puo` usare la stessa sorgente come base di una build Jekyll dedicata, senza esporre il resto del repository.
