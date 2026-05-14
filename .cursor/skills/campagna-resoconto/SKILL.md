---
name: campagna-resoconto
description: >-
  Archives a D&D 5e session into resoconti/, updates PG/PNG sheets and ambientazione,
  clears sessione/, and runs player-safe publish when configured. Use when the user
  runs /resoconto, mentions modalità resoconto, or interactive post-session recap workflow.
disable-model-invocation: true
---

Rispettare sempre le convenzioni del repository definite nella Cursor Rule `campagna` (alwaysApply); non contradirle.

# Modalità Resoconto

Questa regola si attiva dopo una sessione di gioco. Il processo è **interattivo e a fasi sequenziali**: l'AI guida il DM passo dopo passo, fa domande mirate e non procede alla fase successiva senza esplicita conferma. Non produrre mai tutto il materiale in un'unica passata.

---

## Fase 1 — Raccolta iniziale

**Prima di fare qualsiasi domanda**, leggere in sola lettura:
- Tutti i file presenti in `sessione/` (materiale grezzo generato durante la sessione dal vivo), inclusi se presenti `sessione/trascrizione-grezza-doppia.txt` (grezzo dual-track VC) e `sessione/audio/` con le registrazioni WAV
- L'ultimo file in `resoconti/` (per capire dove era rimasta la storia)
- Tutti i file in `personaggi/` (per conoscere i PG disponibili)
- Tutti i file in `png/` (per riconoscere i PNG già documentati)

Poi chiedere al DM, con `AskQuestion`, le seguenti informazioni:
1. **Data della sessione** (formato GG/MM/AAAA)
2. **PG presenti** al tavolo quella sera (usare la lista dei file in `personaggi/` come opzioni selezionabili)
3. **Racconto libero degli eventi**: invitare il DM a descrivere cosa è successo in modo grezzo e informale, senza preoccuparsi della struttura. Il DM può usare termini generici per i personaggi (es. "il paladino", "il nano guerriero") — saranno risolti in automatico.

**Non procedere alla Fase 2 finché il DM non ha fornito il racconto.**

---

## Fase 2 — Chiarimenti e integrazioni

Analizzare il racconto del DM incrociandolo con il materiale letto in Fase 1. Identificare le ambiguità e le lacune, poi porre al DM domande mirate. Esempi tipici:

- **Riferimenti ambigui a personaggi**: se il DM ha scritto "il nano" e ci sono due nani tra i PG, chiedere quale.
- **PNG incontrati**: per ogni PNG menzionato che non ha ancora una scheda in `png/`, chiedere conferma del nome, ruolo e dettagli rilevanti.
- **Luoghi visitati**: per ogni luogo non ancora documentato in `ambientazione/luoghi/`, chiedere conferma del nome e un dettaglio descrittivo.
- **Incongruenze con la storia precedente**: segnalare qualsiasi contraddizione con i resoconti passati e chiedere chiarimento.
- **Esito di situazioni aperte**: se nell'ultimo resoconto erano rimaste domande aperte o ganci narrativi, chiedere se e come si sono risolti.

Raccogliere le risposte. Se emergono nuove ambiguità, fare ulteriori domande. Dichiarare esplicitamente quando il quadro è sufficientemente completo per procedere, e chiedere conferma al DM: *"Ho abbastanza informazioni per procedere. Confermato?"*

**Non procedere alla Fase 3 senza conferma del DM.**

---

## Fase 3 — Proposta titolo e riassunto

Proporre **due o tre titoli evocativi** per la sessione, in stile da cronaca epica.

Proporre un **riassunto** di 3-5 righe che sintetizzi la sessione, scritto in terza persona con i nomi dei PG.

Attendere che il DM scelga o corregga il titolo e approvi (o modifichi) il riassunto.

**Non procedere alla Fase 4 senza approvazione esplicita di titolo e riassunto.**

---

## Fase 4 — Bozza del resoconto completo

Scrivere la **bozza completa** del resoconto seguendo il template sotto. Presentarla al DM come testo in chiaro, **senza ancora salvare nessun file**.

```markdown
# Sessione NNN — Titolo evocativo

**Data:** GG/MM/AAAA

## Riassunto

Paragrafo breve (3-5 righe) che sintetizza la sessione.

## Immagini salienti

### Titolo scena

![Descrizione breve della scena](/immagini/eventi/sessione-NNN/nome-evento.jpg)

*Didascalia breve, coerente con il testo gia` presente nel resoconto.*

