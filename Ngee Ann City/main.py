import pygame
import random
import sys

# Import custom state handlers
import main_menu
import arcade_mode
import free_play_mode

pygame.init()

# ── Screen Configuration ──
SCREEN_W, SCREEN_H = 900, 720
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Ngee Ann City Builder")
clock = pygame.time.Clock()

# ── Global Shared Assets Registry ──
assets = {
    "screen": screen,
    "SCREEN_W": SCREEN_W,
    "SCREEN_H": SCREEN_H,
    "fonts": {
        "title": pygame.font.SysFont('pixeloidsans', 80, bold=True),
        "large": pygame.font.SysFont('pixeloidsans', 60, bold=True),
        "medium": pygame.font.SysFont('pixeloidsans', 30, bold=True),
        "small": pygame.font.SysFont('pixeloidsans', 20, bold=True),
        "tiny": pygame.font.SysFont('pixeloidsans', 15)
    },
    "colors": {
        "NIGHT_PURPLE": (20, 0, 40),
        "CYBER_CYAN": (0, 255, 255),
        "WHITE": (255, 255, 255),
        "BLACK": (10, 10, 10),
        "GRAY_BLDG": (100, 100, 100),
        "GOLD": (255, 215, 0),
        "RED": (220, 50, 50),
        "GREEN_NEON": (0, 220, 80),
        "GRID_LINE": (55, 55, 75),
        "CELL_EMPTY": (22, 5, 45),
        "CELL_HOVER": (0, 90, 90),
        "CELL_OCCUPIED": (38, 10, 65),
        "DARK_PANEL": (14, 0, 32),
        "BUILDING_COLORS": {
            'R': (255, 100, 100),
            'I': (100, 150, 255),
            'C': (255, 200, 50),
            'O': (80, 220, 80),
            '*': (200, 100, 255),
        }
    },
    "layout": {
        "SIDEBAR_W": 240,
        "HEADER_H": 65,
        "COL_LABEL_H": 22,
        "ROW_LABEL_W": 28,
        "ARCADE_CELL": 30,
        "FREE_CELL": 90,
        "ARCADE_GRID_X": 268,
        "ARCADE_GRID_Y": 87,
        "FREE_GRID_X": 290,
        "FREE_GRID_Y": 87
    },
    "constants": {
        "BUILDINGS": ['R', 'I', 'C', 'O', '*'],
        "ARCADE_ROWS": 20,
        "ARCADE_COLS": 20,
        "FREE_ROWS": 5,
        "FREE_COLS": 5
    }
}

# ── Generate Shared Pre-rendered Background Assets ──
sky_gradient = pygame.Surface((SCREEN_W, SCREEN_H))
COLOR_TOP = (0, 98, 214)
COLOR_BOTTOM = (84, 252, 219)
for y in range(SCREEN_H):
    t = y / SCREEN_H
    r = int(COLOR_TOP[0] + (COLOR_BOTTOM[0] - COLOR_TOP[0]) * t)
    g = int(COLOR_TOP[1] + (COLOR_BOTTOM[1] - COLOR_TOP[1]) * t)
    b = int(COLOR_TOP[2] + (COLOR_BOTTOM[2] - COLOR_TOP[2]) * t)
    pygame.draw.line(sky_gradient, (r, g, b), (0, y), (SCREEN_W, y))
assets["sky_gradient"] = sky_gradient

random.seed(42)
bg_rects = []
current_x = 0
while current_x < SCREEN_W:
    w = random.randint(50, 90)
    h = random.randint(80, 240)
    bg_rects.append(pygame.Rect(current_x, SCREEN_H - h, w, h))
    current_x += w - random.randint(5, 20)
assets["bg_rects"] = bg_rects

assets["clouds"] = [
    {"x": 120, "y": 80,  "circles": [(0, 0, 35), (-25, 5, 25), (25, 5, 25), (-45, 10, 18), (45, 10, 18)]},
    {"x": 420, "y": 140, "circles": [(0, 0, 45), (-35, 8, 30), (35, 8, 30), (-60, 15, 22), (60, 15, 22)]},
    {"x": 760, "y": 95,  "circles": [(0, 0, 30), (-22, 4, 22), (22, 4, 22), (-40, 8, 15)]}
]

