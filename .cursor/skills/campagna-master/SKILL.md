---
name: campagna-master
description: >-
  Expands DM notes into full ambientazione markdown (luoghi, nazioni, concetti) with
  templates and Wikipedia inspiration adapted to fantasy-western canon. Use when the user
  runs /master, mentions modalità master, or creating lore files under ambientazione/.
disable-model-invocation: true
---

Rispettare sempre le convenzioni del repository definite nella Cursor Rule `campagna` (alwaysApply); non contradirle.

# Modalità Master — Costruzione dell'Ambientazione

Questa regola si attiva quando il DM vuole trasformare idee e appunti concisi in un documento di ambientazione esteso e narrativo da salvare in `ambientazione/`.

## Flusso di lavoro

1. Il DM fornisce appunti liberi (anche telegrafici, anche disordinati)
2. **L'AI genera subito una bozza completa** del documento nel formato adatto al tipo di contenuto
3. Dopo la bozza, l'AI elenca le domande di approfondimento per affinare il documento in un secondo momento. L'AI non deve "inventare", ma solo "completare": può fare anche molte domande per inquadrare gli aspetti non chiari e può proporre suggerimenti.

## Coerenza con il canon

**Prima di generare qualsiasi contenuto**, leggere tutti i file presenti in `ambientazione/` per garantire coerenza totale con quanto già stabilito.

- Nomi di luoghi, fazioni, razze, date storiche e concetti tecnomagici devono essere consistenti con gli altri file
- Se un elemento degli appunti del DM entra in conflitto con qualcosa di già documentato, segnalarlo esplicitamente **prima** di scrivere la bozza e chiedere come risolvere il conflitto
- Non inventare elementi che contraddicano il canon (es. nuove nazioni, date storiche, tecnologie) senza segnalarlo

## File di output

Nome file in kebab-case. Se il DM non lo specifica, proporre un nome prima di scrivere. Salvare nella sottocartella corretta in base al tipo di contenuto:

| Tipo di contenuto | Sottocartella |
|---|---|
| Luogo (città, insediamento, dungeon, punto geografico, ecc.) | `ambientazione/luoghi/` |
| Fazione / Nazione / Organizzazione | `ambientazione/nazioni/` |
| Evento storico / Concetto / Lore (religioni, tecnomagia, economia, società, ecc.) | `ambientazione/concetti/` |

Il file `ambientazione/ambientazione-giocatori.md` è il documento di introduzione per i giocatori e non rientra in nessuna sottocartella.

## Template per tipo di contenuto

Identificare il tipo di contenuto dagli appunti del DM e usare il template corrispondente.

### Luogo (città, regione, insediamento, dungeon, ecc.)

```markdown
# Nome Luogo

## Immagine

_Nessuna immagine ancora associata._

## Descrizione generale

## Aspetto e atmosfera

## Abitanti e demografia

## Punti di interesse

## Storia e origine

## Ganci narrativi
```

### Fazione / Organizzazione (gilde, governi, culti, bande, ecc.)

```markdown
# Nome Fazione

## Descrizione e scopo

## Struttura e gerarchia

## Membri notevoli

## Risorse e influenza

## Relazioni con altre fazioni

## Segreti e obiettivi nascosti

## Ganci narrativi
```

### Evento storico (guerre, scoperte, catastrofi, trattati, ecc.)

```markdown
# Nome Evento

## Periodo e contesto

## Cause

## Svolgimento

## Conseguenze

## Come viene ricordato oggi

## Ganci narrativi
```

### Concetto / Lore (religioni, tecnomagia, culture, lingue, ecc.)

```markdown
# Nome Concetto

## Descrizione

## Origini

## Diffusione e praticanti

## Effetti sul mondo

## Ganci narrativi
```

## Tono

Narrativo e descrittivo, non enciclopedico. Evocare l'atmosfera del mondo, non elencare fatti. Coerente con il registro fantasy-western / tecnomagico della campagna.

Quando il contenuto generato e` un luogo, mantenere sempre la sezione `## Immagine` tra titolo/metadati e parte descrittiva. Se un asset esiste gia`, collegarlo con `![Veduta di Nome Luogo](/immagini/luoghi/<slug>.<ext>)` invece di lasciare il placeholder.

Quando gli appunti riguardano eventi storici, dinamiche sociali, economia, conflitti territoriali o figure di potere, **cercare ispirazione storica su Wikipedia** usando `WebSearch` e `WebFetch`: la storia del Far West americano (1840-1890) è la bussola narrativa della campagna. Adattare sempre i riferimenti trovati al contesto fantasy prima di usarli nel testo.
