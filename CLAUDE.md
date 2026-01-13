# Istruzioni per la gestione del sito

## Contesto
Sito personale accademico di Marco Guido Palladino.
- Stack: HTML statico (no framework)
- Branch: main
- URL: https://marcoguidopalladino.github.io

## Struttura
```
/
├── index.html           # Homepage
├── research.html        # Pubblicazioni e working papers
├── policy-teaching.html # Attività didattica e policy
├── assets/              # CSS, immagini, PDF
│   ├── css/
│   ├── img/
│   └── papers/          # PDF dei paper
├── CNAME                # Dominio custom (non toccare)
└── README.md
```

## Stile del sito
- Mantieni la struttura HTML e CSS esistente
- Prima di modificare, leggi il file per capire le convenzioni usate
- Usa le stesse classi CSS già presenti

## Workflow
1. Leggi i file rilevanti prima di modificare
2. Per modifiche sostanziali, mostrami prima cosa intendi fare
3. Dopo le modifiche: `git add . && git commit -m "descrizione" && git push`

## Task comuni

### Aggiungere un paper
- Aggiungi il PDF in `assets/papers/`
- Aggiungi la voce in `research.html` seguendo il formato esistente

### Aggiornare il CV
- Il CV è linkato nella homepage o in una sezione specifica
- Sostituisci il PDF in `assets/` se necessario

### Modificare i contenuti
- Le pagine sono HTML puro
- Mantieni la formattazione e le classi esistenti

## Convenzioni
- Commit in inglese
- Nomi file: lowercase con trattini (es. `my-paper.pdf`)
- Immagini ottimizzate prima di caricare

## Da NON fare
- Non modificare CNAME
- Non cambiare la struttura degli URL esistenti
- Non aggiungere framework o dipendenze
