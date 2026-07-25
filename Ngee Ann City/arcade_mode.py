import pygame
import random

coins = 16
turn = 1
score = 0
city = []
bldg1 = None
bldg2 = None
selected_bldg = None
placement_mode = False
demolish_mode = False  # track if demolition tool brush is active
coin_warning_shown = False  # tracks whether the 5-coins-left warning has fired for the current dip
coin_warning_popup_active = False  # True while the centre-screen "Understood" popup is waiting to be dismissed
coin_warning_sidebar_active = False  # True once triggered - stays on permanently, does not time out

def init_mode(assets_ref):
    global city
    c = assets_ref["constants"]
    city = [[' '] * c["ARCADE_COLS"] for _ in range(c["ARCADE_ROWS"])]
    new_bldg_pair(c["BUILDINGS"])

def reset():
    global coins, turn, score
    global city, selected_bldg, placement_mode, demolish_mode, coin_warning_shown
    global coin_warning_popup_active, coin_warning_sidebar_active
    coins = 16
    turn = 1
    score = 0
    city = [[' '] * 20 for _ in range(20)]
    selected_bldg = None
    placement_mode = False
    demolish_mode = False
    coin_warning_shown = False
    coin_warning_popup_active = False
    coin_warning_sidebar_active = False
    new_bldg_pair(['R', 'I', 'C', 'O', '*'])

def new_bldg_pair(pool):
    global bldg1, bldg2
    bldg1 = random.choice(pool)
    bldg2 = random.choice(pool)
    while bldg2 == bldg1:
        bldg2 = random.choice(pool)

def is_valid_placement(r, c, rows, cols):
    if city[r][c] != ' ':
        return False, "Cell is already occupied."

    # Allow placement if the city is empty
    if all(cell == ' ' for row in city for cell in row):
        return True, ""

    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr = r + dr
        nc = c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            if city[nr][nc] != ' ':
                return True, ""

    return False, "Must be adjacent to an existing building."

def get_adjacent(r, c):
    neighbours = []
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr = r + dr
        nc = c + dc
        if 0 <= nr < len(city) and 0 <= nc < len(city[0]):
            if city[nr][nc] != ' ':
                neighbours.append(city[nr][nc])
    return neighbours

def calculate_building_score(r, c):
    building = city[r][c]
    neighbours = get_adjacent(r, c)

    if building == "R":
        # Rule: If next to Industry (I), it scores 1 point only
        if "I" in neighbours:
            return 1
        b_score = 0
        for b in neighbours:
            if b == "R" or b == "C":
                b_score += 1
            elif b == "O":
                b_score += 2
        return b_score

    elif building == "I":
        # Rule: Scores 1 point per Industry in the city
        return sum(row.count("I") for row in city)

    elif building == "C":
        # Rule: Scores 1 point per Commercial adjacent to it
        return neighbours.count("C")

    elif building == "O":
        # Rule: Scores 1 point per Park adjacent to it
        return neighbours.count("O")

    elif building == "*":
        # Rule: Scores 1 point per connected road (*) in the same row
        connected = 1
        # Scan left
        col = c - 1
        while col >= 0 and city[r][col] == "*":
            connected += 1
            col -= 1
        # Scan right
        col = c + 1
        while col < len(city[0]) and city[r][col] == "*":
            connected += 1
            col += 1
        return connected

    return 0

def calculate_total_city_coin_income():
    """
    Scans the entire city grid and calculates the total coin income generated 
    by ALL Industry (I) and Commercial (C) buildings based on adjacent Residential (R) buildings.
    """
    total_income = 0
    for r in range(len(city)):
        for c in range(len(city[0])):
            bldg = city[r][c]
            if bldg in ("I", "C"):
                neighbours = get_adjacent(r, c)
                total_income += neighbours.count("R")
    return total_income

def check_coin_warning(assets):
    global coin_warning_shown, coin_warning_popup_active, coin_warning_sidebar_active
    if coins == 5 and not coin_warning_shown:
        coin_warning_shown = True
        coin_warning_popup_active = True
        coin_warning_sidebar_active = True
    elif coins > 5:
        coin_warning_shown = False

