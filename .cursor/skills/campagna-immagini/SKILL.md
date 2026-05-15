---
name: campagna-immagini
description: >-
  Campaign image workflows: self-contained English image prompts (cinematically realistic) for
  portraits, locations, and session scenes; and importing/normalizing JPEG assets into immagini/
  with Markdown updates. Use when the user runs /prompt-immagine or /importa-immagine, or asks for
  image prompts or asset import.
disable-model-invocation: true
---

Rispettare le convenzioni del repository nella Cursor Rule `campagna` (alwaysApply), **salvo** per la sola uscita del flusso **Prompt immagine**: il testo destinato al modello immagine esterno va redatto in **inglese** ed è un’**eccezione esplicita** alla regola generale del progetto che impone risposte e contenuti generati in **italiano**. Le righe `Tipo immagine:` e `Percorso suggerito:` (fuori dal blocco `text`) possono restare in italiano. **Dentro** il blocco `text` (in chat e in `## Riferimento visivo` sulle schede PG/PNG) usa le tre intestazioni keyword **sempre in inglese** (`Image prompt:`, `Constraints to preserve:`, `Details to avoid:`) e tutto il corpo sotto di esse in inglese. Sulle schede, l'intero prompt sta **solo** dentro un fence ` ```text ` … ` ``` ` sotto `## Riferimento visivo` — stesso blocco copiabile del command, senza intestazioni duplicate fuori dal fence.

# Immagini Campagna

Due flussi distinti: seguire **solo** la sezione richiesta dal command (`/prompt-immagine` vs `/importa-immagine`).

## Prompt immagine

Questa regola si attiva quando il DM chiede un prompt per generare l'immagine della scheda aperta o di una scena di sessione.

## Vincoli

- Opera solo in modalità Ask / sola lettura: non modificare file, non aggiornare direttamente il repository.
- Restituisci testo pronto per il generatore, senza premesse o meta-commenti oltre alla struttura sotto. `Tipo immagine` e `Percorso suggerito` restano **fuori** dal blocco codice; il blocco ` ```text ` raggruppa le tre sezioni da copiare in un colpo solo.
- Il prompt deve essere autosufficiente: chi lo legge non conosce la campagna.
- **Lingua:** tutto il contenuto **dentro** il blocco `text` (sotto le tre intestazioni keyword `Image prompt:`, `Constraints to preserve:`, `Details to avoid:`) va scritto in **inglese** naturale, denso di dettagli visivi, adatto a modelli di generazione immagine; resta l’eccezione alla rule `campagna` sull’italiano. Le intestazioni stesse restano **sempre** in inglese (non tradurle).
- **Stile visivo obbligatorio (globale):** ogni prompt deve imporre un look **cinematically realistic** — come fotogrammi da film o serie live-action di alta produzione: fotografia credibile, ottica da macchina da presa reale, luce naturale o di set coerente, profondità di campo realistica, texture fisiche (pelle, tessuto, metallo, polvere, legno), color grading sobrio; **evitare** estetica da illustrazione fantasy generica, videogioco, CGI “plastic” cartoony, fumetto o rendering 3D da brochure.

## Lettura del contesto

1. Leggi sempre la scheda aperta.
2. Recupera solo il contesto direttamente collegato e necessario.
3. Per un PG o PNG: se esiste `## Riferimento visivo` con blocco ` ```text ` completo e la richiesta è un **ritratto** (o variante di inquadratura dello stesso soggetto), leggi **solo** quel blocco e usalo come **fonte primaria** — riecheggia o adatta solo framing, luce o sfondo; non riscrivere da zero da `## Aspetto`. Se il DM chiede `/prompt-immagine` e il blocco in scheda è già aggiornato, l'output in chat può coincidere con il blocco in file (eventuali ritocchi di inquadratura). Per **scene di sessione**, componi da resoconti + `## Aspetto` + `## Riferimento visivo` (abbigliamento e tratti canonici). Se manca il Riferimento visivo, privilegia `## Aspetto`, `## Personalità`, `## Note DM`, `## Legami con i PG`, `## Eventi interessanti`, poi integra con `resoconti/` e ambientazione pertinente. Usa **`Razza:`** / **`Razza/Classe:`** in testa e le proporzioni nel Riferimento o in Aspetto. Per **orchi**, **Terre Selvagge** o **mezzorco** visivamente rilevanti, leggi anche `ambientazione/concetti/orchi-aspetto-e-cultura-materiale.md`.
4. Per un luogo: se esiste `## Riferimento visivo` con blocco ` ```text ` completo e la richiesta è una **veduta** (o variante di inquadratura dello stesso luogo), leggi **solo** quel blocco e usalo come **fonte primaria** — riecheggia o adatta solo framing, luce o stagione; non riscrivere da zero da `## Aspetto`. Altrimenti privilegia `## Aspetto`, `## Punti di interesse`, `## Storia e origine`, poi integra con `resoconti/`, PNG, concetti, fauna o fazioni collegati. Se il luogo è legato a **presenza orchesca** o **Terre Selvagge** in modo centrale alla scena, considera `ambientazione/concetti/orchi-aspetto-e-cultura-materiale.md` per figure o dettagli ambientali pertinenti.
5. Per un resoconto o una nota/incontro di `sessione/`, individua prima il momento piu` iconico gia` consolidato nel gioco; privilegia `## Riassunto`, `## Eventi principali` e i riferimenti a PG, PNG e luoghi coinvolti. Se compaiono **orchi** o **clan delle Terre Selvagge** come figure visivamente rilevanti, leggi anche `ambientazione/concetti/orchi-aspetto-e-cultura-materiale.md`.
6. Usa solo materiale gia` presente in ambientazione, schede e resoconti. Gli `spunti/` vanno ignorati salvo richiesta esplicita del DM.
7. Se la lore e` ambigua o incompleta, esplicita una breve assunzione minima invece di inventare nuova lore.

