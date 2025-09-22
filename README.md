# Space-Invaders

---

## ✨ Funzionalità principali

* 🚀 **Player controllabile** con movimento fluido e sparo di proiettili.
* 👾 **Nemici** che si muovono, sparano laser e scalano in difficoltà man mano che avanzi.
* 🎵 **Musica dinamica**: cambia velocità e intensità in base al livello/difficoltà.
* 🔊 **Effetti sonori** (spari, esplosioni, pause, game over) — con fallback se i file mancano.
* 🎨 **Asset fallback**: se un’immagine/suono non è presente, il gioco usa forme colorate e suoni silenziosi, così non va mai in crash.
* 🧮 **Collisioni corrette**: ora usano larghezza **e** altezza reali, evitando bug di hitbox.
* 📊 **HUD dettagliato**: punteggio, vite, livello, difficoltà, FPS e tempo di rendering per frame.
* ⏸ **Pause/Mute/Restart** con tasti dedicati (oltre al vecchio sistema Enter/Esc).
* ⚡ **FPS limitati** a 60 per prestazioni stabili.
* 🕹️ **Progressione dinamica**: ogni livello aggiunge nemici, velocità e difficoltà crescente.

---

## 🎮 Controlli

| Tasto                  | Azione                          |
| ---------------------- | ------------------------------- |
| ⬅️ Freccia sinistra    | Muovi il giocatore a sinistra   |
| ➡️ Freccia destra      | Muovi il giocatore a destra     |
| ⬆️ Freccia su / SPAZIO | Spara un proiettile             |
| ⏎ Enter / ESC          | Pausa (toggle)                  |
| P                      | Pausa (toggle alternativo)      |
| M                      | Attiva/disattiva audio (mute)   |
| R                      | Restart (riparte dal livello 1) |
| ❌ (chiudi finestra)    | Esci dal gioco                  |

---

## 🖼️ Screenshot

*(Puoi aggiungere qui delle immagini del gameplay, esempio:)*

![screenshot](docs/screenshot.png)

---

## ⚙️ Requisiti

* **Python 3.9+** (consigliato 3.10 o superiore)
* **Pygame** (`pip install pygame`)

Opzionale (se vuoi usare la musica e i suoni originali):

* File `.ogg` e `.wav` nella cartella `res/sounds/`
* File `.png` e `.jpg` nella cartella `res/images/`

Se i file non ci sono, il gioco userà fallback sicuri (sprite colorati, suoni silenziosi).

---

## 🚀 Avvio del gioco

Clona o scarica il progetto, poi lancia:

```bash
python space_invaders.py
```

---

## 📂 Struttura del progetto

```
space_invaders/
│── space_invaders.py   # Codice principale del gioco
│── res/
│   ├── images/
│   │   ├── spaceship.png
│   │   ├── enemy.png
│   │   ├── bullet.png
│   │   ├── beam.png
│   │   ├── background.jpg
│   │   └── alien.png   # icona finestra
│   └── sounds/
│       ├── pause.wav
│       ├── 1up.wav
│       ├── gameover.wav
│       ├── annihilation.wav
│       ├── explosion.wav
│       ├── enemykill.wav
│       ├── gunshot.wav
│       ├── laser.wav
│       ├── Space_Invaders_Music.ogg
│       └── Space_Invaders_Music_x2.ogg (e varianti più veloci)
└── README.md
```

*(Le cartelle `res/images` e `res/sounds` sono opzionali: il gioco funziona anche senza.)*

---

## 🛠️ Miglioramenti rispetto alla versione originale

* ✅ Gestione **robusta** degli asset (fallback invece di crash).
* ✅ **Collisioni corrette** (ora precise).
* ✅ **Gestione audio** migliorata (niente più errori se non c’è una scheda audio).
* ✅ **Pause/Mute/Restart** extra rispetto all’originale.
* ✅ **Game over** meno invasivo: puoi uscire subito con un tasto invece di aspettare 13 secondi.
* ✅ **Performance**: FPS stabili a 60.
* ✅ **Gameplay più interessante**: progressione di velocità, probabilità di fuoco dei nemici e bonus vita a ogni level-up.

---

## 💡 Idee future

* 🌟 **Power-up** (scudi, triplo colpo, velocità extra).
* 👾 **Nuovi tipi di nemici** con movimenti personalizzati.
* 🏆 **Classifica/hi-score salvata su file**.
* 🎮 **Multiplayer locale** (2 giocatori sulla stessa tastiera).
* 🎛️ **Menu iniziale** con opzioni personalizzabili (difficoltà, volume, fullscreen).

---

## 📜 Licenza

Questo progetto è rilasciato sotto licenza **MIT**.
Gli asset originali (suoni e immagini) appartengono ai rispettivi creatori.

---
