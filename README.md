# Station Météo, Actualités & Passage du métro — Ecran e-Ink 7,5"

Station météo autonome sur **Raspberry Pi** affichant la météo du jour et les actualités françaises sur un écran **e-paper Waveshare 7,5" (B V2, 800×480, bicolore noir/rouge)**.
Ceci est un fork du projet initial créé par Aerodynamics (https://github.com/aerodynamics-py/WEATHER_STATION_PI)

## Fonctionnalités

- **Météo actuelle** : température, humidité, couverture nuageuse, vent (direction km/h), lever/coucher du soleil
- **Pluie dans l'heure** : prévision minute par minute (pas de 15 min)
- **Prévisions horaires** : +3h, +6h, +12h (température, probabilité de pluie, icône jour/nuit)
- **Prévisions quotidiennes** : +24h à +96h (min/max, probabilité de pluie, jour de la semaine en français)
- **Graphe pression/température** (optionnel via `--show-graph`) : historique 7 jours conservé dans `saved.txt`
- **Actualités** : 3 titres d'actualités françaises, découpés automatiquement sur plusieurs lignes
- **Prochains passages du métro** (API Tisséo) : horaires théoriques des deux directions à la station configurée
- **État de la ligne + info réseau** : trafic normal, perturbé ou interrompu (en rouge), avec un extrait daté du message (station concernée, réouverture estimée)
- **Mise en veille automatique** de l'écran la nuit (00h00–08h00) et rafraîchissement toutes les 4 minutes le jour
- **Auto-réparation** : power cycle matériel de l'écran toutes les ~100 rafraîchissements pour éviter les blocages SPI à long terme

## Matériel

| Composant | Référence |
|---|---|
| Raspberry Pi | 3B+, 4 ou 5 (testé sur RPi) |
| Ecran e-paper | Waveshare 7.5inch e-Paper (B) V2 — 800×480 bicolore |
| Rapide de stockage | Carte SD ≥ 8 Go |
| Alimentation | 5V stable ≥ 1A (adaptateur secteur dédié) |

### Branchement

La version *HAT* se branche directement sur le connecteur 40 broches. Version à nappe :

| E-paper | GPIO (BCM) |
|---|---|
| VCC | 3.3V |
| GND | GND |
| DIN | MOSI — GPIO10 |
| CLK | SCLK — GPIO11 |
| CS | CE0 — GPIO8 |
| DC | GPIO25 |
| RST | GPIO17 |
| BUSY | GPIO24 |

> L'alimentation du panneau est contrôlée par le pin **GPIO18** (`PWR_PIN`, défini dans `epdconfig.py`) : c'est lui qui sert au power cycle matériel.

## Prérequis système

- **Raspberry Pi OS 12 (Bookworm)** — fonctionnel et suivi jusqu'en août 2028
- Activer le bus **SPI** :
  ```bash
  sudo raspi-config     # Interface Options > SPI > Enable
  sudo reboot
  ```
- Vérification : `ls /dev/spidev*` doit afficher `/dev/spidev0.0`

## Installation

```bash
cd ~
git clone https://github.com/depuntism/WEATHER_STATION_PI.git
cd weather_station

# Compilateur + en-têtes Python : nécessaires pour construire spidev sous Python 3.11
sudo apt install python3-dev gcc -y
```

### Option A — pipenv (Pipfile fourni, recommandé)

Installe *toutes* les dépendances (y compris `gpiozero` et `spidev`, présents dans la `Pipfile` et la `Pipfile.lock`) :

```bash
pip install --user pipenv
pipenv install
```

### Option B — venv + requirements.txt

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Dans les deux cas, tester ensuite : `pipenv run python3 Assistant_main.py` (option A) ou `python3 Assistant_main.py` (option B).

## Configuration — `.env`

Copiez le modèle puis remplissez-le :

```bash
cp .env.example .env
nano .env
```

| Variable | Description |
|---|---|
| `LATITUDE` / `LONGITUDE` | Coordonnées GPS de la station (ex. `43.6` / `1.433333`) |
| `CITY` | Nom de la ville affiché |
| `NEWS_API_KEY` | Clé **CurrentsAPI** (https://currentsapi.services) — offre gratuite ~600 req/jour |
| `WEATHER_API_KEY` | **Laissez vide** : la météo utilise Open-Meteo (gratuit, sans clé) |
| `ENABLE_WEATHER_LOCATION` | Non utilisé actuellement |
| `TISSEO_API_KEY` | Clé **API Tisséo** (gratuite, par mail à `opendata@tisseo.fr`) |
| `TISSEO_STOP_AREA_ID` | Zone d'arrêt à afficher (ex. `stop_area:SA_1517` = Jolimont) |
| `TISSEO_STOP_NAME` | Nom affiché dans l'en-tête du bloc métro (ex. `Jolimont`) |
| `TISSEO_LINE` | Nom court de la ligne à filtrer (ex. `A`) |
| `CLEANED` | Géré automatiquement par le script (état de l'écran nocturne) |

## Métro & infos réseau (Tisséo)

Le bloc **MÉTRO** affiche, sous un filet de séparation et les actualités, les prochains passages de la ligne configurée (une ligne par direction), puis l'état de la ligne et un extrait de l'info réseau.

- **Clé API** : gratuite, à demander par mail à `opendata@tisseo.fr` (pas de portail en ligne).
- **Station** : l'identifiant se trouve avec l'endpoint `places` :
  ```bash
  curl "https://api.tisseo.fr/v2/places.json?term=jolimont&number=5&key=VOTRE_CLE"
  ```
  Reportez le champ `id` de la catégorie « Arrêts » (ex. `stop_area:SA_1517`) dans `TISSEO_STOP_AREA_ID`.
- **Horaires théoriques** : le métro toulousain est cadencé et **n'a pas de données temps réel**. Les temps d'attente affichés (minutes et secondes, ex. `~2 min 30 s`) sont donc théoriques, signalés par un `~` et par la mention `(~ théorique)` dans l'en-tête. Les bus/tram/Linéo, eux, disposent du temps réel.
- **Ligne affichée** : `TISSEO_LINE` (nom court, ex. `A`) filtre les passages de la station ; seules les deux premières directions sont affichées.
- **État de la ligne** : `normal`, `perturbé` (message sur la ligne mais passages présents) ou `interrompu` (aucun passage + message sur la ligne). Le statut passe en **rouge** en cas de perturbation ; s'il n'y a aucun passage et aucun message, le bloc affiche « Aucun passage annoncé ».
- **Temporaire ou définitive ?** L'API Tisséo ne fournit pas ce champ : la mention `(temporaire)` / `(définitive)` est **déduite du texte** du message (mot « définitive », sinon présence d'une date, d'une heure, de « jusqu'au », « réouverture »…). C'est indicatif, pas une donnée officielle.
- **Info réseau** : une perturbation propre à la ligne est prioritaire, sinon la première info générale du réseau. Le détail (3 lignes max) privilégie les phrases décrivant la gêne et les dates/heures (station concernée, réouverture estimée). Les messages « Agences » et « Parcs relais » sont ignorés, et les emojis sont retirés (police de l'écran).
- **Résilience** : toute erreur réseau/JSON est silencieuse côté écran (le bloc affiche « Horaires indisponibles » / « trafic normal ») et ne bloque jamais le cycle.

> **Licence des données** : données Tisséo sous licence [ODbL](https://data.toulouse-metropole.fr/page/licence) — source : [API Temps Réel Tisséo](https://data.toulouse-metropole.fr/explore/dataset/api-temps-reel-tisseo/information/). « TISSÉO » est une marque déposée ; ce projet n'est ni affilié ni approuvé par Tisséo.

## Tester en manuel

```bash
# Option A (pipenv)
pipenv run python3 Assistant_main.py

# Option B (venv classique)
python3 Assistant_main.py
```

> (Après `source .venv/bin/activate` en option B, la commande est simplement `python3 Assistant_main.py`.)

Attendu dans la console (~50 s) : `Météo mise à jour` → `Actualité mise à jour` → `Métro mis à jour` → `Impression en cours...` → `Mise en veille...` puis `Terminé`. L'écran doit afficher le tableau complet.

- Option **graphe** : `python3 Assistant_main.py --show-graph`
- Mode **debug** : `python3 Assistant_main.py --debug`
- Nettoyage d'écran avant extinction : `python3 clear_shutdown.py`

> Chaque exécution effectue **un** cycle complet puis se termine — c'est le principe « oneshot » exploité par le système de démarrage automatique.

## Démarrage automatique (recommandé : systemd)

Deux fichiers sont fournis à la racine du projet :

- `weathernews.service` : exécute un cycle complet (`flock` anti-chevauchement, timeout 4 min, faible priorité CPU/IO)
- `weathernews.timer` : déclenche toutes les **4 minutes**

```bash
# Adaptez le chemin du python selon votre installation :
#   pipenv  -> ExecStart=... /home/pi/weather_station/.venv/bin/pipenv run python3 Assistant_main.py
#   venv    -> ExecStart=... /home/pi/weather_station/.venv/bin/python3 Assistant_main.py
#   système -> ExecStart=... /usr/bin/python3 Assistant_main.py
# Le reste (flock, timeout, WorkingDirectory) est déjà paramétré dans weathernews.service :
#   WorkingDirectory=/home/pi/weather_station   (dossier du projet)

sudo cp weathernews.service weathernews.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now weathernews.timer

# Vérifier
systemctl list-timers | grep weathernews
```

> **Attention environnement** : le script charge toujours le `.env` situé **à côté de lui-même** avec `override=True`. Votre `.env` à jour doit donc vivre dans le dossier du script. Évitez de dupliquer ces variables ailleurs (ex. `EnvironmentFile=` d'une unité), au risque que la source de vérité soit ambiguë.

### Alternative historique : cron

`start_weathernews.py` crée les anciens jobs cron (mise à jour toutes les 6 min, indépendamment du timer systemd à 4 min, + troncature du log) :

```bash
python3 start_weathernews.py
```

À n'utiliser que si vous ne passez pas à systemd (ne pas cumuler les deux).

## Vérifier que tout fonctionne

| Vérification | Commande | Attendu |
|---|---|---|
| Écran rafraîchi | `journalctl -u weathernews --since "-1 hour"` | Séquence complète sans `Exception` |
| Météo OK | `python3 -c "from weather import Weather; w=Weather('43.6','1.433'); print(w.current_temp())"` | Température en °C |
| Actualités OK | `journalctl -u weathernews \| grep -a "Actualité"` | `Actualité mise à jour`, **pas** de ligne `401` |
| Métro OK | `journalctl -u weathernews \| grep -a "Métro"` | `Métro mis à jour`, pas d'erreur `Erreur Tisséo` |
| Log interne | `tail -20 conf/logging/main_error.log` | Erreurs éventuelles ; seuls les `logger` y sont écrits (les `print` vont dans le journal) |
| Power cycle écran | `grep -ai "reset hardware" conf/logging/main_error.log` | Une entrée toutes les ~100 cycles (~7 h) |
| Service actif | `systemctl status weathernews.timer` | `Active: waiting`, prochaine exécution affichée |

### Forcer un power cycle immédiat (test)

```bash
echo 99 > epd_cycle_count
sudo systemctl restart weathernews
sleep 60
grep -ai "power cycle" conf/logging/main_error.log
```

## Dépannage

| Symptôme | Cause probable | Solution |
|---|---|---|
| « Aucune actualité disponible » mais météo OK | Clé `NEWS_API_KEY` absente/erronée, ou variable injectée dupliquée (ex. `EnvironmentFile=`) | Vérifiez le journal : `apiKey=pub_...` dans l'URL = vieille clé. Mettez la bonne clé dans `.env` (maître grâce à `override=True`), retirez toute duplication systemd |
| Écran ne se rafraîchit plus après plusieurs jours | Pilote SPI / contrôleur e-paper figé (connu) | Le `power_cycle` toutes les ~100 cycles gère le problème seul. Le chemin d'erreur reconstruit aussi GPIO+SPI (`full_reboot`) |
| `grep` répond « fichiers binaires » | Encodage du log | Ajoutez `-a` : `grep -a ...` |
| Rien dans `Assistant_main.log` | Vous utilisez systemd : la sortie va dans journalctl | `journalctl -u weathernews -f` (le fichier log n'est écrit que par `logger`) |
| Mauvaise clé chargée malgré le `.env` correct | Une variable d'environnement existante écrase `.env` (comportement dotenv) | `load_dotenv(..., override=True)` est déjà activé — redéployez la dernière version du script |

## Structure du projet

```
├── Assistant_main.py      # Programme principal (cycles de mise à jour)
├── weather.py             # API Open-Meteo (météo + air) — pas de clé requise
├── news.py                # API CurrentsAPI (actualités françaises)
├── tisseo.py              # API Tisséo (métro + infos réseau)
├── display.py             # Rendu PIL (icônes, texte, cadres)
├── epd7in5b_V2.py         # Pilote Waveshare 7.5" B V2
├── epdconfig.py           # Interface GPIO/SPI + power_cycle + full_reboot
├── tools/graph.py         # Graphe pression/température (--show-graph)
├── icons/                 # Icônes météo (fichiers PNG)
├── font/                  # Polices disponibles (sélection dans display.py, font_choice)
├── start_weathernews.py   # Autostart cron (alternative historique)
├── clear_shutdown.py      # Nettoie l'écran avant extinction
├── weathernews.service    # Unité systemd (oneshot)
├── weathernews.timer      # Timer systemd (toutes les 4 min)
├── Pipfile / Pipfile.lock # Dépendances Python (pipenv)
├── requirements.txt       # Dépendances Python (pip)
├── .env.example           # Template de configuration
├── saved.txt              # Historique du graphe (généré, gitignoré)
└── epd_cycle_count        # Compteur power cycle (généré, gitignoré)
```

Fichiers générés à l'exécution (ignorés de Git) : `conf/logging/` (logs rotatifs), `saved.txt`, `epd_cycle_count`.

## Remarques

- **API météo** : [Open-Meteo](https://open-meteo.com) — gratuite, sans clé, `models=best_match` (sélection automatique ; pour la France, généralement AROME Météo-France).
- **API actualités** : [CurrentsAPI](https://currentsapi.services) — offre gratuite ~600 requêtes/jour (~160/jour ici).
- **API transports** : [API Temps Réel Tisséo](https://data.toulouse-metropole.fr/explore/dataset/api-temps-reel-tisseo/information/) — données sous licence [ODbL](https://data.toulouse-metropole.fr/page/licence). Usage raisonnable requis (~480 requêtes/jour ici).
- Sauvegardes des anciennes versions : `weather.py.bak`, `news.py.bak` (rollback : `cp weather.py.bak weather.py`).
- Le rafraîchissement de l'écran e-paper consomme un pic de courant : une **alimentation 5V stable** dédiée réduit fortement les blocages.
