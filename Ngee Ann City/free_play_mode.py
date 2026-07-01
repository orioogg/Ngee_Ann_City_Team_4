import pygame

# Domain runtime storage data scopes
free_city = []
free_turn = 1
show_fp_overlay = False
fp_overlay_timer = 0
selected_bldg = None
placement_mode = False

def init_mode(assets_ref):
    global free_city
    c = assets_ref["constants"]
    free_city = [[' '] * c["FREE_COLS"] for _ in range(c["FREE_ROWS"])]

def reset():
    global free_city, free_turn, show_fp_overlay, fp_overlay_timer, selected_bldg, placement_mode
    free_city = [[' '] * 5 for _ in range(5)]
    free_turn = 1
    selected_bldg = None
    placement_mode = False
    show_fp_overlay = True
    fp_overlay_timer = 360  # 6 seconds popup notice duration

def draw_grid(screen, grid, rows, cols, gx, gy, cell_px, mouse_pos, colors, fonts, hoverable):
    utils = pygame.display.get_surface()
    for r in range(rows):
        for c in range(cols):
            cr = pygame.Rect(gx + c * cell_px, gy + r * cell_px, cell_px, cell_px)
            is_hover = cr.collidepoint(mouse_pos) and hoverable
            
            if is_hover:
                bg = colors["CELL_HOVER"]
            elif grid[r][c] != ' ':
                bg = colors["CELL_OCCUPIED"]
            else:
                bg = colors["CELL_EMPTY"]
                
            pygame.draw.rect(screen, bg, cr)
            pygame.draw.rect(screen, colors["GRID_LINE"], cr, 1)
            
            # Draw established blocks centered as 1:2 vertical rectangles
            if grid[r][c] != ' ':
                bc = colors["BUILDING_COLORS"].get(grid[r][c], (255, 255, 255))
                rect_w, rect_h = 34, 68
                bldg_rect = pygame.Rect(cr.centerx - rect_w // 2, cr.centery - rect_h // 2, rect_w, rect_h)
                pygame.draw.rect(screen, bc, bldg_rect, border_radius=4)
                s = fonts["small"].render(grid[r][c], True, (10, 10, 10))
                screen.blit(s, s.get_rect(center=bldg_rect.center))

def update(events, mouse_pos, assets):
    global free_turn, show_fp_overlay, fp_overlay_timer, selected_bldg, placement_mode, free_city
    next_state = "freeplay"
    
    screen = assets["screen"]
    utils = assets["utils"]
    fonts = assets["fonts"]
    colors = assets["colors"]
    layout = assets["layout"]
    const = assets["constants"]

    screen.fill((5, 14, 8))
    utils["draw_header"]("◆  FREE PLAY MODE  ◆", t_color=colors["GREEN_NEON"], bg=(0, 24, 8), line_color=colors["GREEN_NEON"])
    
    s = fonts["medium"].render(f"TURN: {free_turn}", True, (255, 255, 255))
    screen.blit(s, (assets["SCREEN_W"] - 160, layout["HEADER_H"] // 2 - s.get_height() // 2))

    utils["draw_sidebar_panel"](bg=(0, 12, 5), line=colors["GREEN_NEON"])

    SY = layout["HEADER_H"] + 14
    screen.blit(fonts["small"].render("BUILD OPTIONS:", True, colors["GREEN_NEON"]), (10, SY))
    SY += 24

    bldg_btns = {}
    for b in const["BUILDINGS"]:
        r = pygame.Rect(10, SY, layout["SIDEBAR_W"] - 20, 38)
        bc = colors["BUILDING_COLORS"][b]
        active = (selected_bldg == b)
        hover = r.collidepoint(mouse_pos) or active
        pygame.draw.rect(screen, bc if hover else (28, 28, 28), r, border_radius=4)
        pygame.draw.rect(screen, bc, r, 2, border_radius=4)
        txt = fonts["medium"].render(f" {b} ", True, (10, 10, 10) if hover else bc)
        screen.blit(txt, txt.get_rect(center=r.center))
        bldg_btns[b] = r
        SY += 44

    # Hotkey Mapping Inputs Tracking Layout
    for idx, b_char in enumerate(['R', 'I', 'C', 'O']):
        lbl_h = fonts["tiny"].render(f"Press [{b_char}]", True, (120, 150, 130))
        screen.blit(lbl_h, (layout["SIDEBAR_W"] - 95, layout["HEADER_H"] + 48 + (idx * 44)))

    demo_r = pygame.Rect(10, assets["SCREEN_H"] - 165, layout["SIDEBAR_W"] - 20, 38)
    utils["draw_btn"](demo_r, "DEMOLISH  [stub]", fonts["tiny"], mouse_pos, color=(180, 60, 60))

    menu_r = pygame.Rect(10, assets["SCREEN_H"] - 68, layout["SIDEBAR_W"] - 20, 40)
    utils["draw_btn"](menu_r, "[Q]  MAIN MENU", fonts["small"], mouse_pos, color=colors["GREEN_NEON"])

    # Draw Current Core Matrix 
    draw_grid(screen, free_city, const["FREE_ROWS"], const["FREE_COLS"],
              layout["FREE_GRID_X"], layout["FREE_GRID_Y"], layout["FREE_CELL"], mouse_pos, colors, fonts, hoverable=placement_mode)
    utils["draw_grid_labels"](const["FREE_ROWS"], const["FREE_COLS"], layout["FREE_GRID_X"], layout["FREE_GRID_Y"], layout["FREE_CELL"])

    # ── 1:2 Drag Follow and Snap Frame Rendering Preview Engine ──
    if placement_mode and selected_bldg:
        cell = utils["grid_cell_at"](*mouse_pos, layout["FREE_GRID_X"], layout["FREE_GRID_Y"], layout["FREE_CELL"], const["FREE_ROWS"], const["FREE_COLS"])
        rect_w, rect_h = 34, 68
        bc = colors["BUILDING_COLORS"].get(selected_bldg, (255, 255, 255))
        
        if cell:
            crow, ccol = cell
            tx = layout["FREE_GRID_X"] + ccol * layout["FREE_CELL"] + layout["FREE_CELL"] // 2
            ty = layout["FREE_GRID_Y"] + crow * layout["FREE_CELL"] + layout["FREE_CELL"] // 2
            p_rect = pygame.Rect(tx - rect_w // 2, ty - rect_h // 2, rect_w, rect_h)
        else:
            p_rect = pygame.Rect(mouse_pos[0] - rect_w // 2, mouse_pos[1] - rect_h // 2, rect_w, rect_h)

        pygame.draw.rect(screen, bc, p_rect, border_radius=4)
        pygame.draw.rect(screen, (255, 255, 255), p_rect, 2, border_radius=4)
        lbl = fonts["small"].render(selected_bldg, True, (10, 10, 10))
        screen.blit(lbl, lbl.get_rect(center=p_rect.center))

    # Countdown notification overlays
    if show_fp_overlay:
        fp_overlay_timer -= 1
        if fp_overlay_timer <= 0:
            show_fp_overlay = False
        utils["draw_retro_popup"]([
            "FREE PLAY: Unlimited coins on a 5x5 grid.",
            "Construction costs 1 coin per turn.",
            "Build on a border cell to expand the perimeter:",
            "1st Expansion -> 15x15  |  2nd Expansion -> 25x25"
        ])

    # Event Handlers Loop Processing Thread
    for event in events:
        if show_fp_overlay and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            show_fp_overlay = False; fp_overlay_timer = 0; continue

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                next_state = "main_menu"; selected_bldg = None; placement_mode = False
            elif event.key == pygame.K_r: selected_bldg = 'R'; placement_mode = True
            elif event.key == pygame.K_i: selected_bldg = 'I'; placement_mode = True
            elif event.key == pygame.K_c: selected_bldg = 'C'; placement_mode = True
            elif event.key == pygame.K_o: selected_bldg = 'O'; placement_mode = True
            elif event.key == pygame.K_ESCAPE: selected_bldg = None; placement_mode = False

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if menu_r.collidepoint(mouse_pos):
                next_state = "main_menu"; selected_bldg = None; placement_mode = False
                continue

            btn_clicked = False
            for b_key, b_rect in bldg_btns.items():
                if b_rect.collidepoint(mouse_pos):
                    selected_bldg = b_key
                    placement_mode = True
                    btn_clicked = True
                    break

            if not btn_clicked and placement_mode and selected_bldg:
                cell = utils["grid_cell_at"](*mouse_pos, layout["FREE_GRID_X"], layout["FREE_GRID_Y"], layout["FREE_CELL"], const["FREE_ROWS"], const["FREE_COLS"])
                if cell:
                    r, c = cell
                    if free_city[r][c] == ' ':
                        free_city[r][c] = selected_bldg
                        free_turn += 1
                        selected_bldg = None
                        placement_mode = False
                    else:
                        assets["system"]["set_msg"]("Cell is already occupied.")

    # Render error/success prompt logs
    msg, m_timer = assets["system"]["get_msg"]()
    if m_timer > 0:
        s_msg = fonts["small"].render(msg, True, (255, 80, 80))
        screen.blit(s_msg, (8, assets["SCREEN_H"] - 130))

    return next_state, {'menu': menu_r, 'demolish': demo_r, **bldg_btns}