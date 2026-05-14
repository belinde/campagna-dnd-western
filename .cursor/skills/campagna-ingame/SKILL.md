---
name: campagna-ingame
description: >-
  Fast tavolo-ready Italian outputs during live play; writes only under sessione/ with
  prefixed filenames. Use when the user runs /ingame, mentions modalità ingame, or live session improv.
disable-model-invocation: true
---

Rispettare sempre le convenzioni del repository definite nella Cursor Rule `campagna` (alwaysApply); non contradirle.

# Modalità Ingame

Questa regola si attiva durante una sessione di gioco dal vivo. Il DM ha bisogno di risposte **rapide, concise e immediatamente utilizzabili al tavolo**.

## Comportamento

- Risposte brevi: niente spiegazioni, meta-commenti o premesse
- Il testo generato deve poter essere letto direttamente ai giocatori
- Priorità alla giocabilità immediata rispetto alla completezza
- Non utilizzare ricerche su web o Wikipedia, all'occorrenza accedi soltanto al server mcp locale "dnd"

## Contenuti tipici da generare al volo

- **PNG**: nome, aspetto fisico in 2-3 righe, tratto caratteriale, motivazione
- **Luoghi**: descrizione atmosferica in 3-5 frasi, dettagli sensoriali (vista, suoni, odori)
- **Dialoghi**: battute in prima persona, coerenti con il personaggio
- **Incontri casuali**: tipo di incontro, numero di avversari, possibile aggancio narrativo
- **Nomi**: liste di nomi adatti all'ambientazione per PNG, luoghi, oggetti

## Salvataggio durante la sessione

Tutti i file creati durante la sessione vanno salvati nella cartella **`sessione/`** con il prefisso di tipo appropriato. L'agente resoconto li integrerà nelle cartelle definitive del repository a fine sessione.

Se durante la sessione esiste gia` un'immagine approvata, il file temporaneo puo` richiamarla direttamente con sintassi Markdown `![](/immagini/...)` e path a partire dalla root del workspace. Il Markdown resta in `sessione/`, ma gli asset in `immagini/` vivono fuori da `sessione/`.

| Tipo di contenuto | Nome file |
|---|---|
| Scheda PNG | `sessione/png-nome.md` |
| Descrizione luogo | `sessione/luogo-nome.md` |
| Appunti generici, dialoghi, eventi | `sessione/nota-argomento.md` |
| Incontro casuale | `sessione/incontro-nome.md` |

Il contenuto può essere grezzo e informale: la rifinitura avverrà in fase resoconto.

**Non scrivere mai direttamente in `png/`, `ambientazione/`, `personaggi/` o `resoconti/` durante la sessione dal vivo.**

## Schede PNG

Se il DM chiede di creare un PNG (o se ne genera uno abbastanza rilevante da meritare una scheda), salvare il file in `sessione/png-nome.md` con questa struttura:

```markdown
# Nome PNG

**Razza/Classe:** ...
**Ruolo:** ...

## Immagine

_Nessuna immagine ancora associata._

## Aspetto

Descrizione fisica in 2-4 frasi.

## Personalità

Tratto dominante, motivazione, segreto o debolezza.

## Legami con i PG

Come ha incontrato il gruppo, qual è il suo atteggiamento verso di loro.

## Note DM

Informazioni riservate al DM: retroscena, alleanze, obiettivi nascosti.

## Scheda di gioco

**Livello/Classe:** ...
**Ruolo tattico:** ...
**CA/PF/Velocita:** ...
**Caratteristiche:** For ..., Des ..., Cos ..., Int ..., Sag ..., Car ...
**Bonus competenza:** ...
**Tiri salvezza/Abilita:** ...
**Attacchi/Azioni:** ...
**Capacita/Incantesimi distintivi:** ...

## Eventi interessanti

_(da aggiornare dopo ogni sessione in cui il PNG appare)_
```

Se il livello del PNG non e` ancora presente in modo chiaro nella scheda, chiederlo esplicitamente al DM prima di completare `## Scheda di gioco`. Durante la sessione i dettagli meccanici possono restare compatti e parzialmente provvisori, ma il livello deve essere indicato.

Se esiste già un file in `png/` per quel personaggio, creare comunque `sessione/png-nome.md` con le nuove informazioni emerse durante la sessione: l'integrazione con la scheda esistente avverrà in fase resoconto.

## Luoghi generati al volo

Se il DM chiede di fissare un luogo nato durante la sessione, salvare `sessione/luogo-nome.md` con una struttura compatta ma coerente:

```markdown
# Nome Luogo

**Regione:** ...
**Tipo:** ...

## Immagine

_Nessuna immagine ancora associata._

## Descrizione generale

## Aspetto e atmosfera

## Punti di interesse

## Note DM
```

Se esiste gia` una veduta del luogo in `immagini/luoghi/`, sostituire la nota con `![Veduta di Nome Luogo](/immagini/luoghi/nome-luogo.jpg)`.

## Note ed eventi di sessione

Per `sessione/nota-argomento.md` e `sessione/incontro-nome.md` e` consentita una sezione opzionale `## Immagini collegate` con immagini gia` esistenti o appena approvate. Quando una scena sara` consolidata nel resoconto, andra` poi spostata sotto `immagini/eventi/sessione-NNN/`.

## Coerenza

Prima di generare contenuti, verificare (in sola lettura):
- I file in `ambientazione/` per nomi, luoghi e tono del mondo
- Gli ultimi file in `resoconti/` per la situazione corrente della campagna
- Tutti i file in `sessione/` per coerenza narrativa
- I file in `personaggi/` e `png/` se il contenuto riguarda personaggi già documentati
- I file in `spunti/` come fonte di ispirazione per agganci narrativi e potenziali eventi (non sono eventi canonici, ma idee che il DM potrebbe voler introdurre)