# ── Shared Utility Components ──
def draw_clouds():
    cloud_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    for group in assets["clouds"]:
        cx, cy = group["x"], group["y"]
        for ox, oy, radius in group["circles"]:
            pygame.draw.circle(cloud_surf, (255, 255, 255, 115), (cx + ox, cy + oy), radius)
    screen.blit(cloud_surf, (0, 0))

def draw_bg_skyline():
    screen.blit(assets["sky_gradient"], (0, 0))
    draw_clouds()
    colors = assets["colors"]
    for b in assets["bg_rects"]:
        pygame.draw.rect(screen, colors["GRAY_BLDG"], b)
        if b.height > 100:
            for yo in (25, 65):
                pygame.draw.rect(screen, colors["CYBER_CYAN"], (b.x + 10, b.y + yo, 7, 7))
                pygame.draw.rect(screen, colors["CYBER_CYAN"], (b.x + 32, b.y + yo, 7, 7))
        if b.height > 160:
            pygame.draw.rect(screen, colors["CYBER_CYAN"], (b.x + 10, b.y + 105, 7, 7))
            pygame.draw.rect(screen, colors["CYBER_CYAN"], (b.x + 32, b.y + 105, 7, 7))

def draw_btn(rect, label, fnt, mouse_pos, active=False, color=(0, 255, 255)):
    hover = rect.collidepoint(mouse_pos) or active
    pygame.draw.rect(screen, color if hover else (40, 12, 72), rect, border_radius=4)
    pygame.draw.rect(screen, color, rect, 2, border_radius=4)
    s = fnt.render(label, True, (10, 10, 10) if hover else (255, 255, 255))
    screen.blit(s, s.get_rect(center=rect.center))

def draw_text_c(text, fnt, color, cx, cy):
    s = fnt.render(text, True, color)
    screen.blit(s, s.get_rect(center=(cx, cy)))