## Traduzione visiva

- Non limitarti a nominare elementi interni al mondo: trasformali in dettagli visivi concreti; la **forma finale** sotto `Image prompt:` va in **inglese** (anche se leggi il materiale di contesto in italiano).
- I nomi propri dei personaggi non devono comparire nel corpo del prompt (né in inglese né in italiano): descrivi il soggetto in modo autosufficiente tramite aspetto, ruolo, postura, equipaggiamento e contesto visivo.
- Esempio concettuale: «scout della carovana» → *well-worn travel clothes, light kit, watchful stance, road dust, frontier horizon* (sempre con il vincolo **cinematically realistic**).
- Esempio concettuale: «strage dei branchi» → *visible signs of exploitation on the plains, bones or hides, trampled tall grass, iron workshops or wagon trains if relevant* — sempre resa realistica da inquadratura filmica, non da icona stilizzata.
- Quando inserisci accenni di background, convertili sempre in atmosfera, mise-en-scene, oggetti, cicatrici, postura o dettagli dell'ambiente.
- Se la scheda suggerisce piu` immagini possibili, scegli quella piu` iconica e rendila chiara nel prompt.
- Oltre al prompt, suggerisci sempre il percorso previsto dal progetto in cui l'asset dovrebbe vivere, coerente con il file aperto.

### Orchi delle Terre Selvagge (traduzione visiva)

Combina la **morfologia D&D** (corpo alto e massiccio, zanne, orecchie, **pelle grigia con toni verdastri**) con **cultura materiale fantasy-prateria**: cuoio e pelli conciate, frange, perline o motivi geometrici inventati, coperte come mantelli, monili da scambio o trofeo, acconciature con ornamenti **non** ancorati a popoli reali. In **scene miste** con umani, elfi o mezzelfi, includi sempre il **confronto di altezza** (linea spalle, soglia, cavalcatura) come per le altre razze non medie.

### Proporzioni, razza e scene di gruppo

Allineamento visivo a D&D 5e: le parole «massiccio», «imponente», «veterano» **non** equivalgono ad altezza umana; la statura va sempre resa esplicita quando la razza non è un umanoide «medio» (umano, elfo, mezzelfo di corporatura simile).

