# Importa immagine

Prima di qualsiasi azione, leggere con `Read` il file `.claude/skills/campagna-immagini/SKILL.md` e applicare **solo** la sezione **«Import asset immagine»** (ignorare la sezione Prompt).

Richiede modalità Agent con permessi di scrittura su file e asset. `CLAUDE.md` resta il contesto base del progetto.

**Comportamento predefinito: additivo.** Conservare immagini e blocchi Markdown già presenti; aggiungere il nuovo asset (path con suffisso se il canonico è occupato) e appendere in `## Immagine` / `## Immagini salienti`. **Sostituire** file o riferimenti esistenti **solo** se il DM chiede esplicitamente sostituzione/aggiornamento dello stesso asset (es. «sostituisci», «replace», «aggiorna il ritratto»).

## Conversione e spostamento asset

Per tutte le operazioni su file immagine (verifica esistenza, controllo dimensioni, ridimensionamento, conversione in JPEG, spostamento nella destinazione e rimozione della sorgente), usare **sempre** lo script:

```bash
python3 tools/scripts/importa_immagine.py <path/origine> <path/destinazione.jpg>
```

Lo script gestisce automaticamente:
- Verifica che la sorgente esista e sia un file immagine valido
- Verifica che la destinazione non sia già occupata (errore se esiste; usare `--force` solo in modalità sostituzione esplicita)
- Conversione in JPEG (da PNG, WebP o altri raster) con appiattimento trasparenza su fondo bianco
- Ridimensionamento se il lato lungo supera 1920 px (rapporto d'aspetto invariato)
- Salvataggio JPEG qualità 85, progressive
- Eliminazione del file sorgente dopo import riuscito

### Opzioni

| Flag | Effetto |
|------|---------|
| `--force` | Sovrascrive la destinazione se esiste (solo per sostituzione esplicita del DM) |
| `--keep-source` | Non elimina il file sorgente dopo l'import |

### Esempio tipico

```bash
python3 tools/scripts/importa_immagine.py trep.png immagini/luoghi/trepali.jpg
```

I path possono essere relativi alla root del repository o assoluti.

## Aggiornamento Markdown

Dopo aver eseguito lo script con successo, aggiornare il file Markdown di destinazione secondo le regole della skill `campagna-immagini` (sezione «Aggiornamento del Markdown»): sostituire il placeholder `_Nessuna immagine ancora associata._` oppure appendere il nuovo blocco immagine in `## Immagine` / `## Immagini salienti`.
