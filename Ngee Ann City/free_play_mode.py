import pygame

# Domain runtime storage data scopes
free_city = []
free_turn = 1
free_profit = 0
show_fp_overlay = False
fp_overlay_timer = 0
selected_bldg = None
placement_mode = False
selected_grid_cell = None  # Tracks (row, col) targeted for demolition
consecutive_losses = 0 # tracks the consecutive losses
loss_warning_shown = False  # NACG-28: whether the popup has fired for the current 15+ streak
loss_warning_popup_active = False  # True while the blocking centre-screen popup awaits [UNDERSTOOD]
loss_warning_sidebar_active = False  # True while consecutive_losses >= 15; drives the sidebar reminder

def init_mode(assets_ref):
    global free_city, selected_grid_cell
    c = assets_ref["constants"]
    # Initialize constants dynamically in case of full state reload
    c["FREE_ROWS"] = 5
    c["FREE_COLS"] = 5
    free_city = [[' '] * c["FREE_COLS"] for _ in range(c["FREE_ROWS"])]
    selected_grid_cell = None

def reset(assets=None):
    global free_city, free_turn, free_profit, show_fp_overlay, fp_overlay_timer, selected_bldg, placement_mode, selected_grid_cell, consecutive_losses
    global loss_warning_shown, loss_warning_popup_active, loss_warning_sidebar_active
    free_city = [[' '] * 5 for _ in range(5)]
    free_turn = 1
    free_profit = 0
    consecutive_losses = 0 
    loss_warning_shown = False
    loss_warning_popup_active = False
    loss_warning_sidebar_active = False
    selected_bldg = None
    placement_mode = False
    show_fp_overlay = True
    fp_overlay_timer = 360  # 6 seconds popup notice duration
    selected_grid_cell = None

    if assets:
        const = assets["constants"]
        layout = assets["layout"]
        
        #reset row/col bounds counters back to initial constraints
        const["FREE_ROWS"] = 5
        const["FREE_COLS"] = 5
        
        #restore grid tile scale size to its default width parameters
        layout["FREE_CELL"] = 90  
        
        #re-center grid layout box dynamically based on the original default scale coordinates
        grid_w_px = 5 * layout["FREE_CELL"]
        canvas_avail_w = assets["SCREEN_W"] - layout["SIDEBAR_W"]
        layout["FREE_GRID_X"] = layout["SIDEBAR_W"] + (canvas_avail_w - grid_w_px) // 2

def calculate_profit(assets=None):
    """
    assets is optional so existing calls without it still work, but callers
    that want NACG-28's loss-streak warnings (and the routine "Turn
    committed!" message) should pass assets in.
    """
    global free_profit, free_city, consecutive_losses
    global loss_warning_shown, loss_warning_popup_active, loss_warning_sidebar_active
    rows = len(free_city)
    cols = len(free_city[0])
    
    income = 0
    upkeep = 0

    visited_r = [[False] * cols for _ in range(rows)]
    
    for r in range(rows):
        for c in range(cols):
            b_type = free_city[r][c]
            if b_type == ' ':
                continue
            
            if b_type == 'R':
                income += 1
                if not visited_r[r][c]:
                    upkeep += 1  
                    queue = [(r, c)]
                    visited_r[r][c] = True
                    while queue:
                        curr_r, curr_c = queue.pop(0)
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nr, nc = curr_r + dr, curr_c + dc
                            if 0 <= nr < rows and 0 <= nc < cols:
                                if free_city[nr][nc] == 'R' and not visited_r[nr][nc]:
                                    visited_r[nr][nc] = True
                                    queue.append((nr, nc))
            elif b_type == 'I':
                income += 2
                upkeep += 1
            elif b_type == 'C':
                income += 3
                upkeep += 2
            elif b_type == 'O':
                upkeep += 1
            elif b_type == '*':
                has_neighbor_road = False
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and free_city[nr][nc] == '*':
                        has_neighbor_road = True
                        break
                if not has_neighbor_road:
                    upkeep += 1

    free_profit += (income - upkeep)

    #tracking consecutive loss
    if income < upkeep:
        consecutive_losses += 1
    else:
        consecutive_losses = 0

    if consecutive_losses >= 20:
        return True  # triggers game over

    # NACG-28: As a player in Free Play Mode, I want the game to warn me
    # when I have made a loss for 15 consecutive turns, so I can make
    # changes before the game ends. Purely informational - reuses the
    # existing non-blocking message bar, and goes quiet on its own once
    # consecutive_losses resets to 0 above (i.e. the moment a turn is
    # profitable again), matching "warning is dismissed until it triggers
    # point 1 again".
    # NACG-28: As a player in Free Play Mode, I want the game to warn me
    # when I have made a loss for 15 consecutive turns, so I can make
    # changes before the game ends. Mirrors NACG-29's pattern: a blocking
    # centre-screen popup fires once per streak (acknowledged via
    # [UNDERSTOOD]), then a permanent sidebar reminder takes over and keeps
    # counting down each turn. Both switch off automatically the moment
    # consecutive_losses resets to 0 above (i.e. a profitable turn),
    # matching "warning is dismissed until it triggers point 1 again".
    if consecutive_losses >= 15:
        if not loss_warning_shown:
            loss_warning_shown = True
            loss_warning_popup_active = True
        loss_warning_sidebar_active = True
    else:
        loss_warning_shown = False
        loss_warning_sidebar_active = False

    if assets and consecutive_losses < 15:
        assets["system"]["set_msg"]("Turn committed! Finances recalculated.")

    return False

