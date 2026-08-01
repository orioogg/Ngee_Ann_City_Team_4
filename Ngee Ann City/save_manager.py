"""
save_manager.py
Handles saving and loading game state for Arcade and Free Play modes.
Also manages the shared leaderboard for Arcade and Free Play modes.

"""

import json
import os

_DIR = os.path.dirname(os.path.abspath(__file__))
ARCADE_SAVE_PATH = os.path.join(_DIR, "arcade_save.json")
LEADERBOARD_PATH = os.path.join(_DIR, "leaderboard.json")
SAVES_DIR = os.path.join(_DIR, "saves")
ARCADE_SAVES_DIR = os.path.join(SAVES_DIR, "arcade")
FREEPLAY_SAVES_DIR = os.path.join(SAVES_DIR, "freeplay")

# Ensure the dedicated saves folders exist
os.makedirs(ARCADE_SAVES_DIR, exist_ok=True)
os.makedirs(FREEPLAY_SAVES_DIR, exist_ok=True)

LEADERBOARD_LIMIT = 10


def save_arcade(coins, turn, score, city, bldg1, bldg2,
                coin_warning_shown, coin_warning_sidebar_active):
    """Persist the current Arcade game state to disk."""
    data = {
        "coins": coins,
        "turn": turn,
        "score": score,
        "city": city,
        "rows": len(city),
        "cols": len(city[0]) if city else 0,
        "bldg1": bldg1,
        "bldg2": bldg2,
        "coin_warning_shown": coin_warning_shown,
        "coin_warning_sidebar_active": coin_warning_sidebar_active,
    }
    try:
        with open(ARCADE_SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return True, "Arcade game saved!"
    except Exception as e:
        return False, f"Save failed: {e}"


def load_arcade():
    if not os.path.exists(ARCADE_SAVE_PATH):
        return None, "No arcade save file found."
    try:
        with open(ARCADE_SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data, None
    except Exception as e:
        return None, f"Load failed: {e}"


def arcade_save_exists():
    return os.path.exists(ARCADE_SAVE_PATH)


def arcade_save_info():
    data, _ = load_arcade()
    if data is None:
        return None
    return f"Turn {data['turn']}  |  Score {data['score']}  |  Coins {data['coins']}"


# --- Arcade Named Save Operations (for arcade/freeplay folder structure) ---

def get_arcade_named_filepath(filename):
    """Get the full path for an arcade save file in the arcade folder."""
    clean_name = filename.strip()
    if not clean_name.endswith(".json"):
        clean_name += ".json"
    return os.path.join(ARCADE_SAVES_DIR, clean_name)


def arcade_named_save_exists(filename):
    """Check if an arcade save with the given filename exists."""
    path = get_arcade_named_filepath(filename)
    return os.path.exists(path)


def save_arcade_named(filename, coins, turn, score, city, bldg1, bldg2,
                      coin_warning_shown, coin_warning_sidebar_active):
    """Save arcade game with a custom filename to the arcade folder."""
    if not filename or not filename.strip():
        return False, "Filename cannot be empty!"

    path = get_arcade_named_filepath(filename)
    data = {
        "filename": filename.strip(),
        "coins": coins,
        "turn": turn,
        "score": score,
        "city": city,
        "rows": len(city),
        "cols": len(city[0]) if city else 0,
        "bldg1": bldg1,
        "bldg2": bldg2,
        "coin_warning_shown": coin_warning_shown,
        "coin_warning_sidebar_active": coin_warning_sidebar_active,
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True, f"Arcade game saved as '{filename.strip()}'!"
    except Exception as e:
        return False, f"Save failed: {e}"


def load_arcade_named(filepath):
    """Load an arcade save from a specific file path."""
    if not os.path.exists(filepath):
        return None, "Save file not found."
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data, None
    except Exception as e:
        return None, f"Load failed: {e}"


def list_arcade_saves():
    """Returns a list of available arcade save files info dictionaries."""
    saves = []
    if not os.path.exists(ARCADE_SAVES_DIR):
        return saves

    for fname in os.listdir(ARCADE_SAVES_DIR):
        if fname.endswith(".json"):
            fpath = os.path.join(ARCADE_SAVES_DIR, fname)
            data, err = load_arcade_named(fpath)
            if data:
                saves.append({
                    "path": fpath,
                    "filename": fname[:-5],
                    "turn": data.get("turn", 1),
                    "score": data.get("score", 0),
                    "coins": data.get("coins", 16)
                })
    return saves


# --- Free Play Save Operations ---

def get_freeplay_filepath(filename):
    clean_name = filename.strip()
    if not clean_name.endswith(".json"):
        clean_name += ".json"
    return os.path.join(FREEPLAY_SAVES_DIR, clean_name)


def freeplay_save_exists(filename):
    path = get_freeplay_filepath(filename)
    return os.path.exists(path)


def save_freeplay(filename, turn, profit, score, city, consecutive_losses, loss_warning_shown, loss_warning_sidebar_active):
    """Persist the Free Play game state with a custom filename."""
    if not filename or not filename.strip():
        return False, "Filename cannot be empty!"

    path = get_freeplay_filepath(filename)
    data = {
        "filename": filename.strip(),
        "turn": turn,
        "profit": profit,
        "score": score,
        "city": city,
        "rows": len(city),
        "cols": len(city[0]) if city else 0,
        "consecutive_losses": consecutive_losses,
        "loss_warning_shown": loss_warning_shown,
        "loss_warning_sidebar_active": loss_warning_sidebar_active,
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True, f"Saved game as '{filename.strip()}'!"
    except Exception as e:
        return False, f"Save failed: {e}"


def load_freeplay(filepath):
    if not os.path.exists(filepath):
        return None, "Save file not found."
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data, None
    except Exception as e:
        return None, f"Load failed: {e}"


def list_freeplay_saves():
    """Returns a list of available freeplay save files info dictionaries."""
    saves = []
    if not os.path.exists(FREEPLAY_SAVES_DIR):
        return saves

    for fname in os.listdir(FREEPLAY_SAVES_DIR):
        if fname.endswith(".json"):
            fpath = os.path.join(FREEPLAY_SAVES_DIR, fname)
            data, err = load_freeplay(fpath)
            if data:
                saves.append({
                    "path": fpath,
                    "filename": fname[:-5],
                    "turn": data.get("turn", 1),
                    "score": data.get("score", 0),
                    "profit": data.get("profit", 0)
                })
    return saves


# --- Leaderboard Helpers ---

def _load_leaderboard_raw():
    if not os.path.exists(LEADERBOARD_PATH):
        return {"arcade": [], "freeplay": []}
    try:
        with open(LEADERBOARD_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("arcade", [])
        data.setdefault("freeplay", [])
        return data
    except Exception:
        return {"arcade": [], "freeplay": []}


def load_leaderboard():
    return _load_leaderboard_raw()


def add_leaderboard_entry(mode, score, name="Anonymous"):
    if mode not in ("arcade", "freeplay"):
        return None

    name = name.strip() or "Anonymous"
    data = _load_leaderboard_raw()
    entries = data[mode]

    entries = [
        e if isinstance(e, dict) else {"name": "Anonymous", "score": e}
        for e in entries
    ]

    if len(entries) >= LEADERBOARD_LIMIT:
        min_score = min(e["score"] for e in entries)
        if score < min_score:
            return None

    entries.append({"name": name, "score": score})
    entries.sort(key=lambda e: e["score"], reverse=True)
    entries = entries[:LEADERBOARD_LIMIT]
    data[mode] = entries

    rank = None
    for i, e in enumerate(entries):
        if e["name"] == name and e["score"] == score:
            rank = i + 1

    try:
        with open(LEADERBOARD_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

    return rank
