import pygame
import random
import save_manager

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
save_popup_active = False  # True while the save result popup awaits dismissal
save_popup_ok = False      # True = saved successfully, False = failed
save_popup_msg = ""        # message to display in the save popup
paused = False             # True when game is paused (pause button / ESC)
end_game_confirm_active = False  # True while the "End Game" confirmation dialog is shown

# ── Murray — Save-as filename flow ─────────────────────────────────────────
# save_dialog_active: filename entry box is open, awaiting a name to save under
# save_filename_input: the text the player has typed so far
# save_dialog_error: inline validation message (e.g. empty filename)
# overwrite_confirm_active: a save with this name already exists, confirm first
# pending_filename: the filename waiting on the overwrite confirmation
# save_dialog_return_to_pause: whether cancelling the flow should reopen the pause menu
save_dialog_active = False
save_filename_input = ""
save_dialog_error = ""
overwrite_confirm_active = False
pending_filename = ""
save_dialog_return_to_pause = False

# Characters not allowed in filenames across common filesystems
_FILENAME_BLOCKLIST = set('\\/:*?"<>|')


# ── Murray — Restore full game state from save file ───────────────────────────
# Reads arcade_save.json and repopulates all module globals so the player
# can resume exactly where they left off, including board dimensions,
# building layout, score, coins, and warning states.
def load_save():
    """
    Restore module globals from the arcade save file.
    Returns (True, message) on success, (False, message) on failure.
    """
    global coins, turn, score, city, bldg1, bldg2
    global coin_warning_shown, coin_warning_popup_active, coin_warning_sidebar_active
    global selected_bldg, placement_mode, demolish_mode, paused, end_game_confirm_active

    data, err = save_manager.load_arcade()
    if data is None:
        return False, err

    coins  = data["coins"]
    turn   = data["turn"]
    score  = data["score"]
    city   = data["city"]
    bldg1  = data["bldg1"]
    bldg2  = data["bldg2"]
    coin_warning_shown           = data.get("coin_warning_shown", False)
    coin_warning_sidebar_active  = data.get("coin_warning_sidebar_active", False)
    coin_warning_popup_active    = False  # never restore a blocking popup
    selected_bldg  = None
    placement_mode = False
    demolish_mode  = False
    paused             = False
    end_game_confirm_active = False

    # Restore board dimensions so the grid renders at the correct size
    saved_rows = data.get("rows", len(city))
    saved_cols = data.get("cols", len(city[0]) if city else 20)
    # Ensure the city grid matches the saved dimensions (guard against corrupt data)
    if len(city) != saved_rows or (city and len(city[0]) != saved_cols):
        city = [[' '] * saved_cols for _ in range(saved_rows)]

    return True, "Arcade game loaded!"


def load_save_from_file(filepath):
    """
    Load arcade game state from a specific file path.
    Returns (True, message) on success, (False, message) on failure.
    """
    global coins, turn, score, city, bldg1, bldg2
    global coin_warning_shown, coin_warning_popup_active, coin_warning_sidebar_active
    global selected_bldg, placement_mode, demolish_mode, paused, end_game_confirm_active

    data, err = save_manager.load_arcade_named(filepath)
    if data is None:
        return False, err

    coins  = data["coins"]
    turn   = data["turn"]
    score  = data["score"]
    city   = data["city"]
    bldg1  = data["bldg1"]
    bldg2  = data["bldg2"]
    coin_warning_shown           = data.get("coin_warning_shown", False)
    coin_warning_sidebar_active  = data.get("coin_warning_sidebar_active", False)
    coin_warning_popup_active    = False  # never restore a blocking popup
    selected_bldg  = None
    placement_mode = False
    demolish_mode  = False
    paused             = False
    end_game_confirm_active = False

    # Restore board dimensions so the grid renders at the correct size
    saved_rows = data.get("rows", len(city))
    saved_cols = data.get("cols", len(city[0]) if city else 20)
    # Ensure the city grid matches the saved dimensions (guard against corrupt data)
    if len(city) != saved_rows or (city and len(city[0]) != saved_cols):
        city = [[' '] * saved_cols for _ in range(saved_rows)]

    return True, "Arcade game loaded!"


