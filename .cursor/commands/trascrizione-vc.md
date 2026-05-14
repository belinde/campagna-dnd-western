# Trascrizione STT (videoconferenza, dual-track, a chunk)

Prima di qualsiasi azione, leggere con `Read` il file `.cursor/skills/campagna-trascrizione-vc/SKILL.md` e applicare **integralmente** quel flusso.

Input atteso: `sessione/trascrizione-grezza-doppia.txt` (da `uv run python scripts/transcribe_session_dual.py …` dopo `scripts/session_record.sh`; il canale giocatori può contenere etichette diar `GIOC_Bxx_Syy`). Elaborazione **a chunk** con domande mirate al master solo dove necessario, **verifica blocco per blocco** prima di scrivere su disco, principio **non inventare nulla**. Output incrementale in `sessione/trascrizione.md` come da skill (append per chunk dopo approvazione). La rule `campagna` resta il contesto base del progetto. Dopo il completamento, il passo successivo tipico è `/resoconto` (trascrizione verificata come fonte primaria degli eventi).
