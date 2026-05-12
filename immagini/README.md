# Gestione immagini canoniche

Le immagini canoniche della campagna vivono in questa cartella e vengono richiamate direttamente dai file Markdown, cosi` da essere:

- leggibili dagli agenti tramite il path esplicito nel file;
- visibili in anteprima Markdown;
- collegate in modo stabile a personaggi, luoghi e resoconti.

## Struttura delle cartelle

- `immagini/personaggi/<slug>.png|jpg|jpeg|webp`
- `immagini/png/<slug>.png|jpg|jpeg|webp`
- `immagini/luoghi/<slug>.png|jpg|jpeg|webp`
- `immagini/eventi/sessione-NNN/<slug-evento>.png|jpg|jpeg|webp`
- `immagini/varie/<slug>.png|jpg|jpeg|webp` per asset non ancora collegati a un file Markdown canonico

Lo `slug` deve seguire, quando possibile, il nome del file Markdown corrispondente:

- `personaggi/dora-l-esploratrice.md` -> `immagini/personaggi/dora-l-esploratrice.png`
- `png/andrew-carver.md` -> `immagini/png/andrew-carver.png`
- `ambientazione/luoghi/valdoren.md` -> `immagini/luoghi/valdoren.png`
- `resoconti/sessione-006.md` -> `immagini/eventi/sessione-006/dora-e-dorothy-in-accampamento.png`

## Sezioni da usare nei Markdown

### Personaggi, PNG e luoghi

Usare sempre una sezione `## Immagine canonica` vicino all'inizio del file, prima della prima sezione descrittiva.

Esempio per un personaggio:

```markdown
## Immagine canonica

![Ritratto canonico di Dora l'Esploratrice](/immagini/personaggi/dora-l-esploratrice.png)

*Ritratto canonico di Dora l'Esploratrice.*
```

Esempio per un luogo:

```markdown
## Immagine canonica

![Veduta canonica di Valdoren](/immagini/luoghi/valdoren.png)

*Veduta canonica di Valdoren.*
```

Se un'immagine non esiste ancora, mantenere comunque la sezione con la nota:

```markdown
## Immagine canonica

_Nessuna immagine canonica ancora associata._
```

### Resoconti

Usare `## Immagini salienti` subito dopo `## Riassunto`, ma solo quando esiste almeno un asset disponibile.

Esempio:

```markdown
## Immagini salienti

### Dora e Dorothy nell'accampamento

![Dora veglia su Dorothy Mercer nell'accampamento notturno](/immagini/eventi/sessione-006/dora-e-dorothy-in-accampamento.png)

*Dora resta accanto a Dorothy Mercer nell'accampamento notturno dopo la strage alla Fattoria Mercer.*
```

## Regole di consistenza

- Ogni file in `personaggi/`, `png/` e `ambientazione/luoghi/` ha una sola immagine primaria.
- Le scene di sessione vivono nei `resoconti/`, non nelle schede personaggio come immagine primaria.
- Le didascalie non devono introdurre nuovo canon: descrivono solo elementi gia` presenti nel testo.
- Evitare mapping impliciti basati solo su nomi vecchi o cartelle miste: il riferimento corretto e` sempre quello scritto nel Markdown.
- Gli asset ancora privi di scheda o resoconto di riferimento possono stare temporaneamente in `immagini/varie/`, ma vanno spostati nella cartella canonica non appena nasce il file Markdown collegato.
