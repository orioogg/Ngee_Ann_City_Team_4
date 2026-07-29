"""
save_manager.py
Handles saving and loading game state for Arcade mode.
Also manages the shared leaderboard for Arcade and Free Play modes.

Save files (stored next to the game scripts):
  arcade_save.json    - current arcade game state
  leaderboard.json    - top-10 high scores for each game mode

Author: Jun Wei
"""

import json
import os

_DIR = os.path.dirname(os.path.abspath(__file__))
# ── Jun Wei ───────────────────────────────────────────────────────
ARCADE_SAVE_PATH    = os.path.join(_DIR, "arcade_save.json")
LEADERBOARD_PATH    = os.path.join(_DIR, "leaderboard.json")

# Janice
FREEPLAY_SAVE_PATH = os.path.join(_DIR, "freeplay_save.json")
# Maximum entries kept per mode
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
    """
    Load Arcade game state from disk.
    Returns (data_dict, error_string).  data_dict is None on failure.
    """
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
    """Return a short summary string for the load screen, or None."""
    data, _ = load_arcade()
    if data is None:
        return None
    return f"Turn {data['turn']}  |  Score {data['score']}  |  Coins {data['coins']}"

# Features for Free Play mode (Janice)
def save_freeplay(turn, profit, score, city, consecutive_losses, loss_warning_shown, loss_warning_sidebar_active):
    """Persist the current Free Play game state to disk."""
    data = {
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
        with open(FREEPLAY_SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return True, "Free Play game saved!"
    except Exception as e:
        return False, f"Save failed: {e}"


def load_freeplay():
    if not os.path.exists(FREEPLAY_SAVE_PATH):
        return None, "No Free Play save file found."
    try:
        with open(FREEPLAY_SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data, None
    except Exception as e:
        return None, f"Load failed: {e}"

# displays information about the saved game
def freeplay_save_info():
    data, _ = load_freeplay()
    if data is None:
        return None
    return f"Turn {data['turn']}  |  Score {data['score']}  |  Profit {data['profit']:+d}"

# ── Leaderboard helpers Jun Wei ───────────────────────────────────────────────────────

def _load_leaderboard_raw():
    """Return the raw leaderboard dict from disk, or a blank template."""
    if not os.path.exists(LEADERBOARD_PATH):
        return {"arcade": [], "freeplay": []}
    try:
        with open(LEADERBOARD_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Ensure both keys exist (forward-compat guard)
        data.setdefault("arcade", [])
        data.setdefault("freeplay", [])
        return data
    except Exception:
        return {"arcade": [], "freeplay": []}


def load_leaderboard():
    """
    Return a dict with keys 'arcade' and 'freeplay', each a list of
    {'name': str, 'score': int} dicts sorted descending by score.
    Older entries with equal scores rank higher (stable sort preserved).
    """
    return _load_leaderboard_raw()


def add_leaderboard_entry(mode, score, name="Anonymous"):
    """
    Insert an entry into the leaderboard for *mode* ('arcade' or 'freeplay').
    Each entry is {'name': str, 'score': int}.
    Ties: the older (existing) score ranks higher — new equal score goes after.
    Keeps only the top LEADERBOARD_LIMIT entries.
    Returns the player's achieved rank (1-based), or None if not in top-10.
    """
    if mode not in ("arcade", "freeplay"):
        return None

    name = name.strip() or "Anonymous"

    data    = _load_leaderboard_raw()
    entries = data[mode]

    # Migrate any legacy plain-int entries (Jun Wei)
    entries = [
        e if isinstance(e, dict) else {"name": "Anonymous", "score": e}
        for e in entries
    ]

    # Check before inserting whether this score can make the top-10.
    # If the board is already full and the new score is strictly less than
    # the lowest entry, it won't make it.
    if len(entries) >= LEADERBOARD_LIMIT:
        min_score = min(e["score"] for e in entries)
        if score < min_score:
            return None  # not in top-10, don't save

    # Append new entry at the end (preserves insertion order for tie-breaking)
    entries.append({"name": name, "score": score})

    # Stable descending sort: higher score first; equal scores keep their
    # original relative order (older entry stays ahead — Python sort is stable)
    entries.sort(key=lambda e: e["score"], reverse=True)

    # Truncate to limit
    entries = entries[:LEADERBOARD_LIMIT]
    data[mode] = entries

    # Find the rank of this specific entry by identity (last occurrence of
    # the same name+score after the sort, since we just appended it last)
    rank = None
    for i, e in enumerate(entries):
        if e["name"] == name and e["score"] == score:
            rank = i + 1
            # Don't break — keep iterating so we end up at the *last* match,
            # which is the one we just inserted (ties: older ranks higher).

    try:
        with open(LEADERBOARD_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

    return rank
