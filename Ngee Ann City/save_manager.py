"""
save_manager.py
Handles saving and loading game state for Arcade mode.
Save file: arcade_save.json (stored next to the game scripts).
"""

import json
import os

_DIR = os.path.dirname(os.path.abspath(__file__))
ARCADE_SAVE_PATH = os.path.join(_DIR, "arcade_save.json")


def save_arcade(coins, turn, score, city, bldg1, bldg2,
                coin_warning_shown, coin_warning_sidebar_active):
    """Persist the current Arcade game state to disk."""
    data = {
        "coins": coins,
        "turn": turn,
        "score": score,
        "city": city,
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
