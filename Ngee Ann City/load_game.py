import pygame
import save_manager

selected_fp_index = 0

def update(events, mouse_pos, assets):
    global selected_fp_index
    screen = assets["screen"]
    utils  = assets["utils"]
    fonts  = assets["fonts"]
    colors = assets["colors"]
    SW     = assets["SCREEN_W"]
    SH     = assets["SCREEN_H"]

    utils["draw_bg_skyline"]()
    ov = pygame.Surface((SW, SH), pygame.SRCALPHA)
    ov.fill((8, 15, 40, 140))
    screen.blit(ov, (0, 0))

    utils["draw_header"]("LOAD SAVED GAME")

    arcade_info = save_manager.arcade_save_info()
    freeplay_saves = save_manager.list_freeplay_saves()

    panel_w = 340
    panel_h = 280
    gap     = 30
    total_w = panel_w * 2 + gap
    panel_y = assets["layout"]["HEADER_H"] + 50
    arcade_x = SW // 2 - total_w // 2
    free_x   = arcade_x + panel_w + gap

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

    # --- Arcade Panel ---
    draw_panel_base(arcade_x, "ARCADE MODE", colors["CYBER_CYAN"])
    load_arcade_btn = None
    if arcade_info:
        parts = [p.strip() for p in arcade_info.split("|")]
        start_y = panel_y + 90
        for i, part in enumerate(parts):
            line = fonts["small"].render(part, True, (220, 220, 220))
            screen.blit(line, line.get_rect(center=(arcade_x + panel_w // 2, start_y + i * 34)))

        load_arcade_btn = pygame.Rect(arcade_x + panel_w // 2 - 110, panel_y + panel_h - 58, 220, 44)
        utils["draw_btn"](load_arcade_btn, "LOAD ARCADE SAVE", fonts["small"], mouse_pos, color=colors["CYBER_CYAN"])
    else:
        no_save = fonts["small"].render("No save file found.", True, (100, 100, 120))
        screen.blit(no_save, no_save.get_rect(center=(arcade_x + panel_w // 2, panel_y + panel_h // 2)))

    # --- Free Play Panel ---
    draw_panel_base(free_x, "FREE PLAY MODE", colors["GREEN_NEON"])
    load_freeplay_btn = None
    fp_prev_btn, fp_next_btn = None, None

    if freeplay_saves:
        if selected_fp_index >= len(freeplay_saves):
            selected_fp_index = 0

        curr_save = freeplay_saves[selected_fp_index]
        
        utils["draw_text_c"](f"File: {curr_save['filename']}", fonts["small"], colors["GOLD"], free_x + panel_w // 2, panel_y + 80)
        utils["draw_text_c"](f"Turn: {curr_save['turn']}  |  Score: {curr_save['score']}", fonts["tiny"], (220, 220, 220), free_x + panel_w // 2, panel_y + 115)
        utils["draw_text_c"](f"Profit: {curr_save['profit']:+d}", fonts["tiny"], colors["GREEN_NEON"] if curr_save['profit'] >= 0 else colors["RED"], free_x + panel_w // 2, panel_y + 138)

        if len(freeplay_saves) > 1:
            utils["draw_text_c"](f"({selected_fp_index + 1} of {len(freeplay_saves)})", fonts["tiny"], (140, 140, 170), free_x + panel_w // 2, panel_y + 165)
            fp_prev_btn = pygame.Rect(free_x + 20, panel_y + 152, 40, 28)
            fp_next_btn = pygame.Rect(free_x + panel_w - 60, panel_y + 152, 40, 28)
            utils["draw_btn"](fp_prev_btn, "<", fonts["small"], mouse_pos)
            utils["draw_btn"](fp_next_btn, ">", fonts["small"], mouse_pos)

        load_freeplay_btn = pygame.Rect(free_x + panel_w // 2 - 110, panel_y + panel_h - 58, 220, 44)
        utils["draw_btn"](load_freeplay_btn, "LOAD SAVED FREE PLAY MODE", fonts["small"], mouse_pos, color=colors["GREEN_NEON"])
    else:
        no_save = fonts["small"].render("No save files found.", True, (100, 100, 120))
        screen.blit(no_save, no_save.get_rect(center=(free_x + panel_w // 2, panel_y + panel_h // 2)))

    # --- Navigation Buttons ---
    back_r = pygame.Rect(SW // 2 - 165, panel_y + panel_h + 30, 330, 48)
    utils["draw_btn"](back_r, "BACK TO MAIN MENU", fonts["medium"], mouse_pos)

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
            elif fp_prev_btn and fp_prev_btn.collidepoint(mouse_pos):
                selected_fp_index = (selected_fp_index - 1) % len(freeplay_saves)
            elif fp_next_btn and fp_next_btn.collidepoint(mouse_pos):
                selected_fp_index = (selected_fp_index + 1) % len(freeplay_saves)
            elif load_freeplay_btn and load_freeplay_btn.collidepoint(mouse_pos):
                import free_play_mode
                curr_save = freeplay_saves[selected_fp_index]
                ok, msg = free_play_mode.load_save_file(curr_save["path"], assets)
                if ok:
                    next_state = "freeplay"
                else:
                    assets["system"]["set_msg"](msg)

    return next_state, {'back': back_r, 'load_arcade': load_arcade_btn, 'load_freeplay': load_freeplay_btn}