- **Nano:** basso di statura, largo di spalle e torace, arti tozzi; accanto a umani, elfi o mezzelfi medi la **sommità del capo** resta nettamente **sotto** la loro (riferimento pratico: circa all’altezza del **petto o delle spalle** di un adulto medio). Può essere massiccio **in larghezza**, non in altezza.
- **Halfling** (se compare nel materiale letto): più basso e di corporatura più snella rispetto al nano; stesso obbligo di confronto visivo con figure medie.
- **Mezzorco:** più alto e più massiccio di un umano medio quando la scheda o il resoconto lo confermano; il contrasto con nani e halfling deve restare evidente.
- **Orco:** più alto e più largo dell’umano medio di riferimento; linea delle spalle e sommità del capo **sopra** l’umano accanto (ancora più imponente di un mezzorco tipico, salvo diversa indicazione nella scheda). Zanne inferiori visibili, orecchie appuntite; pelle **grigia con toni verdastri** — sempre esplicitata nel prompt come la statura, non solo «pelle non umana».
- **Dragonide:** più alto e imponente di un umano medio salvo diversa indicazione nella scheda.
- **Gnomo:** statura bassa paragonabile al nano, ma corporatura più snella se così descritto nella scheda; non confondere proporzioni con il nano «barbuto e tozzo» se il testo dice il contrario.

**Scene con più personaggi o più razze:** nel testo inglese sotto `Image prompt:` inserisci **sempre** almeno una frase sul **rapporto di altezza** (linea delle spalle, teste allineate in modo sbagliato da evitare, soglie di porte o carri, mani su impugnature rispetto al corpo altrui, cavalcature come scala). Così si evita che il modello uniformi tutti a umanoidi alti uguali tra loro.

## Formato dell'output

Struttura obbligatoria della risposta in chat:

1. **Fuori da qualsiasi blocco codice** (due blocchi testuali brevi, così il DM vede subito tipo e path):
   - Riga o paragrafo che inizia con `Tipo immagine:` seguito da una delle tre categorie: `ritratto (PG o PNG)`, `veduta (luogo)`, `scena di sessione`.
   - Riga o paragrafo che inizia con `Percorso suggerito:` seguito dal path sotto `immagini/` (es. `immagini/personaggi/<slug>.<ext>`, `immagini/png/...`, `immagini/luoghi/...`, `immagini/eventi/sessione-NNN/<slug-evento>.<ext>`).

2. **Subito dopo**, un **unico** blocco fenced Markdown con linguaggio `text`, che contenga **solo** le tre sezioni seguenti, **nell'ordine**, con queste intestazioni keyword **letterali in inglese** (inclusi i due punti) ciascuna su una propria riga prima del contenuto — **tutto il testo sotto le intestazioni deve essere in inglese**:
   - `Image prompt:` poi a capo il testo del prompt in **inglese** (uno o pochi paragrafi compatti: soggetto, tratti fisici e materiali, abbigliamento, attrezzatura, ambiente, fantasy-western con lievi tocchi **tecnomagici** dove la lore lo supporta, illuminazione, mood, background resi in modo visivo). Includi **sempre** la richiesta di resa **cinematically realistic** (fotografia credibile, non illustrazione). Se la razza è nano, halfling, gnomo, mezzorco, **orco** o dragonide (o la scena mescola razze diverse), il testo deve includere **sempre** statura e proporzioni coerenti con **Proporzioni, razza e scene di gruppo** e il confronto di altezza quando ci sono più figure; per **orchi** applica anche **Orchi delle Terre Selvagge** e la **cromia** grigio-verdastra (descritta in inglese).
   - `Constraints to preserve:` poi a capo il contenuto in **inglese** (se nulla da aggiungere oltre lo stile globale già nel prompt, scrivi `_None._`). Quando razza ≠ umanoide medio o sono in scena **più razze**, includi voci esplicite su **statura e rapporti tra le figure** oltre a quanto già nel prompt; puoi ripetere che il look deve restare **cinematically realistic**.
   - `Details to avoid:` poi a capo il contenuto in **inglese** (se nulla, `_None._`). Elenca errori probabili del modello (nani/halfling/gnomi con umani: statura; orchi: volto umanizzato, statura media, pelle verde brillante al posto del grigio verdastro, ecc.) e, se utile, divieti di stile: **no** cartoon, **no** plastic CGI, **no** generic fantasy illustration, **no** videogame HUD look — coerente con il vincolo di realismo cinematografico.

Il blocco deve aprirsi con una riga che contiene solo tre backtick (U+0060) seguiti dalla parola `text`, e chiudersi con una riga di soli tre backtick. **Non** annidare altri fence dentro questo blocco (niente triple-backtick nel contenuto delle tre sezioni).

Per verifica: la risposta deve consentire al DM di usare il pulsante copia del blocco codice sull’intero contenuto `text` (prompt + vincoli + dettagli) in un solo gesto.

