---
name: campagna-trascrizione-vc
description: >-
  Cleans dual-stream VC speech-to-text (master + monitor) into labeled dialogue and narrative
  prose, with explicit lacunae and no invention. Use when the user runs /trascrizione-vc,
  mentions trascrizione videoconferenza, or STT cleanup from sessione/trascrizione-grezza-doppia.txt.
disable-model-invocation: true
---

Rispettare sempre le convenzioni del repository definite nella Cursor Rule `campagna` (alwaysApply); non contradirle.

# Modalità Trascrizione videoconferenza (dual-track)

Questa skill si attiva quando il DM ha generato `sessione/trascrizione-grezza-doppia.txt` (merge temporale dei flussi **MASTER** = microfono DM, **GIOCATORI** = monitor uscita audio / VC) e vuole una versione pulita per il resoconto e l’archivio.

## Principio fondamentale

**Non inventare nulla.** Ogni battuta, descrizione o dettaglio nell’output deve essere ricavabile dalla trascrizione grezza o dai file di contesto già esistenti. Dove il testo è lacunoso o incomprensibile, usare marcatori `[lacuna: ...]` come nella skill `campagna-trascrizione`. Non interpolare eventi non esplicitati.

---

## Fase 1 — Lettura del contesto

Prima di elaborare, leggere in sola lettura:

- [`sessione/trascrizione-grezza-doppia.txt`](sessione/trascrizione-grezza-doppia.txt) (input principale)
- Tutti i file in `ambientazione/` (incluse `luoghi/`, `nazioni/`, `concetti/`)
- Tutti i file in `personaggi/` e `png/`
- Tutti i file in `sessione/` **eccetto** `sessione/trascrizione.md` (file di output da sovrascrivere) e, se presente, eventuali altri artefatti generati dallo stesso giro (es. note manuali)
- Tutti i file in `spunti/`
- L’ultimo file in `resoconti/`

---

## Fase 2 — Pulizia (due voci)

Scorrere la trascrizione mantenendo l’**ordine cronologico** indicato dai timestamp in testa a ogni segmento grezzo (non riordinare per speaker).

Scartare (sia dal master sia dai giocatori):

- Frasi palesemente OOC: mondo reale, battute da tavolo, meta-gioco, tiri e meccaniche senza valore narrativo
- Artefatti STT: ripetizioni, parole isolate senza senso, frasi troncate inutilizzabili
- Logistica: problemi audio, “mi sentite?”, pause, chi entra/esce dalla call
- Correzioni in corsa del master (“aspetta”, “ricominciamo”) se non portano contenuto narrativo finale
- Rumore di sistema catturato dal monitor: notifiche, musica di sottofondo senza dialogo riconoscibile (se il testo è solo onomatopea o nonsense, omettere o marcare lacuna)

Conservare:

- Narrazione e descrizioni del master (luoghi, PNG, atmosfera)
- Dialoghi in-character dei giocatori e dichiarazioni di azione rilevanti
- Lore e rivelazioni dette da chiunque
- Discussioni di regole **solo** se producono un esito narrativo esplicitato nella stessa sequenza (altrimenti scartare)

---

## Fase 3 — Ricostruzione

1. **`## Dialogo`**: riscrivere i segmenti conservati in **turni etichettati** `[MASTER]` / `[GIOCATORI]`, in italiano chiaro, correggendo i nomi propri solo usando i file canonici (PG, PNG, luoghi). Unire segmenti consecutivi **dello stesso speaker** solo se nella grezza sono chiaramente la stessa battuta spezzata dallo STT (senza alterare il significato).

2. **`## Narrazione`**: dove ha senso, sintetizzare in prosa in **terza persona** (tono fantasy-western) le stesse informazioni già presenti nel dialogo pulito, **senza** introdurre fatti nuovi. Se il dialogo è già la forma migliore (molto scambi ravvicinati), la narrazione può essere breve o limitata alle scene descrittive del master; non duplicare pedissequamente ogni riga se non aggiunge chiarezza.

3. Lacune: usare esattamente il formato

```
[lacuna: breve descrizione del problema]
```

---

## Output

Salvare in [`sessione/trascrizione.md`](sessione/trascrizione.md):

```markdown
# Trascrizione elaborata (VC) — [data o numero sessione se ricavabile]

## Note di elaborazione

Breve nota su rumore/false trascrizioni, lacune, eventuale sfasamento tra i due canali se evidente dal testo.

## Dialogo

[Turni `[MASTER]` / `[GIOCATORI]` in ordine cronologico, con eventuali [lacuna: ...]]

## Narrazione

[Prosa di supporto / scene, solo da contenuti conservati]
```
