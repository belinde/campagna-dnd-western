---
name: campagna-trascrizione-vc
description: >-
  Interactive dual-stream VC STT cleanup in chronological chunks: questions to the DM
  only for non-deducible gaps, master verifies each block before append to
  sessione/trascrizione.md. No invention. Use for /trascrizione-vc or
  sessione/trascrizione-grezza-doppia.txt.
disable-model-invocation: true
---

Rispettare sempre le convenzioni del repository definite nella Cursor Rule `campagna` (alwaysApply); non contradirle.

# Modalità Trascrizione videoconferenza (dual-track, a chunk)

Questa skill si attiva quando il DM ha generato `sessione/trascrizione-grezza-doppia.txt` (merge temporale: **MASTER** = microfono DM; canale **giocatori** = monitor uscita / VC, con etichette tipo `GIOC_B02_S01`) e vuole una **trascrizione elaborata verificata** in `sessione/trascrizione.md`, adatta al resoconto e all’archivio.

Il flusso è **interattivo**: la grezza si elabora a **blocchi di dimensione limitata**; si pongono **domande al master solo** dove manca evidenza testuale o serve una scelta; il master **approva o corregge** ogni blocco prima che venga scritto su disco. Non elaborare il file intero in un’unica passata senza i gate di verifica.

## Principio fondamentale

**Non inventare nulla.** Ogni battuta, descrizione o dettaglio proposto deve essere ricavabile dalla porzione di grezza del chunk corrente (e dal contesto già consolidato), o dalle risposte esplicite del master alle domande. Dove il testo è lacunoso, usare `[lacuna: ...]` e, se serve proseguire con coerenza, chiedere al master prima di persistere. Non interpolare eventi non esplicitati.

---

## Definizione di «riga di segmento» e di chunk

- **Riga di segmento**: riga della grezza che descrive un intervallo parlato, tipicamente del formato `Inizio–Fine [MASTER|GIOC_…] testo` (prima riga del file può essere un titolo `# …`; non contare come segmento).
- **Dimensione chunk (default)**: **da 20 a 45 righe di segmento**; puntare a **circa 32 righe** per chunk. Se spezzare a quota fissa taglierebbe una sequenza chiaramente unica (stessa battuta spezzata su più righe STT), estendere leggermente il chunk o ridurlo per chiudere al confine naturale.
- **Overlap analitico**: quando si lavora al chunk *N* > 1, includere nel contesto di lettura (non nel testo da **appendere**) le **ultime 2 righe di segmento** del chunk *N−1* già approvato, per continuità di riferimenti pronominali e ordine temporale.
- **Ordine**: sempre **cronologico** lungo la grezza (come i timestamp sulle righe); mai riordinare per speaker.

### Ripresa a sessione interrotta

Se esiste già `sessione/trascrizione.md` con contenuto sotto `## Dialogo` / `## Narrazione`:

1. Leggere `## Note di elaborazione` e cercare la riga di stato **`Progressione chunk:`** (vedi sotto). Se manca, stimare dai commenti HTML `<!-- trascrizione-vc-chunk:N -->` inseriti a fine ogni blocco persistito in `## Dialogo`.
2. Riprendere dalla **prima riga di segmento della grezza** non ancora coperta dall’ultimo chunk completato (il DM può indicare esplicitamente «riparti dalla riga L» o «dopo il timestamp T» — rispettare).
3. **Non** riscrivere chunk già approvati salvo richiesta esplicita del master di rifare un blocco.

---

## Fase A — Lettura del contesto (una tantum all’avvio del giro)

Prima del primo chunk (o subito dopo la ripresa, se manca ancora contesto in chat), leggere in sola lettura:

- [`sessione/trascrizione-grezza-doppia.txt`](sessione/trascrizione-grezza-doppia.txt) (intero file, almeno una volta; durante i chunk successivi basta la **finestra** della grezza per il chunk corrente ± overlap)
- Tutti i file in `ambientazione/` (incluse `luoghi/`, `nazioni/`, `concetti/`)
- Tutti i file in `personaggi/`
- `png/INDICE.md`; aprire le schede in `png/` solo se un nome in trascrizione richiede disambiguazione
- Tutti i file in `sessione/` **eccetto** `sessione/trascrizione.md` come output in scrittura controllata (leggerlo se esiste per ripresa) e artefatti generati nello stesso giro se il DM chiede di ignorarli
- Tutti i file in `spunti/`
- L’ultimo file in `resoconti/`

---

## Fase B — Sommario rolling (aggiornare tra un chunk e l’altro)

Mantenere in chat (e concisamente in `## Note di elaborazione` se utile) un **sommario rolling** di massimo ~15 righe:

- PNG e luoghi **già nominati** nel materiale verificato fin lì
- Decisioni del master su lacune o attribuzioni
- Contraddizioni risolte

Serve a coerenza tra chunk senza rileggere tutto il file ogni volta.

