---
name: campagna-trascrizione-discord
description: >-
  Interactive Discord STT cleanup in chronological chunks (~35-75 segment lines,
  target ~55, 4-line overlap) on raw-merged format [TIME] ACTOR: text; numeric
  Discord IDs require DM mapping. Master verifies each block before append to
  sessione/trascrizione.md. No invention. Use for /trascrizione-discord or
  sessione/raw-merged.txt.
disable-model-invocation: true
---

Rispettare sempre le convenzioni del repository definite in `CLAUDE.md` (contesto permanente); non contradirle.

# Modalità Trascrizione Discord (merge grezzo, a chunk)

Questa skill si attiva quando il DM ha un file grezzo nel formato Discord merge — tipicamente [`sessione/raw-merged.txt`](sessione/raw-merged.txt) — e vuole una **trascrizione elaborata verificata** in `sessione/trascrizione.md`, adatta al resoconto e all’archivio.

## Ereditarietà da trascrizione VC

Per **principio «non inventare»**, dimensione chunk, overlap analitico, **Fase A**, **Fase B**, **Fase C** (C1 salvo aggiunte sotto, C3–C6), template strutturale e vincoli finali: applicare integralmente [`.claude/skills/campagna-trascrizione-vc/SKILL.md`](../campagna-trascrizione-vc/SKILL.md) **salvo** gli override espliciti in questa skill.

Il flusso resta **interattivo**: blocchi ampi ma verificabili (~55 righe di segmento per chunk); domande al master solo dove necessario; approvazione blocco per blocco prima di scrivere su disco.

---

## Input grezzo

- **File canonico:** [`sessione/raw-merged.txt`](sessione/raw-merged.txt) (export/bot Discord esterno al repo; non c’è script di generazione in `tools/`).
- **Path alternativo:** solo se il DM lo indica esplicitamente in chat.

---

## Definizione di «riga di segmento» (override VC)

- **Riga di segmento:** riga che rispetta il formato `[HH:MM:SS] ACTOR: testo` (timestamp `HH:MM:SS` o varianti a tre campi; `ACTOR` = etichetta tra `] ` e il primo `:` del segmento; `testo` = resto della riga).
- Righe vuote, commenti `# …` e righe che non matchano il pattern **non** contano come segmento.
- **Ordine:** cronologico per timestamp sulla riga; a parità di timestamp, ordine del file.
- **Dimensione chunk e overlap:** come in skill VC (35–75, target ~55, overlap analitico 4 righe).

### Parsing ACTOR

- **ACTOR numerico:** stringa composta **solo da cifre** (snowflake Discord, es. `616994893587283988`). Richiede risoluzione in Fase 0 (sotto).
- **ACTOR testuale:** nickname/display name Discord (es. `Grombrindal`, `Dora l'Esploratrice`). Usare l’etichetta grezza nel dialogo elaborato; **non** forzare il nome scheda da `personaggi/` se non inequivocabile (stessa regola VC).

### Etichette in `## Dialogo` (override C2)

- ID mappato a master narratore → `[MASTER]`
- ID mappato a PG o ACTOR testuale giocatore → `[GIOC_<Actor>]` dove `<Actor>` è l’etichetta Discord **letterale** (spazi e apostrofi ammessi, es. `[GIOC_Grombrindal]`, `[GIOC_Dora l'Esploratrice]`)
- ID incerto / altro → `[lacuna: ID …]` o etichetta concordata col master
- **Non** usare `GIOC_Bxx_Syy` (riservato al flusso VC)

---

## Fase 0 — Tabella attribuzioni Discord (obbligatoria)

**Prima del primo chunk** (o subito dopo ripresa se la tabella in `## Note di elaborazione` è assente o incompleta):

1. Leggere la grezza (intero file o campione sufficiente) ed estrarre tutti gli **ACTOR numerici** unici.
2. Per **ogni** ID non ancora in tabella: usare `AskQuestion` (o elenco puntato se lo strumento non basta) chiedendo al master:
   - **Master narratore** → dialogo `[MASTER]`
   - **Personaggio giocante** → indicare quale (preferire nomi da `personaggi/` se il DM li riconosce; altrimenti testo libero per l’etichetta `[GIOC_…]`)
   - **Altro / incerto** → `[lacuna: …]` fino a chiarimento