## Eventi principali

Narrazione degli eventi in ordine cronologico, in terza persona. Includere scelte dei PG rilevanti, combattimenti, rivelazioni narrative.

## Personaggi non giocanti incontrati

- **Nome PNG** — ruolo/relazione con i PG, cosa è emerso

## Luoghi visitati

- **Nome luogo** — breve descrizione o nota rilevante

## Note per la prossima sessione

- Ganci narrativi aperti
- Conseguenze di scelte dei PG da sviluppare
- Preparativi necessari per il DM
```

Tono: narrativo, in terza persona, con i nomi dei PG. Stile da cronaca epica, non da verbale burocratico.

La sezione `## Immagini salienti` e` facoltativa: inserirla solo quando esistono davvero uno o piu` asset. Non creare placeholder vuoti nei resoconti.

Chiedere al DM: *"La bozza è corretta? Vuoi modificare qualcosa prima che salvi il file?"*

Applicare eventuali correzioni e ripresentare la bozza. Solo dopo approvazione esplicita, **salvare il file** `resoconti/sessione-NNN.md` usando la numerazione progressiva (verificare l'ultimo numero in `resoconti/` per determinare il numero corretto).

**Non procedere alla Fase 5 senza aver salvato il file e ricevuto conferma.**

---

## Fase 5 — Aggiornamenti collaterali

Proporre al DM, **uno per uno**, ogni aggiornamento derivato dalla sessione. Per ciascuno, attendere conferma o modifica prima di applicare.

### 5a — Schede PG

Per ogni PG che ha vissuto un momento saliente, proporre la voce da aggiungere alla sezione `## Eventi interessanti` in `personaggi/nome-pg.md`:

```markdown
- **[Sessione NNN]** Breve descrizione dell'evento saliente.
```

Se durante la sessione viene approvato o associato un ritratto del PG, proporre anche l'aggiornamento della sezione `## Immagine` con il path corretto `/immagini/personaggi/<slug>.<ext>`.

### 5b — Schede PNG

Per ogni PNG apparso nella sessione:
- Se esiste già un file in `png/`, proporre la voce da aggiungere a `## Eventi interessanti` in quel file e integrare anche `## Scheda di gioco` se sono emersi dettagli meccanici nuovi o se il livello del PNG e` cambiato.
- Se **non** esiste ancora una scheda, segnalarlo al DM e proporre di crearla in `png/` seguendo il template standard (lo stesso usato dalla modalità ingame), inclusa la sezione `## Scheda di gioco`. Attendere conferma prima di creare il file.
- Se la scheda non indica ancora in modo chiaro il livello del PNG, chiederlo esplicitamente al DM prima di completare o aggiornare `## Scheda di gioco`.
- Se il livello cambia, aggiornare la parte meccanica in modo incrementale: mantenere la build gia` canonizzata e aggiungere solo i benefici coerenti del nuovo livello, salvo istruzioni contrarie del DM.
- Se viene approvato o recuperato un ritratto del PNG, aggiornare anche la sezione `## Immagine` con il path corretto `/immagini/png/<slug>.<ext>`.

Se il progetto usa una pubblicazione pubblica player-safe con allowlist esplicita, tenere nota dei PNG ormai **conosciuti dai giocatori**: in Fase 7 andranno aggiunti alla allowlist del sito. La pubblicazione dei `png/` deve usare un profilo pubblico ridotto che mostri solo **nome, sezione `## Immagine`, descrizione e `## Eventi interessanti`**.

### 5c — File di ambientazione

Se dal resoconto emergono informazioni rilevanti su luoghi o elementi del mondo non ancora documentati, segnalarlo al DM specificando quale file andrebbe creato o aggiornato, indicando la sottocartella corretta (`ambientazione/luoghi/`, `ambientazione/nazioni/` o `ambientazione/concetti/`). Attendere istruzione prima di agire.

Se esiste o viene approvata una veduta del luogo coinvolto nella sessione, proporre anche l'aggiornamento della sezione `## Immagine` del file pertinente in `ambientazione/luoghi/`.

Se il progetto usa una pubblicazione pubblica player-safe con allowlist esplicita, tenere nota anche dei **luoghi visitati o identificati dai giocatori**: in Fase 7 i relativi file in `ambientazione/luoghi/` vanno aggiunti alla allowlist del sito, cosi` i resoconti pubblici possono linkarli direttamente dalla sezione `## Luoghi visitati`.

### 5d — Smistamento file di sessione

Per ogni file in `sessione/`:
- **`png-*.md`** — Se esiste già un file in `png/` per quel PNG, integrare le nuove informazioni nella scheda esistente, inclusa `## Scheda di gioco` quando necessario. Altrimenti creare la scheda in `png/`. Se il livello e` assente o cambiato, chiederlo al DM e aggiornare la scheda in modo additivo, non sostitutivo.
- **`luogo-*.md`** — Valutare se aggiornare un file in `ambientazione/luoghi/` o proporne la creazione. Segnalare al DM prima di agire.
- **`nota-*.md`** / **`incontro-*.md`** — Verificare se ci sono informazioni utili non ancora incorporate nel resoconto o nelle schede; segnalare al DM se qualcosa è stato tralasciato.

Se esistono immagini collegate ai file di `sessione/`, archiviarle nella destinazione prevista dal progetto piu` adatta:
- `immagini/personaggi/` per i PG
- `immagini/png/` per i PNG
- `immagini/luoghi/` per i luoghi
- `immagini/eventi/sessione-NNN/` per le scene di sessione richiamate nel resoconto

I file di sessione sono **fonti complementari** al racconto del DM, non sostitutive: il DM resta la fonte primaria per gli eventi.

**Non procedere alla Fase 6 senza aver completato tutti gli aggiornamenti approvati.**

---

## Fase 6 — Riepilogo e pulizia

Presentare al DM un **riepilogo sintetico** di tutto ciò che è stato fatto:
- File creati o aggiornati (con percorso)
- Voci aggiunte alle schede personaggio
- Eventuali operazioni sospese o rimaste in attesa

Poi chiedere conferma prima di eliminare i file dalla cartella `sessione/`:

*"Posso eliminare i file di sessione temporanei? (sessione/... elenco file)"*

Solo dopo conferma esplicita, **eliminare tutti i file dalla cartella `sessione/`**. Se la cartella è già vuota, segnalarlo e passare comunque alla Fase 7.

---

## Fase 7 — Aggiornamento dei contenuti pubblicati

Se il repository contiene una configurazione di pubblicazione pubblica (per esempio `pubblicazione/manifest.json` e uno script di export dedicato), la fase finale del flusso e` l'aggiornamento del sito player-safe.

Prima di agire:

1. Verificare quali file canonici appena salvati ricadono nel perimetro pubblico definito dal manifest.
2. Verificare che le **immagini salienti** richiamate dal nuovo resoconto esistano davvero nel percorso previsto dal progetto, in particolare sotto `immagini/eventi/sessione-NNN/`.
3. Ricordare che la pubblicazione pubblica usa solo l'output filtrato: **non** esporre mai direttamente i file grezzi del repository privato.
4. Aggiornare la **allowlist** dei materiali conosciuti dai giocatori aggiungendo cio` che la sessione ha reso pubblico: `png/*.md` gia` noti al tavolo, `ambientazione/luoghi/*.md` per i luoghi visitati o chiaramente identificati, ed eventuali altri materiali player-safe approvati dal DM.

Poi:

- eseguire o aggiornare il flusso di export player-safe previsto dal progetto
- rigenerare i contenuti pubblici dopo gli aggiornamenti canonici approvati
- presentare al DM un riepilogo sintetico di cio` che andra` online: nuove pagine, resoconti aggiornati, immagini di scena incluse, voci aggiunte alla allowlist dei materiali conosciuti e nuovi link interni da `## Personaggi non giocanti incontrati` e `## Luoghi visitati`

Se il passo successivo richiede operazioni git o di rete (commit, push, deploy remoto, apertura di PR), chiedere sempre conferma esplicita prima di procedere.

Se il nuovo resoconto o le sue immagini non ricadono ancora nel perimetro pubblico, segnalarlo chiaramente al DM e proporre l'aggiornamento minimo necessario invece di pubblicare materiale in eccesso.
