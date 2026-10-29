# -*- coding:utf-8 -*-
import re
import textwrap
import unicodedata

import requests

# Timeout par défaut : 5s (connexion) / 15s (lecture)
DEFAULT_TIMEOUT = (5, 15)

BASE_URL = "https://api.tisseo.fr/v2"

# Messages génériques sans intérêt pour l'affichage
NOISE_MESSAGE_IDS = {"info_agence_tisseo", "info_parc_relais"}

DATE_RE = re.compile(r"\b\d{2}/\d{2}/\d{4}\b")
# « 1er novembre 2026 », « dimanche 3 mai » : dates en toutes lettres de l'API
MONTH_RE = re.compile(
    r"\b\d{1,2}(?:er)?\s+"
    r"(?:janvier|f[ée]vrier|mars|avril|mai|juin|juillet|ao[uû]t|"
    r"septembre|octobre|novembre|d[ée]cembre)\b",
    re.IGNORECASE,
)
TIME_RE = re.compile(r"\b\d{1,2}\s*h\s*\d{2}\b", re.IGNORECASE)


def _is_dated(text):
    """La phrase contient-elle une date ou une heure exploitable ?"""
    return bool(DATE_RE.search(text) or MONTH_RE.search(text) or TIME_RE.search(text))
# Indices d'une perturbation bornée dans le temps (donc temporaire)
PERIOD_HINTS = ("jusqu'au", "à partir", "réouverture", "reouverture", "reprise")
# Phrases de service sans intérêt pour l'affichage
NOISE_SENTENCE_HINTS = ("plan interactif", "tisseo.fr", "prochains passages")
# Mots-clés d'une gêne de circulation (prioritaires dans l'extrait)
TRAFFIC_HINTS = (
    "interrompu",
    "perturb",
    "ferm",
    "non desservi",
    "dévié",
    "supprim",
    "retard",
    "remplac",
    "arrêt",
)


def _clean(text):
    """Retire emojis/contrôles et normalise les espaces (police bitmap limitée)."""
    if not text:
        return ""
    # NFC d'abord : sinon un accent décomposé (marque combinante) serait supprimé
    text = unicodedata.normalize("NFC", text)
    text = "".join(
        ch for ch in text if unicodedata.category(ch)[0] not in ("S", "C", "M")
    )
    text = " ".join(text.split())
    # Ponctuation : le Markdown laisse des espaces parasites (« 2026 . », « " x " »)
    text = re.sub(r"\s+([.,;!?])", r"\1", text)
    text = re.sub(r'"\s*([^"]*?)\s*"', r'"\1"', text)
    text = re.sub(r"([(\[])\s+", r"\1", text)
    text = re.sub(r"\s+([)\]])", r"\1", text)
    return text


def _strip_markdown(text):
    """Retire la syntaxe Markdown d'une ligne de l'API."""
    # [libellé](url) -> libellé
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    # titres, gras, italique, citations, code
    text = re.sub(r"[#*_`>]", " ", text)
    # puces en début de ligne
    text = re.sub(r"^\s*[-\u2022]\s*", " ", text)
    return text


def _content_lines(text):
    """[(est_un_titre, ligne_nettoyée), ...] en gardant la structure du message."""
    if not text:
        return []
    lines = []
    for raw in text.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        lines.append((raw.startswith("#"), _clean(_strip_markdown(raw))))
    return [(heading, line) for heading, line in lines if line]


def _as_list(value):
    """L'API renvoie tantôt une liste, tantôt un objet seul."""
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return []


def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _priority(sentence):
    """0 = gêne de trafic, 1 = date/période, 2 = contexte."""
    low = sentence.lower()
    if any(hint in low for hint in TRAFFIC_HINTS):
        return 0
    if _is_dated(sentence) or any(hint in low for hint in PERIOD_HINTS):
        return 1
    return 2


def format_wait(seconds):
    """150 -> '2 min 30 s' ; 38 -> '38 s' ; 120 -> '2 min'."""
    if seconds is None:
        return "?"
    if seconds < 60:
        return f"{seconds} s"
    minutes, rest = divmod(seconds, 60)
    if not rest:
        return f"{minutes} min"
    return f"{minutes} min {rest} s"


