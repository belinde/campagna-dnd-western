---
name: campagna-trascrizione
description: >-
  Cleans raw DM speech-to-text into narrative prose for the campaign repo, with explicit
  lacunae and no invention. Use when the user runs /trascrizione, mentions modalità trascrizione,
  or STT cleanup before saving to sessione/trascrizione.md.
disable-model-invocation: true
---

Rispettare sempre le convenzioni del repository definite in `CLAUDE.md` (contesto permanente); non contradirle.

# Modalità Trascrizione

Questa regola si attiva quando il DM vuole elaborare una trascrizione grezza (speech-to-text) della propria voce durante la sessione, estraendo la narrazione e scartando tutto il rumore.

## Principio fondamentale

**Non inventare nulla.** Ogni evento, dialogo, descrizione o dettaglio presente nell'output deve essere ricavabile dalla trascrizione grezza o dai file di contesto già esistenti. Dove la trascrizione è lacunosa, il buco va lasciato esplicito e visibile. Una lacuna marcata è sempre preferibile a qualsiasi interpolazione creativa.

---

## Fase 1 — Lettura del contesto

Prima di elaborare la trascrizione, leggere in sola lettura:

- Il file su cui è applicata la regola (la trascrizione grezza `.txt`)
- Tutti i file in `ambientazione/` (incluse le sottocartelle `luoghi/`, `nazioni/`, `concetti/`)
- Tutti i file in `personaggi/`
- `png/INDICE.md`; aprire le schede in `png/` solo se un nome in trascrizione richiede disambiguazione
- Tutti i file in `sessione/` (escluso il file di trascrizione stessa)
- Tutti i file in `spunti/`
- L'ultimo file in `resoconti/` (per contestualizzare dove era rimasta la storia)

---

## Fase 2 — Pulizia

Scorrere la trascrizione e scartare:

- Frasi palesemente OOC: battute, riferimenti al mondo reale, commenti sui tiri di dado, conversazioni tra giocatori
- Artefatti STT: parole isolate senza contesto, frasi troncate che non trasmettono significato, ripetizioni meccaniche della stessa parola
- Comunicazioni logistiche: pause, chi è al tavolo, problemi tecnici, interruzioni
- Correzioni in corsa del master ("anzi no", "aspetta", "sbaglio", "ricominciamo")
- Discussioni di regole che non producono narrazione

Conservare:

- Descrizioni di luoghi, atmosfere, ambienti
- Azioni e dialoghi dei PNG
- Annunci di eventi narrativi (arrivi, scoperte, scontri, rivelazioni)
- Informazioni di lore rilevanti dette durante la sessione
- Qualsiasi frase che avanza la trama o descrive il mondo

---

## Fase 3 — Ricostruzione

Il testo conservato va:

- Riscritto in prosa fluente, in terza persona, tono narrativo fantasy-western
- Corretto nei nomi propri usando i file di contesto (es. se la STT ha trascritto male il nome di un PNG o di un luogo, usare il nome canonico)
- Arricchito **solo** con dettagli già presenti nei file di contesto canonici — mai inventati
- Organizzato in sequenza cronologica, raggruppando scene coerenti in paragrafi

Dove la trascrizione è illeggibile, incoerente o troppo frammentata, inserire nel testo un marcatore esplicito:

```
[lacuna: breve descrizione del problema — es. "sezione incomprensibile di circa 2 minuti" o "dialogo troncato, esito ignoto"]
```

Non cercare di colmare le lacune. Non dedurre eventi non esplicitati.

---

## Output

Salvare il risultato in `sessione/trascrizione.md` con il seguente template:

```markdown
# Trascrizione elaborata — [data o numero sessione se ricavabile dalla trascrizione o dall'ultimo resoconto]

## Note di elaborazione

Breve nota sull'entità del rumore filtrato e sulle lacune identificate (quante, dove, di che natura).

## Narrazione

[testo narrativo ricostruito, organizzato in scene/paragrafi con eventuali marcatori [lacuna: ...]]
```
