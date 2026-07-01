import pygame
import random
import sys

# ============================================================
#  Ngee Ann City Builder — Pygame GUI
#
#  NACG-14 (Janice)   : Main menu, 5 options, auto-launch      ✓ COMPLETE
#  NACG-21 (Bryan)    : 20×20 / 5×5 city map + turn counter   ✓ COMPLETE
#
#  Stubs for teammates to fill in:
#    NACG-1  (Murray)  : place_arcade() adjacency hook included
#    NACG-22 (JunWei)  : calculate_score() stub
#    NACG-24 (Valerie) : Free Play build logic stub
#    NACG-5  (Valerie) : Free Play demolish logic stub
#    NACG-26 (Murray)  : board_full() hook included → triggers game-over
#    NACG-8  (Janice)  : Free Play loss-counter hook (placeholder)
#    NACG-10 (Janice)  : Arcade demolish (placeholder button)
# ============================================================

pygame.init()

# ── Screen ─────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 900, 720
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Ngee Ann City Builder")
clock = pygame.time.Clock()

# ── Fonts (Courier New — retro aesthetic from game_pygame.py) ──
font_title  = pygame.font.SysFont('couriernew', 46, bold=True)
font_large  = pygame.font.SysFont('couriernew', 28, bold=True)
font_medium = pygame.font.SysFont('couriernew', 20, bold=True)
font_small  = pygame.font.SysFont('couriernew', 14, bold=True)
font_tiny   = pygame.font.SysFont('couriernew', 11)

# ── Colour Palette (matches game_pygame.py) ─────────────────
NIGHT_PURPLE  = ( 20,   0,  40)
CYBER_CYAN    = (  0, 255, 255)
WHITE         = (255, 255, 255)
BLACK         = ( 10,  10,  10)
GRAY_BLDG     = (100, 100, 100)
GOLD          = (255, 215,   0)
RED           = (220,  50,  50)
GREEN_NEON    = (  0, 220,  80)
GRID_LINE     = ( 55,  55,  75)
CELL_EMPTY    = ( 22,   5,  45)
CELL_HOVER    = (  0,  90,  90)
CELL_OCCUPIED = ( 38,  10,  65)
DARK_PANEL    = ( 14,   0,  32)

BUILDING_COLORS = {
    'R': (255, 100, 100),   # Residential
    'I': (100, 150, 255),   # Industry
    'C': (255, 200,  50),   # Commercial
    'O': ( 80, 220,  80),   # Park / Office
    '*': (200, 100, 255),   # Special
}

# ── Game Constants ──────────────────────────────────────────
BUILDINGS   = ['R', 'I', 'C', 'O', '*']
ARCADE_ROWS = 20
ARCADE_COLS = 20
FREE_ROWS   =  5
FREE_COLS   =  5

# ── Layout ──────────────────────────────────────────────────
#   Sidebar | Row-labels | Grid
#     240   |     28     | 20×30=600  →  total 868 ≤ 900  ✓
#   Header | Col-labels | Grid
#     65   |     22     | 20×30=600  →  total 687 ≤ 720  ✓
SIDEBAR_W   = 240
HEADER_H    =  65
COL_LABEL_H =  22
ROW_LABEL_W =  28
ARCADE_CELL =  30          # 30 × 20 = 600 px
FREE_CELL   =  90          # 90 × 5  = 450 px

ARCADE_GRID_X = SIDEBAR_W + ROW_LABEL_W           # 268
ARCADE_GRID_Y = HEADER_H  + COL_LABEL_H           #  87
FREE_GRID_X   = SIDEBAR_W + ROW_LABEL_W + 22      # 290
FREE_GRID_Y   = HEADER_H  + COL_LABEL_H           #  87

