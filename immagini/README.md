# Gestione immagini

Le immagini della campagna vivono in questa cartella e vengono richiamate direttamente dai file Markdown, cosi` da essere:

- leggibili dagli agenti tramite il path esplicito nel file;
- visibili in anteprima Markdown;
- collegate in modo stabile a personaggi, luoghi e resoconti.

## Struttura delle cartelle

- `immagini/personaggi/<slug>.jpg`
- `immagini/png/<slug>.jpg`
- `immagini/luoghi/<slug>.jpg` (veduta o prima immagine del luogo)
- `immagini/luoghi/<slug>-<qualificatore>.jpg` per immagini aggiuntive dello stesso luogo (es. `-mappa`, `-veduta`)
- `immagini/eventi/sessione-NNN/<slug-evento>.jpg`
- `immagini/varie/<slug>.jpg` per asset non ancora collegati a un file Markdown di riferimento

Stesso schema di suffisso per PG/PNG quando servono piu` ritratti (`<slug>-mappa`, `<slug>-ritratto-alt`, ecc.). `/importa-immagine` non sovrascrive per default: vedi skill `campagna-immagini`.

Lo `slug` deve seguire, quando possibile, il nome del file Markdown corrispondente:

- `personaggi/dora-l-esploratrice.md` -> `immagini/personaggi/dora-l-esploratrice.jpg`
- `png/andrew-carver.md` -> `immagini/png/andrew-carver.jpg`
- `ambientazione/luoghi/valdoren.md` -> `immagini/luoghi/valdoren.jpg`
- `resoconti/sessione-006.md` -> `immagini/eventi/sessione-006/dora-e-dorothy-in-accampamento.jpg`

## Normalizzazione

Gli asset nel repository devono essere **JPEG** (`.jpg`) con **lato piu` lungo al massimo 1920 px**. Per import o batch usare il command Cursor **`/importa-immagine`** (skill `.cursor/skills/campagna-immagini/`) e lo script `python3 tools/scripts/normalize_image_assets.py` (opzione `--dry-run` per anteprima). Dopo la normalizzazione i link nei Markdown usano sempre `/immagini/.../slug.jpg`.

## Sezioni da usare nei Markdown

### Personaggi, PNG e luoghi

Usare sempre una sezione `## Immagine` vicino all'inizio del file, prima della prima sezione descrittiva.

Esempio per un personaggio:

```markdown
## Immagine

![Ritratto di Dora l'Esploratrice](/immagini/personaggi/dora-l-esploratrice.jpg)

*Ritratto di Dora l'Esploratrice.*
```

Esempio per un luogo:

```markdown
## Immagine

![Veduta di Valdoren](/immagini/luoghi/valdoren.jpg)

*Veduta di Valdoren.*
```

Piu` immagini nella stessa `## Immagine` (append in import additivo):

```markdown
![Mappa di Valdoren](/immagini/luoghi/valdoren-mappa.jpg)

*Mappa tattica: …*
```

Se un'immagine non esiste ancora, mantenere comunque la sezione con la nota:

```markdown
## Immagine

_Nessuna immagine ancora associata._
```

### Resoconti

Usare `## Immagini salienti` subito dopo `## Riassunto`, ma solo quando esiste almeno un asset disponibile.

Esempio:

```markdown
## Immagini salienti

### Dora e Dorothy nell'accampamento

![Dora veglia su Dorothy Mercer nell'accampamento notturno](/immagini/eventi/sessione-006/dora-e-dorothy-in-accampamento.jpg)

*Dora resta accanto a Dorothy Mercer nell'accampamento notturno dopo la strage alla Fattoria Mercer.*
```

## Regole di consistenza

- Ogni file in `personaggi/`, `png/` e `ambientazione/luoghi/` ha al piu` un asset **canonico** `<slug>.jpg` (ritratto o veduta principale); altre immagini usano path con suffisso e blocchi aggiuntivi in `## Immagine`.
- Le scene di sessione vivono nei `resoconti/`, non nelle schede personaggio come immagine primaria.
- Le didascalie non devono introdurre nuova lore: descrivono solo elementi gia` presenti nel testo.
- Evitare mapping impliciti basati solo su nomi vecchi o cartelle miste: il riferimento corretto e` sempre quello scritto nel Markdown.
- Gli asset ancora privi di scheda o resoconto di riferimento possono stare temporaneamente in `immagini/varie/`, ma vanno spostati nella cartella prevista dal progetto non appena nasce il file Markdown collegato.