def check_and_expand_grid(r, c, const, layout, assets):
    """
    Checks if a building was built on the outer perimeter border bounds.
    If true, pads 5 empty rows/columns around all perimeters up to 15x15 then 25x25.
    Also resizes cell layouts on-the-fly to fit screen view constraints cleanly.
    """
    global free_city
    current_rows = const["FREE_ROWS"]
    current_cols = const["FREE_COLS"]
    
    # Check if placement hit any perimeter border layer
    if r == 0 or r == current_rows - 1 or c == 0 or c == current_cols - 1:
        if current_rows == 5:
            new_size = 15
            layout["FREE_CELL"] = 32  # Downscale square dimensions to fit layout comfortably
            assets["system"]["set_msg"]("Border reached! City expanded to 15x15 perimeter.")
        elif current_rows == 15:
            new_size = 25
            layout["FREE_CELL"] = 20  # Extreme compression scaling for massive 25x25 rendering
            assets["system"]["set_msg"]("Border reached! City expanded to massive 25x25 perimeter.")
        else:
            return  # Maximum expansion threshold achieved caps at 25x25

        # Create padded grid layout housing central state offsets
        pad = 5
        new_grid = [[' '] * new_size for _ in range(new_size)]
        
        for old_r in range(current_rows):
            for old_c in range(current_cols):
                new_grid[old_r + pad][old_c + pad] = free_city[old_r][old_c]
                
        free_city = new_grid
        const["FREE_ROWS"] = new_size
        const["FREE_COLS"] = new_size
        
        # Center the newly-resized map coordinate origins on-screen dynamically 
        grid_w_px = new_size * layout["FREE_CELL"]
        canvas_avail_w = assets["SCREEN_W"] - layout["SIDEBAR_W"]
        layout["FREE_GRID_X"] = layout["SIDEBAR_W"] + (canvas_avail_w - grid_w_px) // 2