# ── Module-level Game State ─────────────────────────────────
state          = "main_menu"   # main_menu | arcade | freeplay | load_game | high_scores | game_over
coins          = 16
turn           = 1
city           = [[' '] * ARCADE_COLS for _ in range(ARCADE_ROWS)]
bldg1          = None          # two buildings offered this turn
bldg2          = None
selected_bldg  = None          # which one the player clicked
placement_mode = False         # True when waiting for grid click
final_score    = 0

free_city  = [[' '] * FREE_COLS for _ in range(FREE_ROWS)]
free_turn  = 1

# Free Play loss counter (NACG-8 hook – Janice)
fp_loss_streak = 0

message       = ""
message_timer = 0
MSG_DURATION  = 150            # ~2.5 s @ 60 fps

# ── One-time background skyline (matches game_pygame.py style) ─
_bg_x = 0
bg_rects: list[pygame.Rect] = []
while _bg_x < SCREEN_W:
    _h = random.randint(100, 290)
    bg_rects.append(pygame.Rect(_bg_x, SCREEN_H - _h, 55, _h))
    _bg_x += 55 + random.randint(4, 12)


# ============================================================
#  GAME LOGIC
# ============================================================

def set_msg(text: str) -> None:
    global message, message_timer
    message, message_timer = text, MSG_DURATION


def new_bldg_pair() -> None:
    global bldg1, bldg2
    bldg1 = random.choice(BUILDINGS)
    bldg2 = random.choice(BUILDINGS)
    while bldg2 == bldg1:
        bldg2 = random.choice(BUILDINGS)


def reset_arcade() -> None:
    global coins, turn, city, selected_bldg, placement_mode, final_score
    coins = 16
    turn  = 1
    city  = [[' '] * ARCADE_COLS for _ in range(ARCADE_ROWS)]
    selected_bldg  = None
    placement_mode = False
    final_score    = 0
    new_bldg_pair()


def reset_freeplay() -> None:
    global free_city, free_turn, fp_loss_streak
    free_city      = [[' '] * FREE_COLS for _ in range(FREE_ROWS)]
    free_turn      = 1
    fp_loss_streak = 0


def board_full(grid: list) -> bool:
    """NACG-26 / NACG-8 hook: returns True when no empty cells remain."""
    return all(cell != ' ' for row in grid for cell in row)


def calculate_score() -> int:
    """NACG-22 stub — scoring logic to be implemented by Jun Wei."""
    return 0


def is_valid_arcade_placement(r: int, c: int) -> tuple[bool, str]:
    """
    NACG-1 adjacency rule (Murray):
      Turn 1  → any empty cell.
      Turn 2+ → must be orthogonally adjacent to an existing building.
    Returns (ok, reason).
    """
    if city[r][c] != ' ':
        return False, "Cell is already occupied."
    if turn == 1:
        return True, ""
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < ARCADE_ROWS and 0 <= nc < ARCADE_COLS and city[nr][nc] != ' ':
            return True, ""
    return False, "Must be adjacent to an existing building."


def place_arcade(r: int, c: int) -> None:
    """Commit Arcade placement, deduct coin, advance turn, refresh pair."""
    global coins, turn, selected_bldg, placement_mode
    city[r][c]     = selected_bldg
    coins         -= 1
    turn          += 1
    selected_bldg  = None
    placement_mode = False
    new_bldg_pair()


# ============================================================
#  DRAW UTILITIES
# ============================================================

def draw_bg_skyline() -> None:
    """Retro 8-bit cityscape from game_pygame.py."""
    screen.fill(NIGHT_PURPLE)
    for b in bg_rects:
        pygame.draw.rect(screen, GRAY_BLDG, b)
        if b.height > 100:
            for yo in (25, 65):
                pygame.draw.rect(screen, CYBER_CYAN, (b.x + 10, b.y + yo, 7, 7))
                pygame.draw.rect(screen, CYBER_CYAN, (b.x + 32, b.y + yo, 7, 7))
            if b.height > 160:
                pygame.draw.rect(screen, CYBER_CYAN, (b.x + 10, b.y + 105, 7, 7))
                pygame.draw.rect(screen, CYBER_CYAN, (b.x + 32, b.y + 105, 7, 7))