### Riferimento visivo sulle schede PG/PNG

- Struttura: `## Riferimento visivo`, riga vuota, poi **un solo** blocco fenced `text` con le tre sezioni keyword (identico al blocco chat sopra). Intestazioni **senza** grassetto Markdown dentro il fence.
- Dopo aver prodotto o rivisto un prompt in chat, **aggiorna** il blocco sulla scheda quando il DM consolida il canon visivo (stesso testo o versione leggermente adattata).
- In **import** o revisione scheda: verifica che `## Riferimento visivo` contenga il fence `text` e che sia coerente con `## Aspetto` e il ritratto in `## Immagine`.

## Import asset immagine

Questa regola si attiva quando il DM ha gia` un file immagine generato e vuole inserirlo nel repository nel posto corretto, collegandolo anche al file Markdown giusto.

## Modalita`

- Opera solo in modalita` Agent / con permessi di scrittura.
- Se la chat e` in modalita` Ask, spiega brevemente che non puoi spostare file o aggiornare il repository e chiedi di passare ad Agent.
- Non generare prompt immagine e non generare nuove immagini: qui l'asset esiste gia`.
- L'asset va spostato nella destinazione prevista dal progetto, non copiato, salvo richiesta esplicita del DM.
- Lavora in modo conservativo: se il contesto non basta per scegliere una destinazione univoca, fai una domanda mirata invece di indovinare.

## Input attesi

Accetta uno di questi input:

- un path locale a un file immagine gia` esistente;
- un file allegato dal DM;
- il file Markdown aperto come contesto principale;
- una breve istruzione che chiarisca se si tratta di ritratto (PG o PNG), veduta di luogo o scena di sessione.

Se manca il file immagine effettivo, fermati e chiedilo esplicitamente.

## Lettura del contesto

1. Leggi sempre il file Markdown aperto o il file indicato dal DM come destinazione.
2. Recupera solo il contesto direttamente necessario per capire che cosa rappresenta l'immagine.
3. Per `personaggi/` e `png/`, privilegia `## Aspetto`, `## Riferimento visivo`, `## Eventi interessanti`, il **Promemoria** in testa alla scheda e l'eventuale `## Immagine`. Dopo l'import, verifica coerenza tra ritratto, Aspetto e Riferimento visivo (regola `.cursor/rules/personaggio-aspetto.mdc`).
4. Per `ambientazione/luoghi/`, privilegia `## Aspetto`, `## Riferimento visivo`, `## Punti di interesse` e l'eventuale `## Immagine`. Dopo l'import, verifica coerenza tra veduta, Aspetto e Riferimento visivo (regola `.cursor/rules/personaggio-aspetto.mdc`).
5. Per `resoconti/`, privilegia `## Riassunto`, `## Eventi principali` e l'eventuale sezione `## Immagini salienti`.
6. Per `sessione/`, usa il file solo come contesto provvisorio: se l'immagine deve diventare scena di sessione nel resoconto, chiarisci prima a quale `resoconti/sessione-NNN.md` dovra` essere collegata.

## Decisione del tipo immagine

Scegli il tipo in base al file di destinazione o all'istruzione del DM:

- `personaggi/*.md` -> ritratto (PG)
- `png/*.md` -> ritratto (PNG)
- `ambientazione/luoghi/*.md` -> veduta di luogo
- `resoconti/*.md` -> scena di sessione

Se il DM apre un file in `sessione/`, non fissare da solo il numero di sessione definitivo: chiedi conferma oppure chiedi quale resoconto andra` aggiornato.

## Percorso previsto per l'asset

Usa questi path:

- `immagini/personaggi/<slug>.jpg` per i PG
- `immagini/png/<slug>.jpg` per i PNG
- `immagini/luoghi/<slug>.jpg` per i luoghi
- `immagini/eventi/sessione-NNN/<slug-evento>.jpg` per le scene di sessione

Regole pratiche:

- Per PG, PNG e luoghi usa di norma lo slug del file Markdown di destinazione.
- Per le scene usa uno slug breve e descrittivo basato sull'evento mostrato.
- L'estensione finale nel repository e` sempre `.jpg` dopo la normalizzazione (vedi sotto), salvo richiesta esplicita del DM.
- Se il file e` gia` nel percorso corretto, non duplicarlo.
- Se il path di destinazione e` gia` occupato da un asset diverso, fermati e chiedi come procedere prima di sovrascrivere.
- Usa `immagini/varie/` solo se il DM lo chiede esplicitamente oppure se non esiste ancora un file Markdown collegato a cui agganciare l'asset.