def calculate_total_score():
    total = 0
    for r in range(len(city)):
        for c in range(len(city[0])):
            if city[r][c] != ' ':
                total += calculate_building_score(r, c)
    return total

def update(events, mouse_pos, assets):
    global coins, turn, score
    global selected_bldg, placement_mode, demolish_mode
    global bldg1, bldg2, city, coin_warning_shown
    global coin_warning_popup_active, coin_warning_sidebar_active
    next_state = "arcade"
    
    screen = assets["screen"]
    utils = assets["utils"]
    fonts = assets["fonts"]
    colors = assets["colors"]
    layout = assets["layout"]
    const = assets["constants"]

    screen.fill((8, 3, 18))
    utils["draw_header"](" ARCADE MODE ")
    
    s_score = fonts["medium"].render(f"SCORE: {score}", True, colors["GREEN_NEON"])
    s_c = fonts["medium"].render(f"COINS: {coins}", True, colors["GOLD"])
    s_t = fonts["medium"].render(f"TURN: {turn}", True, (255, 255, 255))

    margin = 20
    gap = 24
    t_x = assets["SCREEN_W"] - margin - s_t.get_width()
    c_x = t_x - gap - s_c.get_width()

    screen.blit(s_c, (c_x, layout["HEADER_H"] // 2 - s_c.get_height() // 2))
    screen.blit(s_t, (t_x, layout["HEADER_H"] // 2 - s_t.get_height() // 2))
    screen.blit(s_score, (20, layout["HEADER_H"] // 2 - s_score.get_height() // 2))

    utils["draw_sidebar_panel"]()

    SY = layout["HEADER_H"] + 14
    screen.blit(fonts["small"].render("SELECT A BUILDING:", True, colors["CYBER_CYAN"]), (10, SY))
    SY += 24

    btn1 = pygame.Rect(10, SY, layout["SIDEBAR_W"] - 20, 50)
    btn2 = pygame.Rect(10, SY + 62, layout["SIDEBAR_W"] - 20, 50)

    for btn, bldg, key in ((btn1, bldg1, "1"), (btn2, bldg2, "2")):
        active = (selected_bldg == bldg)
        hover = btn.collidepoint(mouse_pos) or active
        bc = colors["BUILDING_COLORS"].get(bldg, (255, 255, 255))
        pygame.draw.rect(screen, colors["CYBER_CYAN"] if hover else (40, 12, 72), btn, border_radius=4)
        pygame.draw.rect(screen, bc, btn, 2, border_radius=4)
        utils["draw_text_c"](f"[{key}]  {bldg}", fonts["large"], (10, 10, 10) if hover else (255, 255, 255), btn.centerx, btn.centery)

    SY += 128
    if placement_mode and selected_bldg:
        utils["draw_text_c"](f"Placing: {selected_bldg}", fonts["small"], colors["GREEN_NEON"], layout["SIDEBAR_W"] // 2, SY)
        utils["draw_text_c"]("Click the grid to place", fonts["tiny"], colors["GREEN_NEON"], layout["SIDEBAR_W"] // 2, SY + 18)
    elif demolish_mode:
        utils["draw_text_c"]("Demolition Mode Active", fonts["small"], (255, 100, 100), layout["SIDEBAR_W"] // 2, SY)
        utils["draw_text_c"]("Click a building to remove", fonts["tiny"], (255, 100, 100), layout["SIDEBAR_W"] // 2, SY + 18)
    elif selected_bldg:
        utils["draw_text_c"](f"Selected: {selected_bldg}", fonts["small"], colors["GOLD"], layout["SIDEBAR_W"] // 2, SY)
    else:
        utils["draw_text_c"]("Pick a building above", fonts["tiny"], (120, 120, 155), layout["SIDEBAR_W"] // 2, SY)

    utils["draw_legend"](10, SY + 42)

    msg, m_timer = assets["system"]["get_msg"]()
    if m_timer > 0:
        is_err = any(w in msg for w in ("occupied", "adjacent", "Invalid", "empty"))
        col = (255, 80, 80) if is_err else colors["GREEN_NEON"]

        msg_y = SY + 42 + 14 + 5 * 13 + 12
        max_w = layout["SIDEBAR_W"] - 16
        words, lines, cur = msg.split(), [], ""
        for w in words:
            trial = f"{cur} {w}".strip()
            if fonts["small"].size(trial)[0] <= max_w:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)

        for i, line in enumerate(lines):
            s_msg = fonts["small"].render(line, True, col)
            screen.blit(s_msg, (8, msg_y + i * 18))

    if coin_warning_sidebar_active:
        warn_box = pygame.Rect(10, assets["SCREEN_H"] - 214, layout["SIDEBAR_W"] - 20, 44)
        pygame.draw.rect(screen, (60, 15, 15), warn_box, border_radius=4)
        pygame.draw.rect(screen, (255, 90, 90), warn_box, 2, border_radius=4)
        utils["draw_text_c"]("WARNING:", fonts["tiny"], (255, 130, 130), warn_box.centerx, warn_box.y + 14)
        utils["draw_text_c"]("Only 5 coins left!", fonts["tiny"], (255, 130, 130), warn_box.centerx, warn_box.y + 30)

    demo_r = pygame.Rect(10, assets["SCREEN_H"] - 165, layout["SIDEBAR_W"] - 20, 38)
    demo_bg = (130, 40, 40) if demolish_mode else (180, 60, 60)
    utils["draw_btn"](demo_r, "[D] DEMOLISH", fonts["small"], mouse_pos, color=demo_bg)

    cancel_r = pygame.Rect(10, assets["SCREEN_H"] - 118, layout["SIDEBAR_W"] - 20, 40)
    menu_r = pygame.Rect(10, assets["SCREEN_H"] - 68, layout["SIDEBAR_W"] - 20, 40)
    utils["draw_btn"](cancel_r, "[ESC]  CANCEL", fonts["small"], mouse_pos)
    utils["draw_btn"](menu_r, "[Q]  MAIN MENU", fonts["small"], mouse_pos)

    # Core Matrix Grid Renderer 
    for r in range(const["ARCADE_ROWS"]):
        for c in range(const["ARCADE_COLS"]):
            cr = pygame.Rect(layout["ARCADE_GRID_X"] + c * layout["ARCADE_CELL"], layout["ARCADE_GRID_Y"] + r * layout["ARCADE_CELL"], layout["ARCADE_CELL"], layout["ARCADE_CELL"])
            is_hover = cr.collidepoint(mouse_pos) and (placement_mode or demolish_mode)
            bg = colors["CELL_HOVER"] if is_hover else (colors["CELL_OCCUPIED"] if city[r][c] != ' ' else colors["CELL_EMPTY"])
            pygame.draw.rect(screen, bg, cr)
            pygame.draw.rect(screen, colors["GRID_LINE"], cr, 1)
            if city[r][c] != ' ':
                bc = colors["BUILDING_COLORS"].get(city[r][c], (255, 255, 255))
                s_char = fonts["small"].render(city[r][c], True, bc)
                screen.blit(s_char, s_char.get_rect(center=cr.center))

    utils["draw_grid_labels"](const["ARCADE_ROWS"], const["ARCADE_COLS"], layout["ARCADE_GRID_X"], layout["ARCADE_GRID_Y"], layout["ARCADE_CELL"])

    understood_r = None
    if coin_warning_popup_active:
        dim = pygame.Surface((assets["SCREEN_W"], assets["SCREEN_H"]), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 165))
        screen.blit(dim, (0, 0))

        box_w, box_h = 480, 210
        box_rect = pygame.Rect((assets["SCREEN_W"] - box_w) // 2, (assets["SCREEN_H"] - box_h) // 2, box_w, box_h)
        pygame.draw.rect(screen, (20, 5, 35), box_rect, border_radius=10)
        pygame.draw.rect(screen, colors["GOLD"], box_rect, 3, border_radius=10)

        utils["draw_text_c"]("⚠  LOW COINS WARNING", fonts["medium"], colors["GOLD"], box_rect.centerx, box_rect.y + 45)
        utils["draw_text_c"]("You only have 5 coins left!", fonts["small"], (255, 255, 255), box_rect.centerx, box_rect.y + 95)
        utils["draw_text_c"]("Spend wisely to avoid running out.", fonts["tiny"], (200, 200, 200), box_rect.centerx, box_rect.y + 120)

        understood_r = pygame.Rect(box_rect.centerx - 90, box_rect.bottom - 55, 180, 42)
        utils["draw_btn"](understood_r, "UNDERSTOOD", fonts["small"], mouse_pos, color=colors["GOLD"])

    # Event Interface Router
    for event in events:
        if coin_warning_popup_active:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and understood_r and understood_r.collidepoint(mouse_pos):
                coin_warning_popup_active = False
            continue

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q: next_state = "main_menu"
            elif event.key == pygame.K_ESCAPE: selected_bldg = None; placement_mode = False; demolish_mode = False
            elif event.key == pygame.K_1: selected_bldg = bldg1; placement_mode = True; demolish_mode = False
            elif event.key == pygame.K_2: selected_bldg = bldg2; placement_mode = True; demolish_mode = False
            elif event.key == pygame.K_d: selected_bldg = None; placement_mode = False; demolish_mode = not demolish_mode
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if btn1.collidepoint(mouse_pos): selected_bldg = bldg1; placement_mode = True; demolish_mode = False
            elif btn2.collidepoint(mouse_pos): selected_bldg = bldg2; placement_mode = True; demolish_mode = False
            elif cancel_r.collidepoint(mouse_pos): selected_bldg = None; placement_mode = False; demolish_mode = False
            elif menu_r.collidepoint(mouse_pos): next_state = "main_menu"
            elif demo_r.collidepoint(mouse_pos):
                demolish_mode = not demolish_mode
                selected_bldg = None
                placement_mode = False
            elif placement_mode or demolish_mode:
                cell = utils["grid_cell_at"](*mouse_pos, layout["ARCADE_GRID_X"], layout["ARCADE_GRID_Y"], layout["ARCADE_CELL"], const["ARCADE_ROWS"], const["ARCADE_COLS"])
                if cell:
                    r, c = cell
                    
                    # --- Demolition Action Segment ---
                    if demolish_mode:
                        if city[r][c] != ' ':
                            if coins >= 1:
                                city[r][c] = ' '
                                score = calculate_total_score()
                                
                                # Demolition costs 1 coin + collect turn income from city
                                income = calculate_total_city_coin_income()
                                coins = coins - 1 + income
                                
                                turn += 1
                                demolish_mode = False
                                assets["system"]["set_msg"]("Building demolished!")
                                check_coin_warning(assets)
                                
                                if coins <= 0:
                                    next_state = "game_over"
                            else:
                                assets["system"]["set_msg"]("Cannot afford demolition! (Requires 1 Coin)")
                        else:
                            assets["system"]["set_msg"]("Cell is already empty!")
                    
                    # --- Regular Placement Action Segment ---
                    elif placement_mode:
                        ok, reason = is_valid_placement(r, c, const["ARCADE_ROWS"], const["ARCADE_COLS"])
                        if ok:
                            city[r][c] = selected_bldg
                            score = calculate_total_score()
                            
                            # Deduction for placement (-1 coin) + collect turn income from city
                            income = calculate_total_city_coin_income()
                            coins = coins - 1 + income
                            
                            turn += 1
                            selected_bldg = None
                            placement_mode = False
                            new_bldg_pair(const["BUILDINGS"])
                            
                            if income > 0:
                                assets["system"]["set_msg"](f"Building placed! (+{income} coin(s) generated)")
                            else:
                                assets["system"]["set_msg"]("Building placed!")

                            check_coin_warning(assets)
                            
                            if all(cell != ' ' for row in city for cell in row) or coins <= 0:
                                next_state = "game_over"
                        else:
                            assets["system"]["set_msg"](reason)

    return next_state, {
        'btn1': btn1, 
        'btn2': btn2, 
        'cancel': cancel_r, 
        'menu': menu_r, 
        'demolish': demo_r,
        'score': score  # To show the current score
    }