def init_mode(assets_ref):
    global city
    c = assets_ref["constants"]
    city = [[' '] * c["ARCADE_COLS"] for _ in range(c["ARCADE_ROWS"])]
    new_bldg_pair(c["BUILDINGS"])

def reset():
    global coins, turn, score
    global city, selected_bldg, placement_mode, demolish_mode, coin_warning_shown
    global coin_warning_popup_active, coin_warning_sidebar_active
    global paused, end_game_confirm_active
    global save_dialog_active, save_filename_input, save_dialog_error
    global overwrite_confirm_active, pending_filename, save_dialog_return_to_pause
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
    save_popup_active = False
    save_popup_ok = False
    save_popup_msg = ""
    paused = False
    end_game_confirm_active = False
    save_dialog_active = False
    save_filename_input = ""
    save_dialog_error = ""
    overwrite_confirm_active = False
    pending_filename = ""
    save_dialog_return_to_pause = False
    new_bldg_pair(['R', 'I', 'C', 'O', '*'])

# ── Murray — Random building pair offered to player each turn ─────────────────
# Picks two different buildings at random from the pool and assigns them to
# bldg1 and bldg2. The while loop ensures the two options are never identical,
# so the player always has a meaningful choice.
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
    if coins <= 5 and not coin_warning_shown:
        coin_warning_shown = True
        coin_warning_popup_active = True
        coin_warning_sidebar_active = True
    elif coins > 5:
        coin_warning_shown = False
        coin_warning_sidebar_active = False

def calculate_total_score():
    total = 0
    for r in range(len(city)):
        for c in range(len(city[0])):
            if city[r][c] != ' ':
                total += calculate_building_score(r, c)
    return total


# ── Murray — Save-as flow helpers ──────────────────────────────────────────
def _open_save_dialog(return_to_pause=False):
    """Open the filename entry dialog, closing the pause menu first if open."""
    global save_dialog_active, save_filename_input, save_dialog_error
    global save_dialog_return_to_pause, paused
    save_filename_input = ""
    save_dialog_error = ""
    save_dialog_return_to_pause = return_to_pause
    save_dialog_active = True
    paused = False


def _commit_save(filename):
    """Actually write the save file and pop up the result."""
    global save_popup_ok, save_popup_msg, save_popup_active
    global save_dialog_active, overwrite_confirm_active, pending_filename
    ok, msg = save_manager.save_arcade_named(
        filename, coins, turn, score, city, bldg1, bldg2,
        coin_warning_shown, coin_warning_sidebar_active
    )
    save_popup_ok = ok
    save_popup_msg = msg
    save_popup_active = True
    save_dialog_active = False
    overwrite_confirm_active = False
    pending_filename = ""


def _attempt_save():
    """
    Validate the typed filename and either save immediately or, if a save
    with that name already exists, ask the player to confirm overwriting it.
    """
    global save_dialog_error, save_dialog_active, overwrite_confirm_active, pending_filename
    name = save_filename_input.strip()
    if not name:
        save_dialog_error = "Filename cannot be empty."
        return

    if save_manager.arcade_named_save_exists(name):
        pending_filename = name
        overwrite_confirm_active = True
        save_dialog_active = False
    else:
        _commit_save(name)