def draw_header(title, t_color=(0, 255, 255), bg=(30, 0, 60), line_color=None):
    pygame.draw.rect(screen, bg, (0, 0, SCREEN_W, assets["layout"]["HEADER_H"]))
    pygame.draw.line(screen, line_color or t_color, (0, assets["layout"]["HEADER_H"]), (SCREEN_W, assets["layout"]["HEADER_H"]), 2)
    draw_text_c(title, assets["fonts"]["large"], t_color, SCREEN_W // 2, assets["layout"]["HEADER_H"] // 2)

def draw_sidebar_panel(bg=(14, 0, 32), line=(0, 255, 255)):
    sb_w = assets["layout"]["SIDEBAR_W"]
    hd_h = assets["layout"]["HEADER_H"]
    pygame.draw.rect(screen, bg, (0, hd_h, sb_w, SCREEN_H - hd_h))
    pygame.draw.line(screen, line, (sb_w, hd_h), (sb_w, SCREEN_H), 2)

def grid_cell_at(mx, my, gx, gy, cell_px, rows, cols):
    c = (mx - gx) // cell_px
    r = (my - gy) // cell_px
    if 0 <= r < rows and 0 <= c < cols:
        return r, c
    return None

def draw_grid_labels(rows, cols, gx, gy, cell_px):
    for c in range(cols):
        s = assets["fonts"]["tiny"].render(str(c + 1), True, (145, 145, 180))
        screen.blit(s, s.get_rect(center=(gx + c * cell_px + cell_px // 2, gy - assets["layout"]["COL_LABEL_H"] // 2)))
    for r in range(rows):
        s = assets["fonts"]["tiny"].render(str(r + 1), True, (145, 145, 180))
        screen.blit(s, s.get_rect(center=(gx - assets["layout"]["ROW_LABEL_W"] // 2, gy + r * cell_px + cell_px // 2)))

def draw_legend(x, y):
    names = {'R': 'Residential', 'I': 'Industry', 'C': 'Commercial', 'O': 'Park/Office', '*': 'Special'}
    screen.blit(assets["fonts"]["tiny"].render("LEGEND:", True, (145, 145, 185)), (x, y))
    y += 14
    for k, col in assets["colors"]["BUILDING_COLORS"].items():
        s = assets["fonts"]["tiny"].render(f" {k}  {names[k]}", True, col)
        screen.blit(s, (x, y))
        y += 13

def draw_retro_popup(text_lines):
    tw, th = 620, 140
    tx = (SCREEN_W - tw) // 2
    ty = (SCREEN_H - th) // 2
    pygame.draw.rect(screen, (10, 10, 10), (tx + 5, ty + 5, tw, th), border_radius=24)
    pygame.draw.rect(screen, (255, 255, 255), (tx, ty, tw, th), border_radius=24)
    pygame.draw.rect(screen, (10, 10, 10), (tx, ty, tw, th), width=4, border_radius=24)
    
    line_height = 24
    start_y = ty + 22
    for i, line in enumerate(text_lines):
        s_text = assets["fonts"]["tiny"].render(line, True, (10, 10, 10))
        screen.blit(s_text, s_text.get_rect(center=(SCREEN_W // 2, start_y + (i * line_height))))
    
    tri_x, tri_y = tx + tw - 32, ty + th - 22
    pygame.draw.polygon(screen, (10, 10, 10), [(tri_x, tri_y), (tri_x + 12, tri_y), (tri_x + 6, tri_y + 6)])

# Pack utils into assets so modules can access them seamlessly
assets["utils"] = {
    "draw_bg_skyline": draw_bg_skyline, "draw_btn": draw_btn, "draw_text_c": draw_text_c,
    "draw_header": draw_header, "draw_sidebar_panel": draw_sidebar_panel,
    "grid_cell_at": grid_cell_at, "draw_grid_labels": draw_grid_labels,
    "draw_legend": draw_legend, "draw_retro_popup": draw_retro_popup
}

# ── Dynamic System Runtime States ──
state = "main_menu"
current_buttons = {}
message = ""
message_timer = 0

def set_msg(text):
    global message, message_timer
    message, message_timer = text, 150

assets["system"] = {"set_msg": set_msg, "get_msg": lambda: (message, message_timer)}

# Initialize default inner game logic loops
arcade_mode.init_mode(assets)
free_play_mode.init_mode(assets)

# ── Application Main Loop ──
while True:
    mouse_pos = pygame.mouse.get_pos()
    events = pygame.event.get()

    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Decrement tracking timers
    if message_timer > 0:
        message_timer -= 1

    # Main State Engine Router
    if state == "main_menu":
        state, current_buttons = main_menu.update(events, mouse_pos, assets)
    elif state == "arcade":
        state, current_buttons = arcade_mode.update(events, mouse_pos, assets)
    elif state == "freeplay":
        state, current_buttons = free_play_mode.update(events, mouse_pos, assets)
    elif state in ("load_game", "high_scores"):
        draw_bg_skyline()
        draw_text_c(state.replace("_", " ").upper(), assets["fonts"]["large"], assets["colors"]["CYBER_CYAN"], SCREEN_W // 2, 240)
        draw_text_c("UNDER DEVELOPMENT", assets["fonts"]["medium"], (255, 255, 255), SCREEN_W // 2, 296)
        back_r = pygame.Rect(SCREEN_W // 2 - 165, 372, 330, 50)
        draw_btn(back_r, "BACK TO MAIN MENU", assets["fonts"]["medium"], mouse_pos)
        current_buttons = {'back': back_r}
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_r.collidepoint(mouse_pos):
                    state = "main_menu"
    elif state == "game_over":
        draw_bg_skyline()
        draw_text_c("GAME OVER", assets["fonts"]["title"], assets["colors"]["RED"], SCREEN_W // 2, 270)
        back_r = pygame.Rect(SCREEN_W // 2 - 165, 432, 330, 50)
        draw_btn(back_r, "MAIN MENU", assets["fonts"]["medium"], mouse_pos)
        current_buttons = {'back': back_r}
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_r.collidepoint(mouse_pos):
                    state = "main_menu"

    pygame.display.flip()
    clock.tick(60)