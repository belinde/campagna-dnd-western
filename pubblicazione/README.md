# Pubblicazione player-safe

Questa cartella definisce il perimetro del sito pubblico generato dal repository privato della campagna.

## Cosa viene pubblicato in v1

- tutti i file in `resoconti/`
- `ambientazione/ambientazione-giocatori.md`
- i materiali inseriti esplicitamente nella allowlist di `manifest.json`
- le schede dei `png/` gia` noti ai giocatori, ma in **profilo pubblico ridotto**
- solo le immagini realmente referenziate dalle pagine pubbliche, incluse le scene in `immagini/eventi/`

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

La v1 pubblica l'intera collection `resoconti/`, una singola pagina fissa (`ambientazione/ambientazione-giocatori.md`) e una allowlist di materiali gia` emersi al tavolo. In particolare, `allowlist.entries` contiene i file da aggiungere al sito quando diventano di conoscenza dei giocatori.

### Profilo pubblico dei PNG

Le schede in `png/` non vengono pubblicate integralmente. Se un file `png/*.md` entra nella allowlist con `profile: "public-png"`, il sito mostra solo:

- nome del PNG
- immagine canonica
- descrizione pubblica ricavata da `## Aspetto`
- sezione `## Eventi interessanti`

Tutte le altre parti della scheda restano private, anche se non sono marcate come `## Note DM`.

### Aggiornamento della allowlist in fase resoconto

Alla finalizzazione di un nuovo resoconto, l'AI deve valutare quali materiali sono diventati ormai noti ai giocatori e aggiornare di conseguenza `allowlist.entries` nel manifest:

- `png/*.md` per i PNG conosciuti al tavolo
- eventuali file di `ambientazione/` o altre pagine player-safe emerse in sessione

L'aggiornamento della allowlist fa parte della finalizzazione del resoconto e precede la rigenerazione del sito pubblico.

## Build locale

Per generare la sorgente del sito pubblico:

```bash
python3 scripts/build_public_site.py
```

Per scegliere una cartella diversa:

```bash
python3 scripts/build_public_site.py --output build/public-site
```

L'output e` una piccola sorgente Jekyll in `build/public-site/`, pronta per essere compilata e pubblicata da GitHub Pages.

## GitHub Pages

Il workflow `.github/workflows/publish-public-site.yml`:

1. genera la sorgente player-safe con lo script Python
2. compila il sito con Jekyll
3. pubblica l'artefatto su GitHub Pages

Per attivarlo nel repository GitHub:

1. apri `Settings > Pages`
2. scegli `GitHub Actions` come source
3. lascia che il workflow faccia deploy su ogni push a `main` o `master`, oppure avvialo manualmente

## Cloudflare Pages come fallback

Se in futuro vorrai spostare l'hosting, il punto di riuso resta lo stesso: `scripts/build_public_site.py` produce una sorgente player-safe stabile e ripetibile. Cloudflare Pages puo` usare la stessa sorgente come base di una build Jekyll dedicata, senza esporre il resto del repository.
