import pygame
import save_manager

# Domain runtime storage data scopes
free_city = []
free_turn = 1
free_profit = 0
free_score = 0
free_upkeep = 0  
demolition_penalty = 0  
show_fp_overlay = False
fp_overlay_timer = 0
selected_bldg = None
placement_mode = False
selected_grid_cell = None  
consecutive_losses = 0  
loss_warning_shown = False  
loss_warning_popup_active = False  
loss_warning_sidebar_active = False  

# --- Save Dialog States ---
show_save_dialog = False
show_overwrite_dialog = False
save_filename_input = ""
save_dialog_error = ""

def init_mode(assets_ref):
    global free_city, selected_grid_cell, free_score, demolition_penalty, free_upkeep
    c = assets_ref["constants"]
    c["FREE_ROWS"] = 5
    c["FREE_COLS"] = 5
    free_city = [[' '] * c["FREE_COLS"] for _ in range(c["FREE_ROWS"])]
    selected_grid_cell = None
    free_score = 0
    free_upkeep = 0
    demolition_penalty = 0

def reset(assets=None):
    global free_city, free_turn, free_profit, free_score, free_upkeep, demolition_penalty, show_fp_overlay, fp_overlay_timer, selected_bldg, placement_mode, selected_grid_cell, consecutive_losses
    global loss_warning_shown, loss_warning_popup_active, loss_warning_sidebar_active
    global show_save_dialog, show_overwrite_dialog, save_filename_input, save_dialog_error

    free_city = [[' '] * 5 for _ in range(5)]
    free_turn = 1
    free_profit = 0
    free_score = 0
    free_upkeep = 0
    demolition_penalty = 0
    consecutive_losses = 0 
    loss_warning_shown = False
    loss_warning_popup_active = False
    loss_warning_sidebar_active = False
    selected_bldg = None
    placement_mode = False
    show_fp_overlay = True
    fp_overlay_timer = 360  
    selected_grid_cell = None

    show_save_dialog = False
    show_overwrite_dialog = False
    save_filename_input = ""
    save_dialog_error = ""

    if assets:
        const = assets["constants"]
        layout = assets["layout"]
        const["FREE_ROWS"] = 5
        const["FREE_COLS"] = 5
        layout["FREE_CELL"] = 90  
        grid_w_px = 5 * layout["FREE_CELL"]
        canvas_avail_w = assets["SCREEN_W"] - layout["SIDEBAR_W"]
        layout["FREE_GRID_X"] = layout["SIDEBAR_W"] + (canvas_avail_w - grid_w_px) // 2

def get_adjacent_buildings(r, c, grid):
    rows = len(grid)
    cols = len(grid[0])
    adj_coords = set()

    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            if grid[nr][nc] != ' ' and (nr, nc) != (r, c):
                adj_coords.add((nr, nc))

    adjacent_road_tiles = [
        (r + dr, c + dc) for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if 0 <= r + dr < rows and 0 <= c + dc < cols and grid[r + dr][c + dc] == '*'
    ]

    if adjacent_road_tiles:
        visited_roads = set()
        for road_r, road_c in adjacent_road_tiles:
            if (road_r, road_c) not in visited_roads:
                queue = [(road_r, road_c)]
                visited_roads.add((road_r, road_c))
                while queue:
                    curr_r, curr_c = queue.pop(0)
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = curr_r + dr, curr_c + dc
                        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == '*':
                            if (nr, nc) not in visited_roads:
                                visited_roads.add((nr, nc))
                                queue.append((nr, nc))

        for rr, rc in visited_roads:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = rr + dr, rc + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    if grid[nr][nc] != ' ' and (nr, nc) != (r, c):
                        adj_coords.add((nr, nc))

    return adj_coords

