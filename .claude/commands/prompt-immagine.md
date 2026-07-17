# Prompt immagine

Prima di qualsiasi risposta, leggere con `Read` il file `.claude/skills/campagna-immagini/SKILL.md` e applicare **solo** la sezione **«Prompt immagine»** (ignorare la sezione Import).

**Eccezione a `CLAUDE.md`:** il contesto permanente impone contenuti in italiano; per questo comando, il blocco fenced `text` usa intestazioni keyword **fisse in inglese** — `Image prompt:`, `Constraints to preserve:`, `Details to avoid:` — e tutto il corpo sotto di esse va in **inglese** (modello immagine esterno). Le due righe `Tipo immagine:` e `Percorso suggerito:` restano **fuori** dal blocco (testo in italiano va bene).

**Schede PG/PNG:** in `## Riferimento visivo` incolla **lo stesso blocco** ` ```text ` … ` ``` ` (non ripetere le intestazioni fuori dal fence). Aggiorna il blocco sulla scheda quando consolidi un prompt nuovo o rivisto.

**Schede luogo:** in `## Riferimento visivo` incolla **lo stesso blocco** fenced; lunghezza libera (veduta e ambiente richiedono piu` contesto visivo di un ritratto). Aggiorna il blocco sulla scheda quando consolidi un prompt nuovo o rivisto.

Struttura: `Tipo immagine:` e `Percorso suggerito:` fuori da qualsiasi blocco codice; subito dopo un **unico** blocco Markdown fenced con linguaggio `text` (tre accenti grafi + `text` in apertura; soli tre accenti grafi in chiusura) con le tre sezioni nell’ordine definito nello skill.

**Stile:** ogni prompt deve richiedere esplicitamente un look **cinematically realistic** (come da skill).

Restituire senza altre premesse oltre a quella struttura. Per il resto, `CLAUDE.md` resta il contesto di lettura del repository.
