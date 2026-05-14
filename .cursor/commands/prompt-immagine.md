# Prompt immagine

Prima di qualsiasi risposta, leggere con `Read` il file `.cursor/skills/campagna-immagini/SKILL.md` e applicare **solo** la sezione **«Prompt immagine»** (ignorare la sezione Import).

**Eccezione alla rule `campagna`:** la rule imposta contenuti in italiano; per questo comando, tutto il testo **dentro** il blocco fenced `text` (sotto `Prompt immagine:`, `Vincoli da preservare:`, `Dettagli da evitare:`) va in **inglese**, perché è pensato per un modello immagine esterno. Le due righe `Tipo immagine:` e `Percorso suggerito:` restano **fuori** dal blocco (testo in italiano va bene).

Struttura: `Tipo immagine:` e `Percorso suggerito:` fuori da qualsiasi blocco codice; subito dopo un **unico** blocco Markdown fenced con linguaggio `text` (tre accenti grafi + `text` in apertura; soli tre accenti grafi in chiusura) con le tre sezioni nell’ordine definito nello skill.

**Stile:** ogni prompt deve richiedere esplicitamente un look **cinematically realistic** (come da skill).

Restituire senza altre premesse oltre a quella struttura. Per il resto, la rule `campagna` resta il contesto di lettura del repository.