def calculate_score(grid):
    rows = len(grid)
    cols = len(grid[0])
    total_score = 0
    total_industry = sum(cell == 'I' for row in grid for cell in row)
    visited_roads_global = set()

    for r in range(rows):
        for c in range(cols):
            b_type = grid[r][c]
            if b_type == ' ':
                continue
            if b_type == 'I':
                total_score += total_industry
            elif b_type == '*':
                if (r, c) not in visited_roads_global:
                    queue = [(r, c)]
                    road_cluster = {(r, c)}
                    while queue:
                        curr_r, curr_c = queue.pop(0)
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nr, nc = curr_r + dr, curr_c + dc
                            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == '*' and (nr, nc) not in road_cluster:
                                road_cluster.add((nr, nc))
                                queue.append((nr, nc))
                    visited_roads_global.update(road_cluster)
                    for rr, rc in road_cluster:
                        row_connected_roads = sum(1 for (xr, xc) in road_cluster if xr == rr and xc != rc)
                        total_score += row_connected_roads
            else:
                adj_coords = get_adjacent_buildings(r, c, grid)
                adj_types = [grid[ar][ac] for ar, ac in adj_coords]
                if b_type == 'R':
                    if 'I' in adj_types:
                        total_score += 1
                    else:
                        r_or_c_count = sum(1 for t in adj_types if t in ('R', 'C'))
                        o_count = sum(1 for t in adj_types if t == 'O')
                        total_score += (r_or_c_count * 1) + (o_count * 2)
                elif b_type == 'C':
                    c_count = sum(1 for t in adj_types if t == 'C')
                    total_score += c_count
                elif b_type == 'O':
                    o_count = sum(1 for t in adj_types if t == 'O')
                    total_score += o_count

    return total_score

def get_current_upkeep_and_income():
    rows = len(free_city)
    cols = len(free_city[0])
    income = 0
    upkeep = demolition_penalty
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

    return income, upkeep

def calculate_profit(assets=None):
    global free_profit, free_city, consecutive_losses, free_score, demolition_penalty, free_upkeep
    global loss_warning_shown, loss_warning_popup_active, loss_warning_sidebar_active

    income, upkeep = get_current_upkeep_and_income()
    free_upkeep = upkeep
    net_turn_profit = income - upkeep
    free_profit += net_turn_profit  
    demolition_penalty = 0  
    free_score = calculate_score(free_city)

    if net_turn_profit < 0:
        consecutive_losses += 1
    else:
        consecutive_losses = 0

    if consecutive_losses >= 20:
        return True  

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
    global free_city
    current_rows = const["FREE_ROWS"]
    current_cols = const["FREE_COLS"]
    
    if r == 0 or r == current_rows - 1 or c == 0 or c == current_cols - 1:
        if current_rows == 5:
            new_size = 15
            layout["FREE_CELL"] = 32  
            assets["system"]["set_msg"]("Border reached! City expanded to 15x15 perimeter.")
        elif current_rows == 15:
            new_size = 25
            layout["FREE_CELL"] = 20  
            assets["system"]["set_msg"]("Border reached! City expanded to massive 25x25 perimeter.")
        else:
            return  

        pad = 5
        new_grid = [[' '] * new_size for _ in range(new_size)]
        for old_r in range(current_rows):
            for old_c in range(current_cols):
                new_grid[old_r + pad][old_c + pad] = free_city[old_r][old_c]
                
        free_city = new_grid
        const["FREE_ROWS"] = new_size
        const["FREE_COLS"] = new_size
        
        grid_w_px = new_size * layout["FREE_CELL"]
        canvas_avail_w = assets["SCREEN_W"] - layout["SIDEBAR_W"]
        layout["FREE_GRID_X"] = layout["SIDEBAR_W"] + (canvas_avail_w - grid_w_px) // 2

