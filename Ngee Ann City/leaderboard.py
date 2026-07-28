# leaderboard.py
# Displays the Top 10 High Scores screen for both Arcade and Free Play modes.
# Accessed from the main menu ("DISPLAY HIGH SCORES") or after a game ends.
#
# Display format: "1. PlayerName – xxx points"  (per acceptance criteria)
# Ties: older score ranks higher (preserved by stable sort in save_manager).
# If fewer than 10 scores exist, only existing entries are shown.
# If no scores exist, "No high scores yet" is displayed.
# Press any key or click BACK to return to the main menu.
#
# Author: Jun Wei

import pygame
import save_manager

# Which tab is currently selected: "arcade" or "freeplay"
_active_tab = "arcade"


def reset():
    """Reset tab to Arcade whenever the screen is (re-)opened."""
    global _active_tab
    _active_tab = "arcade"


def update(events, mouse_pos, assets):
    """
    Renders the leaderboard screen and handles input.
    Returns (next_state, buttons_dict).
    """
    global _active_tab

    screen = assets["screen"]
    utils  = assets["utils"]
    fonts  = assets["fonts"]
    colors = assets["colors"]
    SW     = assets["SCREEN_W"]
    SH     = assets["SCREEN_H"]

    # ── Background ────────────────────────────────────────────────────────────
    utils["draw_bg_skyline"]()
    ov = pygame.Surface((SW, SH), pygame.SRCALPHA)
    ov.fill((8, 15, 40, 140))
    screen.blit(ov, (0, 0))

    # ── Header ────────────────────────────────────────────────────────────────
    utils["draw_header"]("HIGH SCORES")

    # ── Load leaderboard data ─────────────────────────────────────────────────
    lb_data = save_manager.load_leaderboard()
    # Each entry is {'name': str, 'score': int}; migrate legacy plain ints
    raw = lb_data.get(_active_tab, [])
    entries = [
        e if isinstance(e, dict) else {"name": "Anonymous", "score": e}
        for e in raw
    ]

    # ── Tab bar ───────────────────────────────────────────────────────────────
    HEADER_H    = assets["layout"]["HEADER_H"]
    tab_y       = HEADER_H + 16
    tab_w, tab_h, gap = 210, 42, 16
    total_tab_w = tab_w * 2 + gap
    tab_arcade_r   = pygame.Rect(SW // 2 - total_tab_w // 2,              tab_y, tab_w, tab_h)
    tab_freeplay_r = pygame.Rect(SW // 2 - total_tab_w // 2 + tab_w + gap, tab_y, tab_w, tab_h)

    for tab_rect, tab_key, label in (
        (tab_arcade_r,   "arcade",   "ARCADE MODE"),
        (tab_freeplay_r, "freeplay", "FREE PLAY"),
    ):
        active  = (_active_tab == tab_key)
        hover   = tab_rect.collidepoint(mouse_pos)
        tab_col = colors["CYBER_CYAN"] if tab_key == "arcade" else colors["GREEN_NEON"]
        bg_col  = tab_col if (active or hover) else (30, 10, 55)
        txt_col = (10, 10, 10) if (active or hover) else tab_col
        pygame.draw.rect(screen, bg_col,  tab_rect, border_radius=6)
        pygame.draw.rect(screen, tab_col, tab_rect, 2, border_radius=6)
        lbl = fonts["small"].render(label, True, txt_col)
        screen.blit(lbl, lbl.get_rect(center=tab_rect.center))

    # ── Table layout ──────────────────────────────────────────────────────────
    accent      = colors["CYBER_CYAN"] if _active_tab == "arcade" else colors["GREEN_NEON"]
    table_top   = tab_y + tab_h + 20
    row_h       = 40
    table_w     = 580
    table_left  = SW // 2 - table_w // 2

    # Column x-centres
    col_rank  = table_left + 36
    col_name  = table_left + 220
    col_score = table_left + table_w - 50

    # Column headers
    hdr_y = table_top + 10
    for text, cx in (("RANK", col_rank), ("PLAYER", col_name), ("SCORE", col_score)):
        s = fonts["small"].render(text, True, accent)
        screen.blit(s, s.get_rect(center=(cx, hdr_y)))
    pygame.draw.line(screen, accent,
                     (table_left, hdr_y + 16), (table_left + table_w, hdr_y + 16), 1)

    # Medal colours for top 3
    MEDAL = {1: (255, 215, 0), 2: (192, 192, 192), 3: (205, 127, 50)}

    # ── Rows ──────────────────────────────────────────────────────────────────
    if entries:
        for i, entry in enumerate(entries):
            rank      = i + 1
            row_y     = hdr_y + 22 + rank * row_h
            row_color = MEDAL.get(rank, (220, 220, 220))
            name_str  = entry.get("name",  "Anonymous")
            score_val = entry.get("score", 0)

            # Highlight background for top 3
            if rank <= 3:
                hi = pygame.Rect(table_left + 4, row_y - row_h // 2 + 3,
                                 table_w - 8, row_h - 5)
                hi_surf = pygame.Surface((hi.w, hi.h), pygame.SRCALPHA)
                hi_surf.fill((*row_color, 55 if rank == 1 else 30))
                screen.blit(hi_surf, hi)

            # Rank
            rank_s = fonts["medium"].render(f"#{rank}", True, row_color)
            screen.blit(rank_s, rank_s.get_rect(center=(col_rank, row_y)))

            # Player name — truncate if too long
            display_name = name_str if len(name_str) <= 14 else name_str[:13] + "…"
            name_s = fonts["medium"].render(display_name, True, row_color)
            screen.blit(name_s, name_s.get_rect(midleft=(table_left + 68, row_y)))

            # Score — format: "xxx points"
            score_s = fonts["medium"].render(f"{score_val} pts", True, row_color)
            screen.blit(score_s, score_s.get_rect(midright=(table_left + table_w - 6, row_y)))

            # Divider
            pygame.draw.line(screen, (50, 50, 75),
                             (table_left, row_y + row_h // 2 - 3),
                             (table_left + table_w, row_y + row_h // 2 - 3), 1)
    else:
        # Acceptance criteria: "No high scores yet" when file missing or empty
        empty_y = hdr_y + 22 + 3 * row_h
        no_data = fonts["medium"].render("No high scores yet.", True, (120, 120, 150))
        screen.blit(no_data, no_data.get_rect(center=(SW // 2, empty_y)))
        sub = fonts["tiny"].render(
            "Play a game to appear on the leaderboard!", True, (80, 80, 110))
        screen.blit(sub, sub.get_rect(center=(SW // 2, empty_y + 32)))

    # ── Back button ───────────────────────────────────────────────────────────
    back_r = pygame.Rect(SW // 2 - 165, SH - 70, 330, 46)
    utils["draw_btn"](back_r, "BACK TO MAIN MENU", fonts["medium"], mouse_pos)

    # ── Keyboard hint (acceptance criteria: press any key to return) ──────────
    hint = fonts["tiny"].render(
        "Press any key to return to main menu   |   [TAB] Switch mode",
        True, (80, 80, 110))
    screen.blit(hint, hint.get_rect(center=(SW // 2, SH - 18)))

    # ── Event handling ────────────────────────────────────────────────────────
    next_state = "high_scores"

    for event in events:
        if event.type == pygame.KEYDOWN:
            # Any key returns to main menu (acceptance criteria)
            next_state = "main_menu"
            # Override: TAB switches mode instead of leaving
            if event.key == pygame.K_TAB:
                _active_tab = "freeplay" if _active_tab == "arcade" else "arcade"
                next_state  = "high_scores"

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if back_r.collidepoint(mouse_pos):
                next_state = "main_menu"
            elif tab_arcade_r.collidepoint(mouse_pos):
                _active_tab = "arcade"
            elif tab_freeplay_r.collidepoint(mouse_pos):
                _active_tab = "freeplay"

    return next_state, {
        "back":         back_r,
        "tab_arcade":   tab_arcade_r,
        "tab_freeplay": tab_freeplay_r,
    }
