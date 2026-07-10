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


def init_mode(assets_ref):
    global city
    c = assets_ref["constants"]
    city = [[' '] * c["ARCADE_COLS"] for _ in range(c["ARCADE_ROWS"])]
    new_bldg_pair(c["BUILDINGS"])

def reset():
    global coins, turn, score
    global city, selected_bldg, placement_mode
    coins = 16
    turn = 1
    score = 0
    city = [[' '] * 20 for _ in range(20)]
    selected_bldg = None
    placement_mode = False
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
    if turn == 1:
        return True, ""
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and city[nr][nc] != ' ':
            return True, ""
    return False, "Must be adjacent to an existing building."

# Jun Wei NACG-22 
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

        if "I" in neighbours:
            return 1

        score = 0

        for b in neighbours:

            if b == "R":
                score += 1

            elif b == "C":
                score += 1

            elif b == "O":
                score += 2

        return score

    elif building == "I":
        return sum(row.count("I") for row in city)

    elif building == "C":
        return neighbours.count("C")

    elif building == "O":
        return neighbours.count("O")

    elif building == "*":

        connected = 1

        # Check left
        col = c - 1
        while col >= 0 and city[r][col] == "*":
            connected += 1
            col -= 1

        # Check right
        col = c + 1
        while col < len(city[0]) and city[r][col] == "*":
            connected += 1
            col += 1

        return connected


def calculate_total_score():

    total = 0

    for r in range(len(city)):
        for c in range(len(city[0])):

            if city[r][c] != ' ':
                building_score = calculate_building_score(r, c)
                print(f"{city[r][c]} at ({r},{c}) = {building_score}")
                total += building_score

    print("Total =", total)
    return total
# END

def update(events, mouse_pos, assets):
    global coins, turn, score
    global selected_bldg, placement_mode
    global bldg1, bldg2, city
    next_state = "arcade"
    
    screen = assets["screen"]
    utils = assets["utils"]
    fonts = assets["fonts"]
    colors = assets["colors"]
    layout = assets["layout"]
    const = assets["constants"]

    screen.fill((8, 3, 18))
    utils["draw_header"]("◆  ARCADE MODE  ◆")
    
    s_score = fonts["medium"].render(f"SCORE: {score}", True, colors["GREEN_NEON"])
    s_c = fonts["medium"].render(f"COINS: {coins}", True, colors["GOLD"])
    s_t = fonts["medium"].render(f"TURN: {turn}", True, (255,255,255))

    margin = 20
    gap    = 24
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
    elif selected_bldg:
        utils["draw_text_c"](f"Selected: {selected_bldg}", fonts["small"], colors["GOLD"], layout["SIDEBAR_W"] // 2, SY)
    else:
        utils["draw_text_c"]("Pick a building above", fonts["tiny"], (120, 120, 155), layout["SIDEBAR_W"] // 2, SY)

    utils["draw_legend"](10, SY + 42)

    msg, m_timer = assets["system"]["get_msg"]()
    if m_timer > 0:
        is_err = any(w in msg for w in ("occupied", "adjacent", "Invalid"))
        col = (255, 80, 80) if is_err else colors["GREEN_NEON"]

        msg_y = SY + 42 + 14 + 5 * 13 + 12   # below the 5-item legend
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

    demo_r = pygame.Rect(10, assets["SCREEN_H"] - 165, layout["SIDEBAR_W"] - 20, 38)
    utils["draw_btn"](demo_r, "DEMOLISH  [stub]", fonts["tiny"], mouse_pos, color=(180, 60, 60))

    cancel_r = pygame.Rect(10, assets["SCREEN_H"] - 118, layout["SIDEBAR_W"] - 20, 40)
    menu_r = pygame.Rect(10, assets["SCREEN_H"] - 68, layout["SIDEBAR_W"] - 20, 40)
    utils["draw_btn"](cancel_r, "[ESC]  CANCEL", fonts["small"], mouse_pos)
    utils["draw_btn"](menu_r, "[Q]  MAIN MENU", fonts["small"], mouse_pos)

    # Core Matrix Grid Renderer 
    for r in range(const["ARCADE_ROWS"]):
        for c in range(const["ARCADE_COLS"]):
            cr = pygame.Rect(layout["ARCADE_GRID_X"] + c * layout["ARCADE_CELL"], layout["ARCADE_GRID_Y"] + r * layout["ARCADE_CELL"], layout["ARCADE_CELL"], layout["ARCADE_CELL"])
            is_hover = cr.collidepoint(mouse_pos) and placement_mode
            bg = colors["CELL_HOVER"] if is_hover else (colors["CELL_OCCUPIED"] if city[r][c] != ' ' else colors["CELL_EMPTY"])
            pygame.draw.rect(screen, bg, cr)
            pygame.draw.rect(screen, colors["GRID_LINE"], cr, 1)
            if city[r][c] != ' ':
                bc = colors["BUILDING_COLORS"].get(city[r][c], (255, 255, 255))
                s_char = fonts["small"].render(city[r][c], True, bc)
                screen.blit(s_char, s_char.get_rect(center=cr.center))

    utils["draw_grid_labels"](const["ARCADE_ROWS"], const["ARCADE_COLS"], layout["ARCADE_GRID_X"], layout["ARCADE_GRID_Y"], layout["ARCADE_CELL"])

    # Event Interface Router
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q: next_state = "main_menu"
            elif event.key == pygame.K_ESCAPE: selected_bldg = None; placement_mode = False
            elif event.key == pygame.K_1: selected_bldg = bldg1; placement_mode = True
            elif event.key == pygame.K_2: selected_bldg = bldg2; placement_mode = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if btn1.collidepoint(mouse_pos): selected_bldg = bldg1; placement_mode = True
            elif btn2.collidepoint(mouse_pos): selected_bldg = bldg2; placement_mode = True
            elif cancel_r.collidepoint(mouse_pos): selected_bldg = None; placement_mode = False
            elif menu_r.collidepoint(mouse_pos): next_state = "main_menu"
            elif placement_mode:
                cell = utils["grid_cell_at"](*mouse_pos, layout["ARCADE_GRID_X"], layout["ARCADE_GRID_Y"], layout["ARCADE_CELL"], const["ARCADE_ROWS"], const["ARCADE_COLS"])
                if cell:
                    r, c = cell
                    ok, reason = is_valid_placement(r, c, const["ARCADE_ROWS"], const["ARCADE_COLS"])
                    if ok:

                        city[r][c] = selected_bldg
                        score = calculate_total_score()
                        print("Placed:", selected_bldg)
                        print("Score:", score)

                        coins -= 1
                        turn += 1
                        selected_bldg = None
                        placement_mode = False

                        new_bldg_pair(const["BUILDINGS"])
                        assets["system"]["set_msg"]("Building placed!")
                        if all(cell != ' ' for row in city for cell in row) or coins <= 0:
                            next_state = "game_over"
                    else:
                        assets["system"]["set_msg"](reason)

    return next_state, {'btn1': btn1, 'btn2': btn2, 'cancel': cancel_r, 'menu': menu_r, 'demolish': demo_r}