class Tisseo:
    def __init__(self, api_key, stop_area_id, line_short_name="A"):
        self.api_key = api_key
        self.stop_area_id = stop_area_id
        self.line_short_name = line_short_name
        self.line_id = None
        self.departures = []  # [{"direction": str, "times": [secondes, ...], "realtime": bool}]
        self.ok = False  # API joignable et réponse exploitable
        self.line_msg = None  # message propre à la ligne (dict API)
        self.general_msg = None  # premier message général du réseau (dict API)

    def update(self, number=3):
        self.departures = []
        self.ok = False
        self.line_msg = None
        self.general_msg = None
        self.line_id = None

        if not self.api_key or self.api_key == "None":
            print("Erreur : clé TISSEO absente ou vide (TISSEO_API_KEY du fichier .env)")
            return None
        if not self.stop_area_id or self.stop_area_id == "None":
            print("Erreur : arrêt TISSEO absent (TISSEO_STOP_AREA_ID du fichier .env)")
            return None

        try:
            response = requests.get(
                f"{BASE_URL}/stops_schedules.json",
                params={
                    "stopAreaId": self.stop_area_id,
                    "number": number,
                    "timetableByArea": 1,
                    "key": self.api_key,
                },
                timeout=DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur Tisséo (horaires) : {e}")
            return None
        except ValueError:
            print("Erreur Tisséo : réponse JSON invalide (horaires).")
            return None

        try:
            stop_areas = data["departures"]["stopAreas"]
        except (KeyError, TypeError):
            print("Erreur Tisséo : format de réponse inattendu.")
            return None

        for area in _as_list(stop_areas):
            for schedule in _as_list(area.get("schedules")):
                line = schedule.get("line") or {}
                if line.get("shortName") != self.line_short_name:
                    continue
                self.line_id = line.get("id")
                journeys = _as_list(schedule.get("journeys"))
                times = [
                    self._waiting_seconds(j.get("waiting_time")) for j in journeys
                ]
                times = [t for t in times if t is not None][:3]
                if not times:
                    continue
                realtime = any(j.get("realTime") == "1" for j in journeys)
                self.departures.append(
                    {
                        "direction": (schedule.get("destination") or {}).get(
                            "name", "?"
                        ),
                        "times": times,
                        "realtime": realtime,
                    }
                )

        self.ok = True
        self._fetch_messages()
        return self.departures

    @staticmethod
    def _waiting_seconds(waiting_time):
        """'HH:MM:SS' -> secondes (entier). None si illisible."""
        if not waiting_time:
            return None
        try:
            hours, minutes, seconds = (int(p) for p in waiting_time.split(":"))
            return hours * 3600 + minutes * 60 + seconds
        except (ValueError, AttributeError):
            return None

    def _fetch_messages(self):
        try:
            response = requests.get(
                f"{BASE_URL}/messages.json",
                params={"key": self.api_key},
                timeout=DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
        except (requests.exceptions.RequestException, ValueError):
            return

        wanted_id = f"line_{self.line_short_name}"
        for item in _as_list(data.get("messages")):
            msg = item.get("message", {})
            msg_id = msg.get("id", "")
            if msg_id in NOISE_MESSAGE_IDS:
                continue
            if not _clean(msg.get("title")):
                continue
            if msg.get("scope") == "line" and msg_id == wanted_id:
                self.line_msg = msg
            elif msg.get("scope") == "global" and self.general_msg is None:
                self.general_msg = msg

    def line_state(self):
        """normal | perturbe | interrompu | aucun | indisponible."""
        if not self.ok:
            return "indisponible"
        if not self.departures:
            # Pas de passage + un message sur la ligne = interruption probable
            return "interrompu" if self.line_msg else "aucun"
        if self.line_msg:
            return "perturbe"
        return "normal"

    def _kind(self):
        """Temporaire/définitive : déduit du texte, l'API ne le fournit pas."""
        msg = self.line_msg
        if not msg:
            return None
        text = f"{msg.get('title', '')} {msg.get('content', '')}".lower()
        if "définitiv" in text:
            return "définitive"
        if (
            _is_dated(text)
            or any(hint in text for hint in PERIOD_HINTS)
        ):
            return "temporaire"
        return None

    def status_text(self):
        state = self.line_state()
        if state in ("indisponible", "aucun"):
            return ""
        if state in ("interrompu", "perturbe"):
            kind = self._kind()
            suffix = f" ({kind})" if kind else ""
            if state == "interrompu":
                return f"LIGNE {self.line_short_name} INTERROMPUE{suffix}"
            return f"Ligne {self.line_short_name} : trafic perturbé{suffix}"
        if self.general_msg:
            return "Info réseau"
        return f"Ligne {self.line_short_name} : trafic normal"

    def status_alert(self):
        return self.line_state() in ("interrompu", "perturbe")

    def detail_lines(self, width=76, max_lines=3):
        """Titre + extrait daté du message, prêts à afficher (ligne A prioritaire)."""
        msg = self.line_msg or self.general_msg
        if not msg:
            return []

        title = _clean(msg.get("title"))
        if self.line_msg:
            # Le statut dit déjà « Ligne A … » : la place sert au détail
            title = ""

        title_lines = textwrap.wrap(title, width) if title else []
        budget = width * max(0, max_lines - len(title_lines))
        body = self._excerpt(msg.get("content"), budget) if budget else ""

        parts = list(title_lines)
        if body:
            parts.extend(textwrap.wrap(body, width))
        return parts[:max_lines]

    @staticmethod
    def _excerpt(content, max_chars):
        """Phrases les plus utiles du message (perturbation, dates), ordre d'origine."""
        lines = _content_lines(content)
        if not lines:
            return ""
        # Les lignes de titre (# …) répètent le champ « title » : on les écarte
        body = [text for heading, text in lines if not heading]
        if not body:
            body = [text for _, text in lines]

        sentences = []
        for line in body:
            sentences.extend(_sentences(line))
        sentences = [
            s
            for s in sentences
            if not any(hint in s.lower() for hint in NOISE_SENTENCE_HINTS)
        ]
        if not sentences:
            return ""

        # Priorité : nature de la gêne, puis date/période, puis le reste
        order = sorted(range(len(sentences)), key=lambda i: _priority(sentences[i]))

        picked = set()
        for index in order:
            if _priority(sentences[index]) > 1:
                break
            candidate = " ".join(
                sentences[i] for i in sorted(picked) + [index]
            )
            if picked and len(candidate) > max_chars:
                continue
            picked.add(index)
            if len(candidate) >= max_chars:
                break
        if not picked:
            picked = {0}

        out = " ".join(sentences[i] for i in sorted(picked)).strip()
        if len(out) > max_chars:
            cut = out[:max_chars].rsplit(" ", 1)[0]
            out = (cut or out[:max_chars]) + "..."
        return out

    def next_departures(self):
        return self.departures

    def line_message(self):
        """Compatibilité : titre du message affiché (ligne A prioritaire)."""
        msg = self.line_msg or self.general_msg
        return _clean(msg.get("title")) if msg else None