3. Persistere in `## Note di elaborazione`:
   - `Fonte: sessione/raw-merged.txt` (o path indicato dal DM)
   - `Attribuzioni Discord:` con elenco `ID → ruolo/etichetta` (es. `616994893587283988 → MASTER`)

**Durante i chunk:** se compare un **nuovo** ACTOR numerico non in tabella → **fermarsi**, completare Fase 0 per quell’ID, aggiornare la tabella, poi proseguire col chunk.

---

## Fase A — Lettura del contesto (override)

Come in skill VC, con questa sostituzione nella lista file grezzo:

- [`sessione/raw-merged.txt`](sessione/raw-merged.txt) (o path alternativo indicato dal DM): intero file almeno una volta; nei chunk successivi basta la **finestra** del chunk corrente ± overlap.

---

## Fase C — Override per chunk

### C1 — Pulizia (aggiunte Discord)

Oltre alle regole VC, **scartare** in particolare (se non portano contenuto narrativo in-character):

- Meta audio e setup («poste traccia audio», test microfono, «vedo tutti le fette di salame», «possiamo iniziare a giocare»)
- Logistica bot/stream/Discord senza esito narrativo
- Riassunti OOC di sessioni precedenti senza nuova decisione in gioco (sintetizzare in nota chunk solo se il master chiede di conservarli)

### C2 — Ricostruzione proposta (override)

1. **`## Dialogo`:** turni `[MASTER]` e `[GIOC_<Actor>]` come in «Etichette in Dialogo» sopra; lacune `[lacuna: …]` se serve.
2. **`## Narrazione`:** come VC — prosa terza persona solo da contenuti conservati.

### C3 — Domande al master

Oltre ai casi VC, **non** ripetere domande già risolte in Fase 0 per ID numerici noti. Usare C3 per lacune testuali, conflitti e meccanica non vocalizzata.

### C5 — Persistenza su disco (override marker)

Separare i blocchi approvati con:

```html
<!-- trascrizione-discord-chunk:K -->
```

(dove `K` è l’indice 1-based). **Non** usare `trascrizione-vc-chunk` in un giro avviato con questa skill.

In `## Note di elaborazione` mantenere sempre `Fonte:` e `Attribuzioni Discord:` aggiornate.

---

## Ripresa a sessione interrotta (override)

Se esiste già `sessione/trascrizione.md`:

1. Leggare `Progressione chunk:` e i marker `<!-- trascrizione-discord-chunk:N -->`.
2. Se compaiono **solo** marker `trascrizione-vc-chunk` ma la fonte in note è Discord/`raw-merged.txt`, **chiedere al DM** se proseguire con marker discord, rifare da zero o allineare manualmente.
3. Riprendere dalla prima riga di segmento grezza non coperta; non riscrivere chunk già approvati salvo richiesta esplicita.

---

## Template file [`sessione/trascrizione.md`](sessione/trascrizione.md)

```markdown
# Trascrizione elaborata (Discord) — [data o numero sessione se ricavabile]

## Note di elaborazione

- Elaborazione **a chunk** con verifica master tra un blocco e l’altro.
- Fonte: sessione/raw-merged.txt
- Attribuzioni Discord:
  - [ID numerico] → [MASTER | GIOC_… | lacuna]
- Progressione chunk: [stato: in corso / completato; ultimo blocco K; ultima porzione grezza coperta]

[Breve nota su rumore STT, lacune ricorrenti, frammentazione Discord se evidente]

## Dialogo

[Turni in ordine cronologico; dopo ogni chunk approvato, commento `<!-- trascrizione-discord-chunk:K -->`]

## Narrazione

[Prosa di supporto; append per chunk nello stesso ordine K]
```

---

## Output e passo successivo

- Unico file di output canonico: **`sessione/trascrizione.md`** (come VC).
- Al completamento, indicare **`/resoconto`** (skill `campagna-resoconto`) come passo successivo consigliato.