def draw_grid(screen, grid, rows, cols, gx, gy, cell_px, mouse_pos, colors, fonts, hoverable, target_cell=None):
    for r in range(rows):
        for c in range(cols):
            cr = pygame.Rect(gx + c * cell_px, gy + r * cell_px, cell_px, cell_px)
            is_hover = cr.collidepoint(mouse_pos) and hoverable
            bg = colors["CELL_HOVER"] if is_hover else (colors["CELL_OCCUPIED"] if grid[r][c] != ' ' else colors["CELL_EMPTY"])
                
            pygame.draw.rect(screen, bg, cr)
            pygame.draw.rect(screen, colors["GRID_LINE"], cr, 1)
            
            if grid[r][c] != ' ':
                bc = colors["BUILDING_COLORS"].get(grid[r][c], (255, 255, 255))
                rect_w = max(12, int(cell_px * 0.45))
                rect_h = max(24, int(cell_px * 0.90))
                bldg_rect = pygame.Rect(cr.centerx - rect_w // 2, cr.centery - rect_h // 2, rect_w, rect_h)
                pygame.draw.rect(screen, bc, bldg_rect, border_radius=2 if cell_px < 30 else 4)
                
                font_node = fonts["tiny"] if cell_px < 25 else fonts["small"]
                s = font_node.render(grid[r][c], True, (10, 10, 10))
                screen.blit(s, s.get_rect(center=bldg_rect.center))
            
            if target_cell == (r, c):
                pygame.draw.rect(screen, colors.get("GREEN_NEON", (50, 255, 50)), cr, 2 if cell_px < 30 else 3)

def do_save(assets):
    global save_filename_input, save_dialog_error, show_save_dialog, show_overwrite_dialog
    if not save_filename_input.strip():
        save_dialog_error = "Error: Filename cannot be empty!"
        assets["system"]["set_msg"](save_dialog_error)
        return False
    
    ok, msg = save_manager.save_freeplay(
        save_filename_input,
        free_turn,
        free_profit,
        free_score,
        free_city,
        consecutive_losses,
        loss_warning_shown,
        loss_warning_sidebar_active
    )
    if ok:
        assets["system"]["set_msg"](msg)
        show_save_dialog = False
        show_overwrite_dialog = False
        save_filename_input = ""
        save_dialog_error = ""
        return True
    else:
        save_dialog_error = msg
        assets["system"]["set_msg"](msg)
        return False

def update(events, mouse_pos, assets):
    global free_turn, free_profit, free_score, free_upkeep, show_fp_overlay, fp_overlay_timer, selected_bldg, placement_mode, free_city, selected_grid_cell, demolition_penalty
    global consecutive_losses, loss_warning_shown, loss_warning_popup_active, loss_warning_sidebar_active
    global show_save_dialog, show_overwrite_dialog, save_filename_input, save_dialog_error

    next_state = "freeplay"
    screen = assets["screen"]
    utils = assets["utils"]
    fonts = assets["fonts"]
    colors = assets["colors"]
    layout = assets["layout"]
    const = assets["constants"]

    screen.fill((8, 3, 18))

    header_color = colors.get("NEON_GREEN", (57, 255, 20))
    header_font = fonts.get("large", fonts.get("large", fonts["medium"]))
    header_surf = header_font.render("FREE PLAY MODE", True, header_color)
    header_rect = header_surf.get_rect(center=(assets["SCREEN_W"] // 2, layout["HEADER_H"] // 2))
    screen.blit(header_surf, header_rect)

    s_score = fonts["medium"].render(f"SCORE: {free_score}", True, colors["GREEN_NEON"])
    p_color = colors["GREEN_NEON"] if free_profit >= 0 else colors["RED"]
    s_p = fonts["medium"].render(f"PROFIT: {free_profit:+d}", True, p_color)
    s_t = fonts["medium"].render(f"TURN: {free_turn}", True, (255, 255, 255))

    margin, gap = 20, 24
    t_x = assets["SCREEN_W"] - margin - s_t.get_width()
    p_x = t_x - gap - s_p.get_width()

    screen.blit(s_p, (p_x, layout["HEADER_H"] // 2 - s_p.get_height() // 2))
    screen.blit(s_t, (t_x, layout["HEADER_H"] // 2 - s_t.get_height() // 2))
    screen.blit(s_score, (20, layout["HEADER_H"] // 2 - s_score.get_height() // 2))

    utils["draw_sidebar_panel"]()

    SY = layout["HEADER_H"] + 14
    screen.blit(fonts["small"].render("SELECT A BUILDING:", True, colors["CYBER_CYAN"]), (10, SY))
    SY += 24

    bldg_btns = {}
    btn_h = 44
    for idx, b in enumerate(const["BUILDINGS"]):
        key_label = str(idx + 1)
        btn_r = pygame.Rect(10, SY, layout["SIDEBAR_W"] - 20, btn_h)
        active = (selected_bldg == b)
        hover = btn_r.collidepoint(mouse_pos) or active
        bc = colors["BUILDING_COLORS"].get(b, (255, 255, 255))
        pygame.draw.rect(screen, colors["CYBER_CYAN"] if hover else (40, 12, 72), btn_r, border_radius=4)
        pygame.draw.rect(screen, bc, btn_r, 2, border_radius=4)
        utils["draw_text_c"](f"[{key_label}]  {b}", fonts["large"], (10, 10, 10) if hover else (255, 255, 255), btn_r.centerx, btn_r.centery)
        bldg_btns[b] = btn_r
        SY += btn_h + 6

    SY += 6
    if placement_mode and selected_bldg:
        utils["draw_text_c"](f"Placing: {selected_bldg}", fonts["small"], colors["GREEN_NEON"], layout["SIDEBAR_W"] // 2, SY)
        utils["draw_text_c"]("Click the grid to place", fonts["tiny"], colors["GREEN_NEON"], layout["SIDEBAR_W"] // 2, SY + 18)
    elif selected_grid_cell is not None:
        utils["draw_text_c"]("Building selected", fonts["small"], (255, 100, 100), layout["SIDEBAR_W"] // 2, SY)
        utils["draw_text_c"]("Press [D] to demolish", fonts["tiny"], (255, 100, 100), layout["SIDEBAR_W"] // 2, SY + 18)
    elif selected_bldg:
        utils["draw_text_c"](f"Selected: {selected_bldg}", fonts["small"], colors["GOLD"], layout["SIDEBAR_W"] // 2, SY)
    else:
        utils["draw_text_c"]("Pick a building above", fonts["tiny"], (120, 120, 155), layout["SIDEBAR_W"] // 2, SY)

    utils["draw_legend"](10, SY + 42)

    msg, m_timer = assets["system"]["get_msg"]()
    if m_timer > 0:
        is_err = any(w in msg for w in ("occupied", "select", "Please", "Invalid", "Error", "empty"))
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

    if loss_warning_sidebar_active:
        warn_box = pygame.Rect(10, assets["SCREEN_H"] - 214, layout["SIDEBAR_W"] - 20, 44)
        pygame.draw.rect(screen, (60, 15, 15), warn_box, border_radius=4)
        pygame.draw.rect(screen, (255, 90, 90), warn_box, 2, border_radius=4)
        line2 = "Ends in 5 turns if this continues!" if consecutive_losses == 15 else f"{max(0, 20 - consecutive_losses)} turn(s) left before game over!"
        utils["draw_text_c"]("WARNING: LOSS STREAK", fonts["tiny"], (255, 130, 130), warn_box.centerx, warn_box.y + 14)
        utils["draw_text_c"](line2, fonts["tiny"], (255, 130, 130), warn_box.centerx, warn_box.y + 30)

    # --- Sidebar Action Buttons ---
    menu_r = pygame.Rect(10, assets["SCREEN_H"] - 55, layout["SIDEBAR_W"] - 20, 38)
    utils["draw_btn"](menu_r, "[Q]  MAIN MENU", fonts["small"], mouse_pos, color=(220, 50, 50))

    save_r = pygame.Rect(10, assets["SCREEN_H"] - 100, layout["SIDEBAR_W"] - 20, 38)
    utils["draw_btn"](save_r, "[S]  SAVE GAME", fonts["small"], mouse_pos, color=colors["CYBER_CYAN"])

    demo_r = pygame.Rect(10, assets["SCREEN_H"] - 145, layout["SIDEBAR_W"] - 20, 38)
    utils["draw_btn"](demo_r, "[D]  DEMOLISH", fonts["small"], mouse_pos, color=(180, 60, 60))

    end_turn_r = pygame.Rect(10, assets["SCREEN_H"] - 190, layout["SIDEBAR_W"] - 20, 38)
    utils["draw_btn"](end_turn_r, "[E]  END TURN", fonts["small"], mouse_pos, color=colors["GOLD"])
    
    draw_grid(screen, free_city, const["FREE_ROWS"], const["FREE_COLS"],
              layout["FREE_GRID_X"], layout["FREE_GRID_Y"], layout["FREE_CELL"], mouse_pos, colors, fonts, 
              hoverable=placement_mode, target_cell=selected_grid_cell)
    utils["draw_grid_labels"](const["FREE_ROWS"], const["FREE_COLS"], layout["FREE_GRID_X"], layout["FREE_GRID_Y"], layout["FREE_CELL"])

    loss_line_y = layout["FREE_GRID_Y"] + (const["FREE_ROWS"] * layout["FREE_CELL"]) + 58
    loss_line_color = (255, 80, 80) if consecutive_losses >= 15 else (255, 220, 60)
    loss_line = fonts["small"].render(f"Consecutive turns with losses: {consecutive_losses}", True, loss_line_color)
    screen.blit(loss_line, (layout["FREE_GRID_X"], loss_line_y))

    _, active_upkeep = get_current_upkeep_and_income()
    upkeep_surf = fonts["small"].render(f"UPKEEP: {active_upkeep}", True, (255, 90, 90) if active_upkeep > 0 else (200, 200, 200))
    upkeep_x = assets["SCREEN_W"] - upkeep_surf.get_width() - 40
    screen.blit(upkeep_surf, (upkeep_x, loss_line_y))

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

    # --- SAVE GAME DIALOG MODAL ---
    sd_confirm_btn, sd_cancel_btn = None, None
    if show_save_dialog and not show_overwrite_dialog:
        dim = pygame.Surface((assets["SCREEN_W"], assets["SCREEN_H"]), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        screen.blit(dim, (0, 0))

        box_w, box_h = 440, 260
        box_rect = pygame.Rect((assets["SCREEN_W"] - box_w) // 2, (assets["SCREEN_H"] - box_h) // 2, box_w, box_h)
        pygame.draw.rect(screen, (14, 0, 32), box_rect, border_radius=10)
        pygame.draw.rect(screen, colors["CYBER_CYAN"], box_rect, 2, border_radius=10)

        utils["draw_text_c"]("SAVE GAME", fonts["medium"], colors["CYBER_CYAN"], box_rect.centerx, box_rect.y + 35)
        utils["draw_text_c"]("Enter a custom filename:", fonts["small"], (220, 220, 220), box_rect.centerx, box_rect.y + 70)

        # Text Field Input
        input_box = pygame.Rect(box_rect.centerx - 160, box_rect.y + 98, 320, 40)
        pygame.draw.rect(screen, (30, 10, 55), input_box, border_radius=4)
        pygame.draw.rect(screen, colors["CYBER_CYAN"], input_box, 2, border_radius=4)
        txt_s = fonts["small"].render(save_filename_input + "|", True, (255, 255, 255))
        screen.blit(txt_s, txt_s.get_rect(midleft=(input_box.x + 10, input_box.centery)))

        if save_dialog_error:
            utils["draw_text_c"](save_dialog_error, fonts["tiny"], (255, 80, 80), box_rect.centerx, box_rect.y + 150)

        sd_confirm_btn = pygame.Rect(box_rect.centerx - 145, box_rect.y + 185, 130, 40)
        sd_cancel_btn = pygame.Rect(box_rect.centerx + 15, box_rect.y + 185, 130, 40)

        utils["draw_btn"](sd_confirm_btn, "CONFIRM", fonts["small"], mouse_pos, color=colors["GREEN_NEON"])
        utils["draw_btn"](sd_cancel_btn, "CANCEL", fonts["small"], mouse_pos, color=(220, 50, 50))

    # --- OVERWRITE PROMPT DIALOG MODAL ---
    ow_yes_btn, ow_no_btn = None, None
    if show_overwrite_dialog:
        dim = pygame.Surface((assets["SCREEN_W"], assets["SCREEN_H"]), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 190))
        screen.blit(dim, (0, 0))

        box_w, box_h = 460, 220
        box_rect = pygame.Rect((assets["SCREEN_W"] - box_w) // 2, (assets["SCREEN_H"] - box_h) // 2, box_w, box_h)
        pygame.draw.rect(screen, (25, 5, 25), box_rect, border_radius=10)
        pygame.draw.rect(screen, colors["RED"], box_rect, 3, border_radius=10)

        utils["draw_text_c"]("⚠ OVERWRITE FILE?", fonts["medium"], colors["RED"], box_rect.centerx, box_rect.y + 40)
        utils["draw_text_c"](f"A save with filename '{save_filename_input}' already exists.", fonts["tiny"], (220, 220, 220), box_rect.centerx, box_rect.y + 80)
        utils["draw_text_c"]("Are you sure you want to overwrite it?", fonts["small"], (255, 255, 255), box_rect.centerx, box_rect.y + 110)

        ow_yes_btn = pygame.Rect(box_rect.centerx - 145, box_rect.y + 150, 130, 40)
        ow_no_btn = pygame.Rect(box_rect.centerx + 15, box_rect.y + 150, 130, 40)

        utils["draw_btn"](ow_yes_btn, "OVERWRITE", fonts["small"], mouse_pos, color=colors["RED"])
        utils["draw_btn"](ow_no_btn, "CANCEL", fonts["small"], mouse_pos)

    # --- INPUT EVENT PROCESSING ---
    for event in events:
        if loss_warning_popup_active:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and loss_understood_r and loss_understood_r.collidepoint(mouse_pos):
                loss_warning_popup_active = False
            continue

        if show_fp_overlay and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            show_fp_overlay = False
            fp_overlay_timer = 0
            continue

        # Overwrite Modal Controls
        if show_overwrite_dialog:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if ow_yes_btn and ow_yes_btn.collidepoint(mouse_pos):
                    do_save(assets)
                elif ow_no_btn and ow_no_btn.collidepoint(mouse_pos):
                    show_overwrite_dialog = False
            continue

        # Save Dialog Modal Controls
        if show_save_dialog:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if not save_filename_input.strip():
                        save_dialog_error = "Error: Filename cannot be empty!"
                        assets["system"]["set_msg"](save_dialog_error)
                    elif save_manager.freeplay_save_exists(save_filename_input):
                        show_overwrite_dialog = True
                    else:
                        do_save(assets)
                elif event.key == pygame.K_ESCAPE:
                    show_save_dialog = False
                    save_dialog_error = ""
                elif event.key == pygame.K_BACKSPACE:
                    save_filename_input = save_filename_input[:-1]
                else:
                    if event.unicode.isprintable() and len(save_filename_input) < 20:
                        save_filename_input += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if sd_confirm_btn and sd_confirm_btn.collidepoint(mouse_pos):
                    if not save_filename_input.strip():
                        save_dialog_error = "Error: Filename cannot be empty!"
                        assets["system"]["set_msg"](save_dialog_error)
                    elif save_manager.freeplay_save_exists(save_filename_input):
                        show_overwrite_dialog = True
                    else:
                        do_save(assets)
                elif sd_cancel_btn and sd_cancel_btn.collidepoint(mouse_pos):
                    show_save_dialog = False
                    save_dialog_error = ""
            continue

        # Standard Gameplay Controls
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                reset(assets)
                pygame.event.clear()
                return "main_menu", {'menu': menu_r, 'demolish': demo_r, 'end_turn': end_turn_r, **bldg_btns}
            elif event.key == pygame.K_s:
                show_save_dialog = True
                save_filename_input = ""
                save_dialog_error = ""
            elif event.key == pygame.K_1: selected_bldg = 'R'; placement_mode = True; selected_grid_cell = None
            elif event.key == pygame.K_2: selected_bldg = 'I'; placement_mode = True; selected_grid_cell = None
            elif event.key == pygame.K_3: selected_bldg = 'C'; placement_mode = True; selected_grid_cell = None
            elif event.key == pygame.K_4: selected_bldg = 'O'; placement_mode = True; selected_grid_cell = None
            elif event.key == pygame.K_5: selected_bldg = '*'; placement_mode = True; selected_grid_cell = None
            elif event.key == pygame.K_e:
                free_turn += 1
                if calculate_profit(assets):
                    reset(assets)
                    pygame.event.clear()
                    return "game_over", {'menu': menu_r, 'demolish': demo_r, 'end_turn': end_turn_r, **bldg_btns}
                selected_bldg = None; placement_mode = False; selected_grid_cell = None
            elif event.key == pygame.K_d:
                if selected_grid_cell is not None:
                    dr, dc = selected_grid_cell
                    removed_type = free_city[dr][dc]
                    free_city[dr][dc] = ' '
                    demolition_penalty += 1  
                    assets["system"]["set_msg"](f"Demolished {removed_type}. End turn to update finances.")
                    selected_grid_cell = None
                else:
                    assets["system"]["set_msg"]("Please select a building to demolish")

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if menu_r.collidepoint(mouse_pos):
                reset(assets)
                pygame.event.clear()
                return "main_menu", {'menu': menu_r, 'demolish': demo_r, 'end_turn': end_turn_r, **bldg_btns}
            
            if save_r.collidepoint(mouse_pos):
                show_save_dialog = True
                save_filename_input = ""
                save_dialog_error = ""
                continue

            if end_turn_r.collidepoint(mouse_pos):
                free_turn += 1
                if calculate_profit(assets):
                    reset(assets)
                    pygame.event.clear()
                    return "game_over", {'menu': menu_r, 'demolish': demo_r, 'end_turn': end_turn_r, **bldg_btns}
                selected_bldg = None; placement_mode = False; selected_grid_cell = None
                continue

            if demo_r.collidepoint(mouse_pos):
                if selected_grid_cell is not None:
                    dr, dc = selected_grid_cell
                    removed_type = free_city[dr][dc]
                    free_city[dr][dc] = ' '
                    demolition_penalty += 1  
                    assets["system"]["set_msg"](f"Demolished {removed_type}. End turn to update finances.")
                    selected_grid_cell = None
                else:
                    assets["system"]["set_msg"]("Please select a building to demolish")
                continue

            btn_clicked = False
            for b_key, b_rect in bldg_btns.items():
                if b_rect.collidepoint(mouse_pos):
                    selected_bldg = b_key; placement_mode = True; selected_grid_cell = None
                    btn_clicked = True
                    break

            if not btn_clicked:
                cell = utils["grid_cell_at"](*mouse_pos, layout["FREE_GRID_X"], layout["FREE_GRID_Y"], layout["FREE_CELL"], const["FREE_ROWS"], const["FREE_COLS"])
                if cell:
                    r, c = cell
                    if placement_mode and selected_bldg:
                        if free_city[r][c] == ' ':
                            free_city[r][c] = selected_bldg
                            check_and_expand_grid(r, c, const, layout, assets)
                            selected_bldg = None; placement_mode = False
                        else:
                            assets["system"]["set_msg"]("Cell is already occupied.")
                    else:
                        if free_city[r][c] != ' ':
                            selected_grid_cell = (r, c)
                            assets["system"]["set_msg"](f"Selected {free_city[r][c]} cell. Press [D] to demolish.")
                        else:
                            selected_grid_cell = None

    return next_state, {'menu': menu_r, 'demolish': demo_r, 'end_turn': end_turn_r, **bldg_btns}

def load_save_file(filepath, assets_ref=None):
    global free_city, free_turn, free_profit, free_score, consecutive_losses, demolition_penalty, free_upkeep
    global loss_warning_shown, loss_warning_sidebar_active, show_fp_overlay

    data, err = save_manager.load_freeplay(filepath)
    if data is None:
        return False, err

    free_turn = data["turn"]
    free_profit = data["profit"]
    free_score = data["score"]
    free_city = data["city"]
    demolition_penalty = 0
    consecutive_losses = data.get("consecutive_losses", 0)
    loss_warning_shown = data.get("loss_warning_shown", False)
    loss_warning_sidebar_active = data.get("loss_warning_sidebar_active", False)
    show_fp_overlay = False  

    if assets_ref:
        rows = data["rows"]
        cols = data["cols"]
        assets_ref["constants"]["FREE_ROWS"] = rows
        assets_ref["constants"]["FREE_COLS"] = cols

        if rows == 5:
            assets_ref["layout"]["FREE_CELL"] = 90
        elif rows == 15:
            assets_ref["layout"]["FREE_CELL"] = 32
        elif rows == 25:
            assets_ref["layout"]["FREE_CELL"] = 20

        grid_w_px = cols * assets_ref["layout"]["FREE_CELL"]
        canvas_avail_w = assets_ref["SCREEN_W"] - assets_ref["layout"]["SIDEBAR_W"]
        assets_ref["layout"]["FREE_GRID_X"] = assets_ref["layout"]["SIDEBAR_W"] + (canvas_avail_w - grid_w_px) // 2

    return True, "Free Play game loaded!"