def draw_grid(screen, grid, rows, cols, gx, gy, cell_px, mouse_pos, colors, fonts, hoverable, target_cell=None):
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
            
            if grid[r][c] != ' ':
                bc = colors["BUILDING_COLORS"].get(grid[r][c], (255, 255, 255))
                # Scale physical visual token items layout bounds automatically to adapt cell shrink thresholds
                rect_w = max(12, int(cell_px * 0.45))
                rect_h = max(24, int(cell_px * 0.90))
                bldg_rect = pygame.Rect(cr.centerx - rect_w // 2, cr.centery - rect_h // 2, rect_w, rect_h)
                pygame.draw.rect(screen, bc, bldg_rect, border_radius=2 if cell_px < 30 else 4)
                
                # Dynamic text scaling check so letters don't bleed out of small cards
                font_node = fonts["tiny"] if cell_px < 25 else fonts["small"]
                s = font_node.render(grid[r][c], True, (10, 10, 10))
                screen.blit(s, s.get_rect(center=bldg_rect.center))
            
            # Draw highlight overlay around target demolition candidate cell
            if target_cell == (r, c):
                pygame.draw.rect(screen, colors.get("GREEN_NEON", (50, 255, 50)), cr, 2 if cell_px < 30 else 3)

def update(events, mouse_pos, assets):
    global free_turn, free_profit, show_fp_overlay, fp_overlay_timer, selected_bldg, placement_mode, free_city, selected_grid_cell
    global consecutive_losses, loss_warning_shown, loss_warning_popup_active, loss_warning_sidebar_active
    next_state = "freeplay"
    
    screen = assets["screen"]
    utils = assets["utils"]
    fonts = assets["fonts"]
    colors = assets["colors"]
    layout = assets["layout"]
    const = assets["constants"]

    screen.fill((5, 14, 8))
    utils["draw_header"]("FREE PLAY MODE", t_color=colors["GREEN_NEON"], bg=(0, 24, 8), line_color=colors["GREEN_NEON"])
    
    # --- TOP RIGHT STATS PLACEMENT ---
    s_t = fonts["medium"].render(f"TURN: {free_turn}", True, (255, 255, 255))
    p_color = colors["GREEN_NEON"] if free_profit >= 0 else colors["RED"]
    s_p = fonts["medium"].render(f"PROFIT: {free_profit:+d}", True, p_color)
    
    top_right_x = assets["SCREEN_W"] - max(s_t.get_width(), s_p.get_width()) - 20
    screen.blit(s_t, (top_right_x, 12))
    screen.blit(s_p, (top_right_x, 38))

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
    for idx, b_char in enumerate(['R', 'I', 'C', 'O', '*']):
        lbl_h = fonts["tiny"].render(f"Press [{b_char}]", True, (120, 150, 130))
        screen.blit(lbl_h, (layout["SIDEBAR_W"] - 95, layout["HEADER_H"] + 48 + (idx * 44)))

    if loss_warning_sidebar_active:
        warn_box = pygame.Rect(10, assets["SCREEN_H"] - 214, layout["SIDEBAR_W"] - 20, 44)
        pygame.draw.rect(screen, (60, 15, 15), warn_box, border_radius=4)
        pygame.draw.rect(screen, (255, 90, 90), warn_box, 2, border_radius=4)
        if consecutive_losses == 15:
            line2 = "Ends in 5 turns if this continues!"
        else:
            turns_remaining = max(0, 20 - consecutive_losses)
            line2 = f"{turns_remaining} turn(s) left before game over!"
        utils["draw_text_c"]("WARNING: LOSS STREAK", fonts["tiny"], (255, 130, 130), warn_box.centerx, warn_box.y + 14)
        utils["draw_text_c"](line2, fonts["tiny"], (255, 130, 130), warn_box.centerx, warn_box.y + 30)

    # --- Sidebar Action Buttons Positioning Control Layout ---
    end_turn_r = pygame.Rect(10, assets["SCREEN_H"] - 165, layout["SIDEBAR_W"] - 20, 42)
    utils["draw_btn"](end_turn_r, "[E]  END TURN", fonts["medium"], mouse_pos, color=colors["GOLD"])

    demo_r = pygame.Rect(10, assets["SCREEN_H"] - 115, layout["SIDEBAR_W"] - 20, 35)
    utils["draw_btn"](demo_r, "[D]  DEMOLISH", fonts["small"], mouse_pos, color=(180, 60, 60))

    menu_r = pygame.Rect(10, assets["SCREEN_H"] - 68, layout["SIDEBAR_W"] - 20, 40)
    utils["draw_btn"](menu_r, "[Q]  MAIN MENU", fonts["small"], mouse_pos, color=colors["GREEN_NEON"])

    draw_grid(screen, free_city, const["FREE_ROWS"], const["FREE_COLS"],
              layout["FREE_GRID_X"], layout["FREE_GRID_Y"], layout["FREE_CELL"], mouse_pos, colors, fonts, 
              hoverable=placement_mode, target_cell=selected_grid_cell)
    utils["draw_grid_labels"](const["FREE_ROWS"], const["FREE_COLS"], layout["FREE_GRID_X"], layout["FREE_GRID_Y"], layout["FREE_CELL"])

    # Small, always-on readout so the player can track the streak from turn 1,
    # separate from the pop-up/sidebar warning which only appears at 15+.
    loss_line_y = layout["FREE_GRID_Y"] + (const["FREE_ROWS"] * layout["FREE_CELL"]) + 58
    loss_line_color = (255, 130, 130) if consecutive_losses >= 15 else (150, 150, 170)
    loss_line = fonts["tiny"].render(f"Consecutive turns with losses: {consecutive_losses}", True, loss_line_color)
    screen.blit(loss_line, (layout["FREE_GRID_X"], loss_line_y))

    if placement_mode and selected_bldg:
        cell = utils["grid_cell_at"](*mouse_pos, layout["FREE_GRID_X"], layout["FREE_GRID_Y"], layout["FREE_CELL"], const["FREE_ROWS"], const["FREE_COLS"])
        rect_w = max(12, int(layout["FREE_CELL"] * 0.45))
        rect_h = max(24, int(layout["FREE_CELL"] * 0.90))
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
        font_node = fonts["tiny"] if layout["FREE_CELL"] < 25 else fonts["small"]
        lbl = font_node.render(selected_bldg, True, (10, 10, 10))
        screen.blit(lbl, lbl.get_rect(center=p_rect.center))

    if show_fp_overlay:
        fp_overlay_timer -= 1
        if fp_overlay_timer <= 0:
            show_fp_overlay = False
        utils["draw_retro_popup"]([
            "FREE PLAY: Unlimited coins on a 5x5 grid.",
            "Place buildings, then click 'END TURN' to compute profits.",
            "Build on a border cell to expand the perimeter:",
            "1st Expansion -> 15x15  |  2nd Expansion -> 25x25"
        ])

    # NACG-28: centre-screen blocking popup for the 15-turn loss-streak warning
    loss_understood_r = None
    if loss_warning_popup_active:
        dim = pygame.Surface((assets["SCREEN_W"], assets["SCREEN_H"]), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 165))
        screen.blit(dim, (0, 0))

        box_w, box_h = 500, 220
        box_rect = pygame.Rect((assets["SCREEN_W"] - box_w) // 2, (assets["SCREEN_H"] - box_h) // 2, box_w, box_h)
        pygame.draw.rect(screen, (10, 25, 12), box_rect, border_radius=10)
        pygame.draw.rect(screen, (255, 90, 90), box_rect, 3, border_radius=10)

        utils["draw_text_c"]("⚠  LOSS STREAK WARNING", fonts["medium"], (255, 90, 90), box_rect.centerx, box_rect.y + 45)
        utils["draw_text_c"]("Net loss for 15 consecutive turns!", fonts["small"], (255, 255, 255), box_rect.centerx, box_rect.y + 95)
        utils["draw_text_c"]("Game will end in 5 turns if this continues.", fonts["tiny"], (220, 220, 220), box_rect.centerx, box_rect.y + 120)

        loss_understood_r = pygame.Rect(box_rect.centerx - 90, box_rect.bottom - 55, 180, 42)
        utils["draw_btn"](loss_understood_r, "UNDERSTOOD", fonts["small"], mouse_pos, color=(255, 90, 90))

    for event in events:
        if loss_warning_popup_active:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and loss_understood_r and loss_understood_r.collidepoint(mouse_pos):
                loss_warning_popup_active = False
            continue  # swallow all other input while the popup must be acknowledged

        if show_fp_overlay and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            show_fp_overlay = False
            fp_overlay_timer = 0
            continue

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                reset(assets)  #reset everything back to 5x5 layout (to fix bug)
                pygame.event.clear()  #clear out lingering inputs
                return "main_menu", {'menu': menu_r, 'demolish': demo_r, 'end_turn': end_turn_r, **bldg_btns}
            elif event.key == pygame.K_r: 
                selected_bldg = 'R'
                placement_mode = True
                selected_grid_cell = None
            elif event.key == pygame.K_i: 
                selected_bldg = 'I'
                placement_mode = True
                selected_grid_cell = None
            elif event.key == pygame.K_c: 
                selected_bldg = 'C'
                placement_mode = True
                selected_grid_cell = None
            elif event.key == pygame.K_o: 
                selected_bldg = 'O'
                placement_mode = True
                selected_grid_cell = None
            elif event.key == pygame.K_8 or event.key == pygame.K_KP_MULTIPLY: 
                selected_bldg = '*'
                placement_mode = True
                selected_grid_cell = None
            elif event.key == pygame.K_ESCAPE: 
                selected_bldg = None
                placement_mode = False
            
            # Hotkey: [E] for End Turn
            elif event.key == pygame.K_e:
                free_turn += 1
                if calculate_profit(assets):
                    next_state = "game_over"
                selected_bldg = None
                placement_mode = False
                selected_grid_cell = None
                
            # Hotkey: [D] for Demolish
            elif event.key == pygame.K_d:
                if selected_grid_cell is not None:
                    dr, dc = selected_grid_cell
                    removed_type = free_city[dr][dc]
                    free_city[dr][dc] = ' '
                    free_profit -= 1  
                    assets["system"]["set_msg"](f"Demolished {removed_type} (-1 coin). Click 'End Turn' to update financials.")
                    selected_grid_cell = None
                else:
                    assets["system"]["set_msg"]("Please select a building to demolish")

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if menu_r.collidepoint(mouse_pos):
                reset(assets)  #reset layout parameters
                pygame.event.clear()  #clear clicks so they don't bleed onto menu items
                return "main_menu", {'menu': menu_r, 'demolish': demo_r, 'end_turn': end_turn_r, **bldg_btns}

            # Check explicit End Turn Commit click
            if end_turn_r.collidepoint(mouse_pos):
                free_turn += 1
                if calculate_profit(assets):
                    reset(assets)  # wipes grid back to 5x5 so game_over won't crash on reload!
                    pygame.event.clear()
                    return "game_over", {'menu': menu_r, 'demolish': demo_r, 'end_turn': end_turn_r, **bldg_btns}

                selected_bldg = None
                placement_mode = False
                selected_grid_cell = None
                continue

            # Process explicit Demolish Event Command Click Loop
            if demo_r.collidepoint(mouse_pos):
                if selected_grid_cell is not None:
                    dr, dc = selected_grid_cell
                    removed_type = free_city[dr][dc]
                    free_city[dr][dc] = ' '
                    free_profit -= 1  
                    assets["system"]["set_msg"](f"Demolished {removed_type} (-1 coin). Click 'End Turn' to update financials.")
                    selected_grid_cell = None
                else:
                    assets["system"]["set_msg"]("Please select a building to demolish")
                continue

            btn_clicked = False
            for b_key, b_rect in bldg_btns.items():
                if b_rect.collidepoint(mouse_pos):
                    selected_bldg = b_key
                    placement_mode = True
                    selected_grid_cell = None
                    btn_clicked = True
                    break

            if not btn_clicked:
                cell = utils["grid_cell_at"](*mouse_pos, layout["FREE_GRID_X"], layout["FREE_GRID_Y"], layout["FREE_CELL"], const["FREE_ROWS"], const["FREE_COLS"])
                if cell:
                    r, c = cell
                    if placement_mode and selected_bldg:
                        if free_city[r][c] == ' ':
                            free_city[r][c] = selected_bldg
                            # Trigger perimeter layout check immediately on construction placement loop
                            check_and_expand_grid(r, c, const, layout, assets)
                            selected_bldg = None
                            placement_mode = False
                        else:
                            assets["system"]["set_msg"]("Cell is already occupied.")
                    else:
                        # Select an existing building to target for demolition
                        if free_city[r][c] != ' ':
                            selected_grid_cell = (r, c)
                            assets["system"]["set_msg"](f"Selected {free_city[r][c]} cell. Ready to Demolish.")
                        else:
                            selected_grid_cell = None

    # UI Rendering Layer for the notification box
    msg, m_timer = assets["system"]["get_msg"]()
    if m_timer > 0:
        s_msg = fonts["small"].render(msg, True, (10, 10, 10))
        
        pad_x, pad_y = 12, 8
        box_w = s_msg.get_width() + (pad_x * 2)
        box_h = s_msg.get_height() + (pad_y * 2)
        
        box_x = layout["FREE_GRID_X"]
        box_y = layout["FREE_GRID_Y"] + (const["FREE_ROWS"] * layout["FREE_CELL"]) + 15
        
        msg_box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        
        pygame.draw.rect(screen, (255, 255, 255), msg_box_rect, border_radius=2)
        pygame.draw.rect(screen, (0, 0, 0), msg_box_rect, 1, border_radius=2)
        
        screen.blit(s_msg, (box_x + pad_x, box_y + pad_y))

    return next_state, {'menu': menu_r, 'demolish': demo_r, 'end_turn': end_turn_r, **bldg_btns}

