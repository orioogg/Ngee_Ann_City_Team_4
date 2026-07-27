"""
load_game.py
Displays two save slot panels (Arcade and Free Play).
- Arcade: fully functional save/load.
- Free Play: visual placeholder only ("Coming Soon").
"""

import pygame
import save_manager


def update(events, mouse_pos, assets):
    """
    Renders the load game screen and handles input.
    Returns (next_state, buttons_dict).
    Possible next states: "load_game", "arcade", "main_menu"
    """
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
    utils["draw_header"]("LOAD SAVED GAME")

    # ── Save info ─────────────────────────────────────────────────────────────
    arcade_info = save_manager.arcade_save_info()  # str or None

    # ── Panel layout ──────────────────────────────────────────────────────────
    panel_w = 320
    panel_h = 260
    gap     = 40
    total_w = panel_w * 2 + gap
    panel_y = assets["layout"]["HEADER_H"] + 70
    arcade_x = SW // 2 - total_w // 2
    free_x   = arcade_x + panel_w + gap

    # ── Helper: draw a panel background + title ───────────────────────────────
    def draw_panel_base(px, title, border_color):
        panel_rect = pygame.Rect(px, panel_y, panel_w, panel_h)
        bg_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        bg_surf.fill((10, 5, 30, 200))
        screen.blit(bg_surf, (px, panel_y))
        pygame.draw.rect(screen, border_color, panel_rect, 2, border_radius=8)
        title_surf = fonts["medium"].render(title, True, border_color)
        screen.blit(title_surf, title_surf.get_rect(center=(px + panel_w // 2, panel_y + 36)))
        pygame.draw.line(screen, border_color,
                         (px + 16, panel_y + 60), (px + panel_w - 16, panel_y + 60), 1)

    # ── Arcade panel (functional) ─────────────────────────────────────────────
    draw_panel_base(arcade_x, "ARCADE MODE", colors["CYBER_CYAN"])

    load_arcade_btn = None
    if arcade_info:
        parts = [p.strip() for p in arcade_info.split("|")]
        start_y = panel_y + 90
        for i, part in enumerate(parts):
            line = fonts["small"].render(part, True, (220, 220, 220))
            screen.blit(line, line.get_rect(center=(arcade_x + panel_w // 2, start_y + i * 34)))

        load_arcade_btn = pygame.Rect(arcade_x + panel_w // 2 - 110, panel_y + panel_h - 58, 220, 44)
        utils["draw_btn"](load_arcade_btn, "LOAD ARCADE SAVE", fonts["small"], mouse_pos,
                          color=colors["CYBER_CYAN"])
    else:
        no_save = fonts["small"].render("No save file found.", True, (100, 100, 120))
        screen.blit(no_save, no_save.get_rect(center=(arcade_x + panel_w // 2, panel_y + panel_h // 2)))

        btn_rect = pygame.Rect(arcade_x + panel_w // 2 - 110, panel_y + panel_h - 58, 220, 44)
        pygame.draw.rect(screen, (40, 40, 55), btn_rect, border_radius=4)
        pygame.draw.rect(screen, (70, 70, 90), btn_rect, 2, border_radius=4)
        s = fonts["small"].render("LOAD ARCADE SAVE", True, (70, 70, 90))
        screen.blit(s, s.get_rect(center=btn_rect.center))

    # ── Free Play panel (placeholder) ─────────────────────────────────────────
    # Dimmed border to signal it's inactive
    fp_color = (40, 100, 60)  # muted green
    draw_panel_base(free_x, "FREE PLAY MODE", fp_color)

    # "Coming Soon" badge
    badge_surf = fonts["medium"].render("COMING SOON", True, (60, 130, 80))
    screen.blit(badge_surf, badge_surf.get_rect(center=(free_x + panel_w // 2, panel_y + panel_h // 2 - 10)))

    sub_surf = fonts["tiny"].render("Save/load not yet available", True, (60, 100, 70))
    screen.blit(sub_surf, sub_surf.get_rect(center=(free_x + panel_w // 2, panel_y + panel_h // 2 + 22)))

    # Greyed-out button (purely visual, not clickable)
    fp_btn_rect = pygame.Rect(free_x + panel_w // 2 - 110, panel_y + panel_h - 58, 220, 44)
    pygame.draw.rect(screen, (25, 40, 30), fp_btn_rect, border_radius=4)
    pygame.draw.rect(screen, (40, 70, 50), fp_btn_rect, 2, border_radius=4)
    fp_s = fonts["small"].render("LOAD FREE PLAY SAVE", True, (40, 70, 50))
    screen.blit(fp_s, fp_s.get_rect(center=fp_btn_rect.center))

    # ── Back button ───────────────────────────────────────────────────────────
    back_r = pygame.Rect(SW // 2 - 165, panel_y + panel_h + 40, 330, 48)
    utils["draw_btn"](back_r, "BACK TO MAIN MENU", fonts["medium"], mouse_pos)

    # ── Hint ──────────────────────────────────────────────────────────────────
    hint = fonts["tiny"].render("[ENTER] to load Arcade  |  [ESC] to go back",
                                True, (100, 100, 130))
    screen.blit(hint, hint.get_rect(center=(SW // 2, SH - 26)))

    # ── Events ────────────────────────────────────────────────────────────────
    next_state = "load_game"

    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                next_state = "main_menu"
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and arcade_info:
                import arcade_mode
                ok, msg = arcade_mode.load_save()
                if ok:
                    next_state = "arcade"
                else:
                    assets["system"]["set_msg"](msg)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if back_r.collidepoint(mouse_pos):
                next_state = "main_menu"
            elif load_arcade_btn and load_arcade_btn.collidepoint(mouse_pos):
                import arcade_mode
                ok, msg = arcade_mode.load_save()
                if ok:
                    next_state = "arcade"
                else:
                    assets["system"]["set_msg"](msg)
            # Free Play panel click is intentionally ignored (not implemented)

    return next_state, {'back': back_r, 'load_arcade': load_arcade_btn}