def update(events, mouse_pos, assets):
    global coins, turn, score
    global selected_bldg, placement_mode, demolish_mode
    global bldg1, bldg2, city, coin_warning_shown
    global coin_warning_popup_active, coin_warning_sidebar_active
    global save_popup_active, save_popup_ok, save_popup_msg
    global paused, end_game_confirm_active
    global save_dialog_active, save_filename_input, save_dialog_error
    global overwrite_confirm_active, pending_filename, save_dialog_return_to_pause
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

    # ── Murray — Sidebar: two randomly offered buildings for player to choose ──
    # Renders btn1 and btn2 using the current bldg1/bldg2 values. The player
    # clicks (or presses 1/2) to select one, which enters placement mode so
    # they can click a valid grid cell to place it.
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

    pause_r    = pygame.Rect(10, assets["SCREEN_H"] - 190, layout["SIDEBAR_W"] - 20, 38)
    demo_r     = pygame.Rect(10, assets["SCREEN_H"] - 145, layout["SIDEBAR_W"] - 20, 38)
    save_r     = pygame.Rect(10, assets["SCREEN_H"] - 100, layout["SIDEBAR_W"] - 20, 38)
    menu_r     = pygame.Rect(10, assets["SCREEN_H"] - 55,  layout["SIDEBAR_W"] - 20, 38)

    demo_bg = (130, 40, 40) if demolish_mode else (180, 60, 60)
    
    utils["draw_btn"](pause_r,    "[ESC]  PAUSE",  fonts["small"], mouse_pos)
    utils["draw_btn"](demo_r,     "[D]  DEMOLISH",  fonts["small"], mouse_pos, color=demo_bg)
    utils["draw_btn"](save_r,     "[S]  SAVE GAME",  fonts["small"], mouse_pos, color=colors["CYBER_CYAN"])
    utils["draw_btn"](menu_r,     "[Q]  MAIN MENU",  fonts["small"], mouse_pos, color=(220, 50, 50))

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

    # ── Murray — Save-as filename entry dialog ─────────────────────────────────
    # Lets the player type a custom filename before saving. Shows an inline
    # error if they try to confirm with an empty name.
    save_confirm_r = None
    save_cancel_r = None
    if save_dialog_active:
        dim = pygame.Surface((assets["SCREEN_W"], assets["SCREEN_H"]), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 165))
        screen.blit(dim, (0, 0))

        box_w, box_h = 480, 230
        box_rect = pygame.Rect((assets["SCREEN_W"] - box_w) // 2,
                               (assets["SCREEN_H"] - box_h) // 2, box_w, box_h)
        pygame.draw.rect(screen, (20, 5, 35), box_rect, border_radius=10)
        pygame.draw.rect(screen, colors["CYBER_CYAN"], box_rect, 3, border_radius=10)

        utils["draw_text_c"]("SAVE GAME", fonts["medium"], colors["CYBER_CYAN"],
                             box_rect.centerx, box_rect.y + 38)
        utils["draw_text_c"]("Enter a filename:", fonts["tiny"], (200, 200, 200),
                             box_rect.centerx, box_rect.y + 70)

        input_r = pygame.Rect(box_rect.x + 30, box_rect.y + 88, box_w - 60, 40)
        pygame.draw.rect(screen, (10, 10, 20), input_r, border_radius=4)
        pygame.draw.rect(screen, colors["GOLD"] if save_dialog_error else colors["CYBER_CYAN"], input_r, 2, border_radius=4)
        display_text = save_filename_input if save_filename_input else ""
        cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
        s_input = fonts["small"].render(display_text + cursor, True, (255, 255, 255))
        screen.blit(s_input, (input_r.x + 8, input_r.centery - s_input.get_height() // 2))

        if save_dialog_error:
            utils["draw_text_c"](save_dialog_error, fonts["tiny"], (255, 100, 100),
                                 box_rect.centerx, input_r.bottom + 16)

        save_confirm_r = pygame.Rect(box_rect.centerx - 160, box_rect.bottom - 55, 140, 42)
        save_cancel_r  = pygame.Rect(box_rect.centerx + 20,  box_rect.bottom - 55, 140, 42)
        utils["draw_btn"](save_confirm_r, "SAVE", fonts["small"], mouse_pos, color=colors["GREEN_NEON"])
        utils["draw_btn"](save_cancel_r,  "CANCEL", fonts["small"], mouse_pos, color=colors["CYBER_CYAN"])

    # ── Murray — Overwrite confirmation ─────────────────────────────────────────
    # Shown when the chosen filename already has a save on disk.
    overwrite_yes_r = None
    overwrite_no_r = None
    if overwrite_confirm_active:
        dim = pygame.Surface((assets["SCREEN_W"], assets["SCREEN_H"]), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 175))
        screen.blit(dim, (0, 0))

        box_w, box_h = 480, 210
        box_rect = pygame.Rect((assets["SCREEN_W"] - box_w) // 2,
                               (assets["SCREEN_H"] - box_h) // 2, box_w, box_h)
        pygame.draw.rect(screen, (30, 20, 5), box_rect, border_radius=10)
        pygame.draw.rect(screen, colors["GOLD"], box_rect, 3, border_radius=10)

        utils["draw_text_c"]("OVERWRITE SAVE?", fonts["medium"], colors["GOLD"],
                             box_rect.centerx, box_rect.y + 42)
        utils["draw_text_c"](f'A save named "{pending_filename}" already exists.',
                             fonts["small"], (220, 220, 220), box_rect.centerx, box_rect.y + 90)
        utils["draw_text_c"]("This will replace it.", fonts["tiny"], (180, 180, 180),
                             box_rect.centerx, box_rect.y + 114)

        overwrite_yes_r = pygame.Rect(box_rect.centerx - 160, box_rect.bottom - 55, 140, 42)
        overwrite_no_r  = pygame.Rect(box_rect.centerx + 20,  box_rect.bottom - 55, 140, 42)
        utils["draw_btn"](overwrite_yes_r, "OVERWRITE", fonts["small"], mouse_pos, color=colors["RED"] if "RED" in colors else (220, 50, 50))
        utils["draw_btn"](overwrite_no_r,  "CANCEL",     fonts["small"], mouse_pos, color=colors["CYBER_CYAN"])

    # ── Murray — Save result popup ─────────────────────────────────────────────
    # Blocks all input until dismissed. Shows green border on success,
    # red border on failure, with the exact save/error message.
    save_ok_r = None
    if save_popup_active:
        dim = pygame.Surface((assets["SCREEN_W"], assets["SCREEN_H"]), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 165))
        screen.blit(dim, (0, 0))

        box_w, box_h = 480, 200
        box_rect = pygame.Rect((assets["SCREEN_W"] - box_w) // 2,
                               (assets["SCREEN_H"] - box_h) // 2, box_w, box_h)
        border_col = (0, 200, 100) if save_popup_ok else (220, 50, 50)
        title_col  = (0, 220, 120) if save_popup_ok else (255, 80, 80)
        title_text = "GAME SAVED" if save_popup_ok else "SAVE FAILED"

        pygame.draw.rect(screen, (20, 5, 35), box_rect, border_radius=10)
        pygame.draw.rect(screen, border_col, box_rect, 3, border_radius=10)

        utils["draw_text_c"](title_text, fonts["medium"], title_col,
                             box_rect.centerx, box_rect.y + 50)
        utils["draw_text_c"](save_popup_msg, fonts["small"], (220, 220, 220),
                             box_rect.centerx, box_rect.y + 100)

        save_ok_r = pygame.Rect(box_rect.centerx - 80, box_rect.bottom - 58, 160, 40)
        utils["draw_btn"](save_ok_r, "OK", fonts["medium"], mouse_pos, color=border_col)

    # ── Pause Menu Overlay ────────────────────────────────────────────────────
    # Displayed when the player opens Pause. Shows Resume, Save Game, End Game,
    # and a reminder that save files are not touched by ending the session.
    pause_resume_r   = None
    pause_save_r     = None
    pause_endgame_r  = None

    if paused and not end_game_confirm_active:
        # Dim the game behind the menu
        dim = pygame.Surface((assets["SCREEN_W"], assets["SCREEN_H"]), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 170))
        screen.blit(dim, (0, 0))

        box_w, box_h = 420, 320
        box_rect = pygame.Rect((assets["SCREEN_W"] - box_w) // 2,
                               (assets["SCREEN_H"] - box_h) // 2, box_w, box_h)
        pygame.draw.rect(screen, (20, 5, 40), box_rect, border_radius=10)
        pygame.draw.rect(screen, colors["CYBER_CYAN"], box_rect, 3, border_radius=10)

        utils["draw_text_c"]("GAME PAUSED", fonts["medium"],
                             colors["CYBER_CYAN"], box_rect.centerx, box_rect.y + 42)

        pause_resume_r  = pygame.Rect(box_rect.centerx - 150, box_rect.y + 88, 300, 46)
        pause_save_r    = pygame.Rect(box_rect.centerx - 150, box_rect.y + 148, 300, 46)
        pause_endgame_r = pygame.Rect(box_rect.centerx - 150, box_rect.y + 208, 300, 46)

        utils["draw_btn"](pause_resume_r,  "RESUME GAME",  fonts["small"], mouse_pos,
                          color=colors["CYBER_CYAN"])
        utils["draw_btn"](pause_save_r,    "SAVE GAME",    fonts["small"], mouse_pos,
                          color=colors["GOLD"])
        utils["draw_btn"](pause_endgame_r, "END GAME",     fonts["small"], mouse_pos,
                          color=colors["RED"])

        hint = fonts["tiny"].render("[ESC] Resume", True, (80, 80, 110))
        screen.blit(hint, hint.get_rect(center=(box_rect.centerx, box_rect.bottom - 18)))

    # ── End Game Confirmation Dialog ──────────────────────────────────────────
    # Prevents accidental progress loss: player must explicitly confirm before
    # the session is cleared. Cancelling returns seamlessly to the paused game.
    confirm_yes_r = None
    confirm_no_r  = None

    if end_game_confirm_active:
        dim = pygame.Surface((assets["SCREEN_W"], assets["SCREEN_H"]), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 185))
        screen.blit(dim, (0, 0))

        box_w, box_h = 500, 240
        box_rect = pygame.Rect((assets["SCREEN_W"] - box_w) // 2,
                               (assets["SCREEN_H"] - box_h) // 2, box_w, box_h)
        pygame.draw.rect(screen, (25, 5, 10), box_rect, border_radius=10)
        pygame.draw.rect(screen, colors["RED"], box_rect, 3, border_radius=10)

        utils["draw_text_c"]("END GAME?", fonts["medium"],
                             colors["RED"], box_rect.centerx, box_rect.y + 44)
        utils["draw_text_c"]("Your current progress will be lost.",
                             fonts["small"], (220, 220, 220),
                             box_rect.centerx, box_rect.y + 94)
        utils["draw_text_c"]("(Existing save files will not be affected.)",
                             fonts["tiny"], (140, 140, 160),
                             box_rect.centerx, box_rect.y + 122)

        confirm_yes_r = pygame.Rect(box_rect.centerx - 160, box_rect.bottom - 68, 140, 44)
        confirm_no_r  = pygame.Rect(box_rect.centerx + 20,  box_rect.bottom - 68, 140, 44)

        utils["draw_btn"](confirm_yes_r, "YES, END", fonts["small"], mouse_pos,
                          color=colors["RED"])
        utils["draw_btn"](confirm_no_r,  "CANCEL",   fonts["small"], mouse_pos,
                          color=colors["CYBER_CYAN"])

    # Event Interface Router
    for event in events:
        if save_popup_active:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and save_ok_r and save_ok_r.collidepoint(mouse_pos):
                save_popup_active = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                save_popup_active = False
            continue

        if coin_warning_popup_active:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and understood_r and understood_r.collidepoint(mouse_pos):
                coin_warning_popup_active = False
            continue

        # ── Overwrite confirmation events ───────────────────────────────────
        if overwrite_confirm_active:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if overwrite_yes_r and overwrite_yes_r.collidepoint(mouse_pos):
                    _commit_save(pending_filename)
                elif overwrite_no_r and overwrite_no_r.collidepoint(mouse_pos):
                    # Cancelled overwrite: go back to editing the filename
                    overwrite_confirm_active = False
                    pending_filename = ""
                    save_dialog_active = True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                overwrite_confirm_active = False
                pending_filename = ""
                save_dialog_active = True
            continue

        # ── Save-as filename dialog events ──────────────────────────────────
        if save_dialog_active:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if save_confirm_r and save_confirm_r.collidepoint(mouse_pos):
                    _attempt_save()
                elif save_cancel_r and save_cancel_r.collidepoint(mouse_pos):
                    save_dialog_active = False
                    if save_dialog_return_to_pause:
                        paused = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    _attempt_save()
                elif event.key == pygame.K_ESCAPE:
                    save_dialog_active = False
                    if save_dialog_return_to_pause:
                        paused = True
                elif event.key == pygame.K_BACKSPACE:
                    save_filename_input = save_filename_input[:-1]
                    save_dialog_error = ""
                elif event.unicode and event.unicode not in _FILENAME_BLOCKLIST and event.unicode.isprintable():
                    if len(save_filename_input) < 60:
                        save_filename_input += event.unicode
                        save_dialog_error = ""
            continue

        # ── End Game confirmation dialog events ───────────────────────────────
        if end_game_confirm_active:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if confirm_yes_r and confirm_yes_r.collidepoint(mouse_pos):
                    # Confirmed: clear volatile session data and return to main menu
                    reset()
                    return "main_menu", {}
                elif confirm_no_r and confirm_no_r.collidepoint(mouse_pos):
                    # Cancelled: close dialog, stay paused
                    end_game_confirm_active = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # ESC cancels the confirm dialog, not the whole pause
                    end_game_confirm_active = False
            continue

        # ── Pause menu events ─────────────────────────────────────────────────
        if paused:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if pause_resume_r and pause_resume_r.collidepoint(mouse_pos):
                    paused = False
                elif pause_save_r and pause_save_r.collidepoint(mouse_pos):
                    _open_save_dialog(return_to_pause=True)
                elif pause_endgame_r and pause_endgame_r.collidepoint(mouse_pos):
                    end_game_confirm_active = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = False
            continue

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Open the pause menu (deselect any active modes first)
                selected_bldg = None
                placement_mode = False
                demolish_mode = False
                paused = True
            elif event.key == pygame.K_1: selected_bldg = bldg1; placement_mode = True; demolish_mode = False
            elif event.key == pygame.K_2: selected_bldg = bldg2; placement_mode = True; demolish_mode = False
            elif event.key == pygame.K_d: selected_bldg = None; placement_mode = False; demolish_mode = not demolish_mode
            elif event.key == pygame.K_s:
                _open_save_dialog()
            elif event.key == pygame.K_q:
                # Return to the main menu immediately, same as Free Play's menu button
                reset()
                return "main_menu", {}
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if btn1.collidepoint(mouse_pos): selected_bldg = bldg1; placement_mode = True; demolish_mode = False
            elif btn2.collidepoint(mouse_pos): selected_bldg = bldg2; placement_mode = True; demolish_mode = False
            elif save_r.collidepoint(mouse_pos):
                _open_save_dialog()
            elif pause_r.collidepoint(mouse_pos):
                # Clicking the PAUSE button opens the pause menu
                selected_bldg = None
                placement_mode = False
                demolish_mode = False
                paused = True
            elif menu_r.collidepoint(mouse_pos):
                # Return to the main menu immediately, same as Free Play's menu button
                reset()
                return "main_menu", {}
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
                    
                    # ── Murray — Building placement: place selected building, end game if board full ──
                    # Places the chosen building on the clicked cell, recalculates
                    # the score, deducts 1 coin and adds any income earned this turn,
                    # then generates a fresh pair of buildings for the next turn.
                    # If every cell is now occupied the game ends so the player
                    # can see their final total score.
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
        'pause': pause_r,
        'menu': menu_r, 
        'demolish': demo_r,
        'save': save_r,
        'score': score
    }