---

## Fase C — Loop per ogni chunk

Per il chunk corrente (finestra di righe di segmento sulla grezza):

### C1 — Pulizia (due voci)

Stesse regole della versione monolitica:

**Scartare** (master e giocatori): OOC, meta-gioco, tiri senza esito narrativo nella stessa sequenza, artefatti STT inutilizzabili, logistica call, correzioni in corsa senza esito finale, rumore sistema senza dialogo riconoscibile.

**Conservare**: narrazione master, dialoghi in-character, azioni dichiarate rilevanti, lore; discussioni di regole solo se l’esito narrativo è esplicitato subito dopo.

### C2 — Ricostruzione proposta (solo per questo chunk)

1. **`## Dialogo`** (solo parte chunk): turni `[MASTER]` e `[GIOC_Bxx_Syy]` / `[GIOC_Bxx_S?]` / `[GIOCATORI]`. **Non** attribuire nomi di PG da `personaggi/` se non inequivocabile dalla grezza o dal sommario rolling + battuta; usare `[lacuna: attribuzione parlante incerta]` se serve.
2. **`## Narrazione`** (solo parte chunk): prosa terza persona, **solo** da contenuti conservati; niente fatti nuovi.
3. Lacune: `[lacuna: breve descrizione]`.

### C3 — Domande al master (solo se necessario)

Usare `AskQuestion` (o messaggio strutturato con elenco puntato se lo strumento non basta) **solo** per:

- Lacune che impediscono attribuzione o comprensione del blocco
- Conflitto intra-chunk o con il sommario rolling / resoconto precedente
- Dettagli meccanici non esplicitati nel parlato

Se nulla di tutto ciò, dichiarare «nessuna domanda per questo chunk» e passare a C4.

### C4 — Verifica blocco

Presentare al master in chiaro:

1. **Riferimento grezzo**: intervallo di righe di segmento (o primi/ultimi timestamp del chunk) trattate.
2. **Proposta** `## Dialogo` + **proposta** `## Narrazione` per il chunk.

Chiedere esplicitamente: approvazione, correzioni inline, o richiesta di rifare il chunk con vincoli.

**Solo dopo approvazione esplicita** persistere (C5).

### C5 — Persistenza su disco

- **Primo chunk del giro** (file assente o vuoto o DM ha chiesto ricomincio da zero): creare `sessione/trascrizione.md` con il template completo sotto, inserendo contenuti del chunk solo nelle sezioni `## Dialogo` e `## Narrazione`, e in `## Note di elaborazione` includere:
  - nota su rumore/sfasamento se noto
  - riga **`Progressione chunk: chunk 1/N stimato`** (N stimato oppure «N da determinare»)
- **Chunk successivi**: **appendere** al contenuto esistente di `## Dialogo` e `## Narrazione` (due append distinti coerenti con l’ordine cronologico). Separare i blocchi con una riga vuota e un commento HTML:

```html
<!-- trascrizione-vc-chunk:K -->
```

dove `K` è l’indice 1-based del chunk. Aggiornare in `## Note di elaborazione` la riga **`Progressione chunk: chunk 1–K completati; ultima riga grezza coperta: …`** (o ultimo timestamp fine chunk).

Non appendere le righe dell’overlap analitico due volte.

### C6 — Chiusura del giro

Quando l’ultima riga di segmento della grezza è stata coperta e approvata:

- Aggiornare `## Note di elaborazione` con stato **completo** e eventuale nota «elaborazione a chunk verificata dal master».
- Indicare al DM che il passo successivo consigliato è **`/resoconto`** (skill `campagna-resoconto`), che userà `sessione/trascrizione.md` come **fonte primaria** degli eventi.

---

## Template file [`sessione/trascrizione.md`](sessione/trascrizione.md)

```markdown
# Trascrizione elaborata (VC) — [data o numero sessione se ricavabile]

## Note di elaborazione

- Elaborazione **a chunk** con verifica master tra un blocco e l’altro.
- Progressione chunk: [stato: in corso / completato; ultimo blocco K; ultima porzione grezza coperta]

[Breve nota su rumore/false trascrizioni, lacune ricorrenti, sfasamento canali se evidente]

## Dialogo

[Turni in ordine cronologico; dopo ogni chunk approvato, commento `<!-- trascrizione-vc-chunk:K -->`]

## Narrazione

[Prosa di supporto; append per chunk nello stesso ordine K]
```

---

## Output e vincoli finali

- Unico file di output canonico del flusso: **`sessione/trascrizione.md`**.
- Il master non deve «riscrivere tutta la sessione a memoria»: integra solo ciò che le domande C3 o la verifica C4 richiedono.
- Se il DM rinuncia esplicitamente alla trascrizione verificata per passare al resoconto, documentare quella scelta in `## Note di elaborazione` su richiesta del DM (fuori scope abituale della skill).