## Normalizzazione asset

Prima di considerare l'import concluso, l'asset nel repository deve essere **JPEG** (`.jpg`), con **lato piu` lungo al massimo 1920 px** (rapporto d'aspetto invariato) e qualita` circa **85** (progressive), salvo richiesta esplicita del DM.

- **PNG / WebP** (e altri raster non JPEG): converti in JPEG; se c'e` trasparenza, appiattisci su **fondo bianco**; riduci se `max(larghezza, altezza) > 1920`; elimina il file sorgente dopo aver scritto `<slug>.jpg`.
- **JPEG con lato lungo > 1920**: riduci e salva come `<slug>.jpg` con qualita` ~85; elimina la sorgente se l'estensione o il nome cambiano.
- **JPEG con lato lungo <= 1920**: **solo rinomina** a `.jpg` (es. `.jpeg` -> `.jpg`) **senza ricompressione**; se e` gia` `.jpg` al path corretto, non toccare i pixel.

L'operazione e` **idempotente**: se il file e` gia` JPEG `.jpg` con vincolo rispettato nel path previsto, non modificarlo.

Per automatizzare: `python3 tools/scripts/normalize_image_assets.py <path-asset-o-cartella>` (opzione `--dry-run` per anteprima). Dopo conversioni/rinomine, lo script puo` aggiornare i riferimenti `/immagini/...` nei Markdown del repository.

## Aggiornamento del Markdown

Aggiorna sempre anche il file Markdown collegato all'asset.

### Personaggi, PNG e luoghi

Assicurati che esista una sola sezione `## Immagine`, subito prima della prima sezione descrittiva del file.

Formato:

```markdown
## Immagine

![Ritratto di Nome](/immagini/personaggi/nome.jpg)

*Ritratto di Nome.*
```

Per i luoghi:

```markdown
## Immagine

![Veduta di Nome Luogo](/immagini/luoghi/nome-luogo.jpg)

*Veduta di Nome Luogo.*
```

Regole:

- Se c'e` un placeholder `_Nessuna immagine ancora associata._`, sostituiscilo.
- Se esiste gia` un'immagine primaria, aggiornala invece di aggiungerne una seconda.
- La didascalia non deve introdurre nuova lore non gia` nel testo.

### Resoconti

Usa o crea la sezione `## Immagini salienti` subito dopo `## Riassunto`, ma solo quando esiste davvero un asset da collegare.

Formato:

```markdown
## Immagini salienti

### Titolo breve della scena

![Descrizione breve della scena](/immagini/eventi/sessione-NNN/slug-evento.jpg)

*Didascalia breve che descrive solo elementi gia` presenti nel resoconto.*
```

Regole:

- Non duplicare la sezione se esiste gia`.
- Ogni scena importata aggiunge un nuovo blocco sotto `## Immagini salienti`.
- Il titolo della scena deve essere breve, leggibile e coerente con il resoconto.
- Le immagini di evento appartengono ai `resoconti/`; non promuoverle a immagine primaria di personaggi o luoghi.

## Comportamento operativo

Quando il DM chiede di importare un'immagine:

1. identifica il file Markdown da aggiornare;
2. determina il tipo immagine e il percorso sotto `immagini/`;
3. sposta o rinomina l'asset nel path giusto, senza lasciarne una copia nella posizione originale;
4. normalizza l'asset a JPEG `.jpg` con lato lungo <= 1920 px (o esegui `python3 tools/scripts/normalize_image_assets.py` sul path);
5. aggiorna il Markdown con il link `/immagini/...` corretto (estensione `.jpg`);
6. evita duplicati, placeholder residui o sezioni ripetute;
7. conferma al DM il path finale dell'asset e il file Markdown aggiornato.

## Quando fermarsi e chiedere

Fai una domanda mirata invece di procedere se manca uno di questi elementi:

- il file immagine effettivo;
- il file Markdown di destinazione;
- il numero di sessione per una scena;
- la distinzione fra ritratto (personaggio) e scena di sessione quando entrambe sono plausibili;
- il consenso a sovrascrivere un asset gia` esistente nel percorso previsto.

