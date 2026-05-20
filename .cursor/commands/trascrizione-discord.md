# Trascrizione STT (Discord, a chunk)

Prima di qualsiasi azione, leggere con `Read` i file:

1. `.cursor/skills/campagna-trascrizione-discord/SKILL.md` — applicare **integralmente** (override Discord).
2. `.cursor/skills/campagna-trascrizione-vc/SKILL.md` — regole conmotioni (chunk, fasi A/B/C, non inventare) dove la skill Discord rimanda alla VC.

Input atteso: `sessione/raw-merged.txt` nel formato `[HH:MM:SS] ACTOR: testo` (merge da bot/export Discord; path alternativo solo se il DM lo indica). **Fase 0 obbligatoria:** per ogni `ACTOR` composto solo da cifre (ID Discord), chiedere al master se è master narratore, personaggio giocante o altro, e registrare la tabella in `## Note di elaborazione`.

Elaborazione **a chunk** (**35–75** righe di segmento, target **~55**; overlap analitico **4** righe; estensione fino a **~85** se serve chiudere una battuta STT spezzata) con domande mirate al master solo dove necessario, **verifica blocco per blocco** prima di scrivere su disco, principio **non inventare nulla**. Marker persistenza: `<!-- trascrizione-discord-chunk:K -->`. Output incrementale in `sessione/trascrizione.md` (append per chunk dopo approvazione). La rule `campagna` resta il contesto base del progetto. Dopo il completamento, il passo successivo tipico è `/resoconto` (trascrizione verificata come fonte primaria degli eventi).
