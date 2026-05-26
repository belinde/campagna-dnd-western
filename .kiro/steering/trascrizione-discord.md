---
inclusion: manual
---

# Trascrizione STT (Discord, a chunk)

Applica integralmente le regole della skill Discord, che a sua volta rimanda alla skill VC per le fasi comuni:

#[[file:.cursor/skills/campagna-trascrizione-discord/SKILL.md]]

#[[file:.cursor/skills/campagna-trascrizione-vc/SKILL.md]]

Input atteso: `sessione/raw-merged.txt` nel formato `[HH:MM:SS] ACTOR: testo`. Elaborazione a chunk (35–75 righe, target ~55, overlap 4). Fase 0 obbligatoria per ACTOR numerici. La rule `campagna` resta il contesto base del progetto (steering always-on).