def draw_btn(rect: pygame.Rect, label: str, fnt,
             mouse_pos: tuple, active: bool = False,
             color: tuple = CYBER_CYAN) -> None:
    hover = rect.collidepoint(mouse_pos) or active
    pygame.draw.rect(screen, color if hover else (40, 12, 72), rect, border_radius=4)
    pygame.draw.rect(screen, color, rect, 2, border_radius=4)
    s = fnt.render(label, True, BLACK if hover else WHITE)
    screen.blit(s, s.get_rect(center=rect.center))


def draw_text_c(text: str, fnt, color: tuple, cx: int, cy: int) -> None:
    s = fnt.render(text, True, color)
    screen.blit(s, s.get_rect(center=(cx, cy)))


def draw_header(title: str, t_color: tuple = CYBER_CYAN,
                bg: tuple = (30, 0, 60), line_color: tuple = None) -> None:
    pygame.draw.rect(screen, bg, (0, 0, SCREEN_W, HEADER_H))
    pygame.draw.line(screen, line_color or t_color,
                     (0, HEADER_H), (SCREEN_W, HEADER_H), 2)
    draw_text_c(title, font_large, t_color, SCREEN_W // 2, HEADER_H // 2)


def draw_sidebar_panel(bg: tuple = DARK_PANEL, line: tuple = CYBER_CYAN) -> None:
    pygame.draw.rect(screen, bg, (0, HEADER_H, SIDEBAR_W, SCREEN_H - HEADER_H))
    pygame.draw.line(screen, line, (SIDEBAR_W, HEADER_H), (SIDEBAR_W, SCREEN_H), 2)


def draw_grid(grid: list, rows: int, cols: int,
              gx: int, gy: int, cell_px: int,
              mouse_pos: tuple, hoverable: bool = False) -> None:
    """
    NACG-21: Render the city grid with row/col labels.
    Highlights hovered cell cyan when hoverable=True (placement mode).
    """
    for r in range(rows):
        for c in range(cols):
            cr = pygame.Rect(gx + c * cell_px, gy + r * cell_px, cell_px, cell_px)
            is_hover = cr.collidepoint(mouse_pos) and hoverable
            if is_hover:
                bg = CELL_HOVER
            elif grid[r][c] != ' ':
                bg = CELL_OCCUPIED
            else:
                bg = CELL_EMPTY
            pygame.draw.rect(screen, bg, cr)
            pygame.draw.rect(screen, GRID_LINE, cr, 1)
            if grid[r][c] != ' ':
                bc = BUILDING_COLORS.get(grid[r][c], WHITE)
                s  = font_small.render(grid[r][c], True, bc)
                screen.blit(s, s.get_rect(center=cr.center))


def draw_grid_labels(rows: int, cols: int,
                     gx: int, gy: int, cell_px: int) -> None:
    """NACG-21: Column numbers above, row numbers left of grid."""
    for c in range(cols):
        s = font_tiny.render(str(c + 1), True, (145, 145, 180))
        screen.blit(s, s.get_rect(
            center=(gx + c * cell_px + cell_px // 2, gy - COL_LABEL_H // 2)))
    for r in range(rows):
        s = font_tiny.render(str(r + 1), True, (145, 145, 180))
        screen.blit(s, s.get_rect(
            center=(gx - ROW_LABEL_W // 2, gy + r * cell_px + cell_px // 2)))


def grid_cell_at(mx: int, my: int, gx: int, gy: int,
                 cell_px: int, rows: int, cols: int):
    """Return (row, col) for pixel (mx, my), or None if outside the grid."""
    c = (mx - gx) // cell_px
    r = (my - gy) // cell_px
    if 0 <= r < rows and 0 <= c < cols:
        return r, c
    return None


def draw_sidebar_msg() -> None:
    """Timed feedback message in the lower sidebar."""
    if message_timer > 0:
        is_err = any(w in message for w in ("occupied", "adjacent", "Invalid"))
        col = (255, 80, 80) if is_err else GREEN_NEON
        s   = font_small.render(message, True, col)
        screen.blit(s, (8, SCREEN_H - 155))


def draw_legend(x: int, y: int) -> None:
    """Small building-type colour key in the sidebar."""
    names = {'R': 'Residential', 'I': 'Industry',
             'C': 'Commercial',  'O': 'Park/Office', '*': 'Special'}
    screen.blit(font_tiny.render("LEGEND:", True, (145, 145, 185)), (x, y))
    y += 14
    for k, col in BUILDING_COLORS.items():
        s = font_tiny.render(f" {k}  {names[k]}", True, col)
        screen.blit(s, (x, y))
        y += 13


# ============================================================
#  SCREEN: MAIN MENU — NACG-14 ✓
# ============================================================

def draw_main_menu(mouse_pos: tuple) -> dict:
    draw_bg_skyline()

    # Overlay for legibility over skyline
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((15, 0, 35, 168))
    screen.blit(ov, (0, 0))

    # Title (NACG-14 AC: displayed automatically on launch)
    draw_text_c("NGEE ANN CITY",       font_title,  CYBER_CYAN, SCREEN_W // 2,  78)
    draw_text_c("B  U  I  L  D  E  R", font_medium, WHITE,      SCREEN_W // 2, 128)
    pygame.draw.line(screen, CYBER_CYAN, (190, 154), (SCREEN_W - 190, 154), 1)

    # 5 menu options (NACG-14 AC: all 5 options, clearly numbered)
    items = [
        ("1", "1)  START NEW ARCADE GAME"),
        ("2", "2)  START NEW FREE PLAY GAME"),
        ("3", "3)  LOAD SAVED GAME"),
        ("4", "4)  DISPLAY HIGH SCORES"),
        ("5", "5)  EXIT GAME"),
    ]
    bw, bh = 350, 47
    bx = SCREEN_W // 2 - bw // 2
    rects: dict = {}
    for i, (key, lbl) in enumerate(items):
        r = pygame.Rect(bx, 172 + i * 62, bw, bh)
        draw_btn(r, lbl, font_small, mouse_pos)
        rects[key] = r

    draw_text_c("Press 1–5 or click to select", font_tiny, (100, 100, 130),
                SCREEN_W // 2, SCREEN_H - 28)
    return rects


# ============================================================
#  SCREEN: ARCADE MODE — NACG-14 routing + NACG-21 display ✓
# ============================================================

def draw_arcade(mouse_pos: tuple) -> dict:
    screen.fill((8, 3, 18))

    # ── Header (NACG-21: turn number always visible) ────────
    draw_header("◆  ARCADE MODE  ◆")
    s_c = font_medium.render(f"COINS: {coins}", True, GOLD)
    s_t = font_medium.render(f"TURN: {turn}",   True, WHITE)
    screen.blit(s_c, (SCREEN_W - 295, HEADER_H // 2 - s_c.get_height() // 2))
    screen.blit(s_t, (SCREEN_W - 115, HEADER_H // 2 - s_t.get_height() // 2))

    # ── Sidebar ─────────────────────────────────────────────
    draw_sidebar_panel()

    SY = HEADER_H + 14
    screen.blit(font_small.render("SELECT A BUILDING:", True, CYBER_CYAN), (10, SY))
    SY += 24

    btn1 = pygame.Rect(10, SY,      SIDEBAR_W - 20, 50)
    btn2 = pygame.Rect(10, SY + 62, SIDEBAR_W - 20, 50)

    for btn, bldg, key in ((btn1, bldg1, "1"), (btn2, bldg2, "2")):
        active = (selected_bldg == bldg)
        hover  = btn.collidepoint(mouse_pos) or active
        bc     = BUILDING_COLORS.get(bldg, WHITE)
        pygame.draw.rect(screen, CYBER_CYAN if hover else (40, 12, 72), btn, border_radius=4)
        pygame.draw.rect(screen, bc, btn, 2, border_radius=4)
        draw_text_c(f"[{key}]  {bldg}", font_large,
                    BLACK if hover else WHITE, btn.centerx, btn.centery)

    SY += 128

    # Placement status
    if placement_mode and selected_bldg:
        draw_text_c(f"Placing: {selected_bldg}", font_small, GREEN_NEON, SIDEBAR_W // 2, SY)
        draw_text_c("Click the grid to place",   font_tiny,  GREEN_NEON, SIDEBAR_W // 2, SY + 18)
    elif selected_bldg:
        draw_text_c(f"Selected: {selected_bldg}", font_small, GOLD, SIDEBAR_W // 2, SY)
    else:
        draw_text_c("Pick a building above", font_tiny, (120, 120, 155), SIDEBAR_W // 2, SY)

    draw_legend(10, SY + 42)
    draw_sidebar_msg()

    # NACG-10 stub (Janice) — demolish button placeholder
    demo_r = pygame.Rect(10, SCREEN_H - 165, SIDEBAR_W - 20, 38)
    draw_btn(demo_r, "DEMOLISH  [stub]", font_tiny, mouse_pos, color=(180, 60, 60))

    cancel_r = pygame.Rect(10, SCREEN_H - 118, SIDEBAR_W - 20, 40)
    menu_r   = pygame.Rect(10, SCREEN_H - 68,  SIDEBAR_W - 20, 40)
    draw_btn(cancel_r, "[ESC]  CANCEL",   font_small, mouse_pos)
    draw_btn(menu_r,   "[Q]  MAIN MENU",  font_small, mouse_pos)

    # ── 20×20 City Map (NACG-21) ────────────────────────────
    draw_grid(city, ARCADE_ROWS, ARCADE_COLS,
              ARCADE_GRID_X, ARCADE_GRID_Y,
              ARCADE_CELL, mouse_pos, hoverable=placement_mode)
    draw_grid_labels(ARCADE_ROWS, ARCADE_COLS,
                     ARCADE_GRID_X, ARCADE_GRID_Y, ARCADE_CELL)

    return {'btn1': btn1, 'btn2': btn2,
            'cancel': cancel_r, 'menu': menu_r, 'demolish': demo_r}


# ============================================================
#  SCREEN: FREE PLAY MODE — NACG-21 display + stubs ✓
# ============================================================

def draw_freeplay(mouse_pos: tuple) -> dict:
    screen.fill((5, 14, 8))

    # ── Header (NACG-21: turn number) ───────────────────────
    draw_header("◆  FREE PLAY MODE  ◆",
                t_color=GREEN_NEON, bg=(0, 24, 8), line_color=GREEN_NEON)
    s = font_medium.render(f"TURN: {free_turn}", True, WHITE)
    screen.blit(s, (SCREEN_W - 160, HEADER_H // 2 - s.get_height() // 2))

    # ── Sidebar ─────────────────────────────────────────────
    draw_sidebar_panel(bg=(0, 12, 5), line=GREEN_NEON)

    SY = HEADER_H + 14
    screen.blit(font_small.render("BUILD OPTIONS:", True, GREEN_NEON), (10, SY))
    SY += 24

    # NACG-24 stubs — one button per building type (Valerie)
    bldg_btns: dict = {}
    for b in BUILDINGS:
        r  = pygame.Rect(10, SY, SIDEBAR_W - 20, 38)
        bc = BUILDING_COLORS[b]
        hover = r.collidepoint(mouse_pos)
        pygame.draw.rect(screen, bc if hover else (28, 28, 28), r, border_radius=4)
        pygame.draw.rect(screen, bc, r, 2, border_radius=4)
        txt = font_medium.render(f" {b} ", True, BLACK if hover else bc)
        screen.blit(txt, txt.get_rect(center=r.center))
        bldg_btns[b] = r
        SY += 44

    screen.blit(font_tiny.render("Logic: NACG-24 / NACG-5 (Valerie)", True, (60, 60, 60)), (8, SY + 4))

    # NACG-5 stub — demolish
    demo_r = pygame.Rect(10, SCREEN_H - 165, SIDEBAR_W - 20, 38)
    draw_btn(demo_r, "DEMOLISH  [stub]", font_tiny, mouse_pos, color=(180, 60, 60))

    menu_r = pygame.Rect(10, SCREEN_H - 68, SIDEBAR_W - 20, 40)
    draw_btn(menu_r, "[Q]  MAIN MENU", font_small, mouse_pos, color=GREEN_NEON)

    # ── 5×5 City Map (NACG-21) ──────────────────────────────
    draw_grid(free_city, FREE_ROWS, FREE_COLS,
              FREE_GRID_X, FREE_GRID_Y, FREE_CELL, mouse_pos, hoverable=False)
    draw_grid_labels(FREE_ROWS, FREE_COLS,
                     FREE_GRID_X, FREE_GRID_Y, FREE_CELL)

    return {'menu': menu_r, 'demolish': demo_r, **bldg_btns}


# ============================================================
#  PLACEHOLDER SCREENS
# ============================================================

def draw_placeholder(title: str, mouse_pos: tuple) -> dict:
    draw_bg_skyline()
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((15, 0, 35, 185))
    screen.blit(ov, (0, 0))
    draw_text_c(title,               font_large,  CYBER_CYAN, SCREEN_W // 2, 240)
    draw_text_c("UNDER DEVELOPMENT", font_medium, WHITE,      SCREEN_W // 2, 296)
    back = pygame.Rect(SCREEN_W // 2 - 165, 372, 330, 50)
    draw_btn(back, "BACK TO MAIN MENU", font_medium, mouse_pos)
    return {'back': back}


# ============================================================
#  SCREEN: GAME OVER — triggered by NACG-26 (arcade) or NACG-8 (free play)
# ============================================================

def draw_game_over(mouse_pos: tuple) -> dict:
    draw_bg_skyline()
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((20, 0, 40, 210))
    screen.blit(ov, (0, 0))
    pygame.draw.line(screen, RED, (140, 212), (SCREEN_W - 140, 212), 2)
    draw_text_c("GAME OVER",                    font_title,  RED,  SCREEN_W // 2, 270)
    draw_text_c(f"FINAL SCORE:  {final_score}", font_large,  GOLD, SCREEN_W // 2, 338)
    pygame.draw.line(screen, RED, (140, 375), (SCREEN_W - 140, 375), 2)
    back = pygame.Rect(SCREEN_W // 2 - 165, 432, 330, 50)
    draw_btn(back, "MAIN MENU", font_medium, mouse_pos)
    return {'back': back}


# ============================================================
#  MAIN LOOP
# ============================================================

reset_arcade()
reset_freeplay()

current_buttons: dict = {}
running = True

while running:
    mouse_pos = pygame.mouse.get_pos()

    # ── Event Handling ──────────────────────────────────────
    #    current_buttons holds rects from the previous draw frame.
    #    One-frame lag is imperceptible since button positions never change.
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # ── MAIN MENU ──────────────────────────────────────
        if state == "main_menu":
            # NACG-14 AC: "select a menu option by entering the corresponding number"
            if event.type == pygame.KEYDOWN:
                if   event.key == pygame.K_1: reset_arcade();   state = "arcade"
                elif event.key == pygame.K_2: reset_freeplay(); state = "freeplay"
                elif event.key == pygame.K_3: state = "load_game"
                elif event.key == pygame.K_4: state = "high_scores"
                elif event.key == pygame.K_5: running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                b = current_buttons
                if b.get('1', pygame.Rect(0,0,0,0)).collidepoint(mouse_pos):
                    reset_arcade();   state = "arcade"
                elif b.get('2', pygame.Rect(0,0,0,0)).collidepoint(mouse_pos):
                    reset_freeplay(); state = "freeplay"
                elif b.get('3', pygame.Rect(0,0,0,0)).collidepoint(mouse_pos):
                    state = "load_game"
                elif b.get('4', pygame.Rect(0,0,0,0)).collidepoint(mouse_pos):
                    state = "high_scores"
                elif b.get('5', pygame.Rect(0,0,0,0)).collidepoint(mouse_pos):
                    running = False

        # ── ARCADE MODE ────────────────────────────────────
        elif state == "arcade":
            if event.type == pygame.KEYDOWN:
                if   event.key == pygame.K_q:      state = "main_menu"
                elif event.key == pygame.K_ESCAPE:
                    selected_bldg = None; placement_mode = False
                elif event.key == pygame.K_1:
                    selected_bldg = bldg1; placement_mode = True
                elif event.key == pygame.K_2:
                    selected_bldg = bldg2; placement_mode = True

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                b = current_buttons
                if b.get('btn1', pygame.Rect(0,0,0,0)).collidepoint(mouse_pos):
                    selected_bldg = bldg1; placement_mode = True
                elif b.get('btn2', pygame.Rect(0,0,0,0)).collidepoint(mouse_pos):
                    selected_bldg = bldg2; placement_mode = True
                elif b.get('cancel', pygame.Rect(0,0,0,0)).collidepoint(mouse_pos):
                    selected_bldg = None; placement_mode = False
                elif b.get('menu', pygame.Rect(0,0,0,0)).collidepoint(mouse_pos):
                    state = "main_menu"
                elif placement_mode:
                    # Direct pixel-to-cell hit-test (no frame-lag dependency)
                    cell = grid_cell_at(*mouse_pos,
                                        ARCADE_GRID_X, ARCADE_GRID_Y,
                                        ARCADE_CELL, ARCADE_ROWS, ARCADE_COLS)
                    if cell:
                        r, c = cell
                        ok, reason = is_valid_arcade_placement(r, c)
                        if ok:
                            place_arcade(r, c)
                            set_msg("Building placed!")
                            # NACG-26 hook (Murray): trigger game-over when board full
                            if board_full(city):
                                final_score = calculate_score()
                                state = "game_over"
                        else:
                            set_msg(reason)

        # ── FREE PLAY MODE ─────────────────────────────────
        elif state == "freeplay":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    state = "main_menu"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if current_buttons.get('menu', pygame.Rect(0,0,0,0)).collidepoint(mouse_pos):
                    state = "main_menu"
                # NACG-24 / NACG-5 building/demolish logic goes here (Valerie)

        # ── PLACEHOLDER SCREENS ────────────────────────────
        elif state in ("load_game", "high_scores"):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if current_buttons.get('back', pygame.Rect(0,0,0,0)).collidepoint(mouse_pos):
                    state = "main_menu"

        # ── GAME OVER ──────────────────────────────────────
        elif state == "game_over":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if current_buttons.get('back', pygame.Rect(0,0,0,0)).collidepoint(mouse_pos):
                    state = "main_menu"

    # Message countdown
    if message_timer > 0:
        message_timer -= 1

    # ── Draw ────────────────────────────────────────────────
    if   state == "main_menu":
        current_buttons = draw_main_menu(mouse_pos)
    elif state == "arcade":
        current_buttons = draw_arcade(mouse_pos)
    elif state == "freeplay":
        current_buttons = draw_freeplay(mouse_pos)
    elif state == "load_game":
        current_buttons = draw_placeholder("LOAD SAVED GAME", mouse_pos)
    elif state == "high_scores":
        current_buttons = draw_placeholder("HIGH SCORES", mouse_pos)
    elif state == "game_over":
        current_buttons = draw_game_over(mouse_pos)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
