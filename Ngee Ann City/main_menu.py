import pygame
import sys

def update(events, mouse_pos, assets):
    next_state = "main_menu"
    utils = assets["utils"]
    fonts = assets["fonts"]
    colors = assets["colors"]
    
    utils["draw_bg_skyline"]()

    # Dark overlay screen surface mask
    ov = pygame.Surface((assets["SCREEN_W"], assets["SCREEN_H"]), pygame.SRCALPHA)
    ov.fill((8, 15, 40, 110)) 
    assets["screen"].blit(ov, (0, 0))

    utils["draw_text_c"]("NGEE ANN CITY", fonts["title"], (255, 255, 255), assets["SCREEN_W"] // 2, 78)
    utils["draw_text_c"]("B  U  I  L  D  E  R", fonts["medium"], (255, 255, 255), assets["SCREEN_W"] // 2, 128)
    pygame.draw.line(assets["screen"], (255, 255, 255), (190, 154), (assets["SCREEN_W"] - 190, 154), 1)

    items = [
        ("1", "1)  START NEW ARCADE GAME"),
        ("2", "2)  START NEW FREE PLAY GAME"),
        ("3", "3)  LOAD SAVED GAME"),
        ("4", "4)  DISPLAY HIGH SCORES"),
        ("5", "5)  EXIT GAME"),
    ]
    bw, bh = 350, 47
    bx = assets["SCREEN_W"] // 2 - bw // 2
    buttons = {}
    
    for i, (key, lbl) in enumerate(items):
        r = pygame.Rect(bx, 172 + i * 62, bw, bh)
        utils["draw_btn"](r, lbl, fonts["small"], mouse_pos)
        buttons[key] = r

    utils["draw_text_c"]("Press 1–5 or click to select", fonts["tiny"], (100, 100, 130), assets["SCREEN_W"] // 2, assets["SCREEN_H"] - 28)

    # Keyboard & Click Input Routing Interface
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1: import arcade_mode; arcade_mode.reset(); next_state = "arcade"
            elif event.key == pygame.K_2: import free_play_mode; free_play_mode.reset(assets); next_state = "freeplay"
            elif event.key == pygame.K_3: next_state = "load_game"
            elif event.key == pygame.K_4: next_state = "high_scores"
            elif event.key == pygame.K_5:
                pygame.quit()
                sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if buttons['1'].collidepoint(mouse_pos): import arcade_mode; arcade_mode.reset(); next_state = "arcade"
            elif buttons['2'].collidepoint(mouse_pos): import free_play_mode; free_play_mode.reset(assets); next_state = "freeplay"
            elif buttons['3'].collidepoint(mouse_pos): next_state = "load_game"
            elif buttons['4'].collidepoint(mouse_pos): next_state = "high_scores"
            elif buttons['5'].collidepoint(mouse_pos):
                pygame.quit()
                sys.exit()

    return next_state, buttons
