import pygame
import random  # to generate different building heights

# 1. Initialization
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 600, 400
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Ngee Ann City - Main Menu")
clock = pygame.time.Clock()

# 2. Retro Font & Color Setup
font_title = pygame.font.SysFont('couriernew', 50, bold=True) 
font_button = pygame.font.SysFont('couriernew', 24, bold=True) 

# --- RGB COLOR PALETTE ---
CYBER_CYAN = (0, 255, 255)    
WHITE = (255, 255, 255)
NIGHT_PURPLE = (20, 0, 40)     
GRAY_BUILDING = (100, 100, 100) 
BLACK = (10, 10, 10)

# --- Title Setup ---
title_surface = font_title.render("NGEE ANN CITY", False, CYBER_CYAN)
title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 80))

# --- Buttons Setup ---
new_game_rect = pygame.Rect(200, 180, 200, 50)
continue_rect = pygame.Rect(200, 250, 200, 50)

new_game_text = font_button.render("NEW GAME", False, BLACK)
continue_text = font_button.render("CONTINUE", False, BLACK)

new_game_text_rect = new_game_text.get_rect(center=new_game_rect.center)
continue_text_rect = continue_text.get_rect(center=continue_rect.center)

# --- 8-BIT LANDSCAPE SETUP (DOUBLED SIZE) ---
buildings = []
building_width = 60  # Doubled from 30 to 60 pixels
gap = 8              # Slightly increased gap to separate large structures
current_x = 0

# Randomly generate the wider skyscrapers across the screen
while current_x < SCREEN_WIDTH:
    # Increased the max random height so they feel appropriately massive
    building_height = random.randint(120, 280)
    building_rect = pygame.Rect(current_x, SCREEN_HEIGHT - building_height, building_width, building_height)
    buildings.append(building_rect)
    current_x += building_width + gap

running = True
while running:
    mouse_pos = pygame.mouse.get_pos()

    # 3. Event Handling Loop
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: 
                if new_game_rect.collidepoint(mouse_pos):
                    print("Starting a New Game...")
                elif continue_rect.collidepoint(mouse_pos):
                    print("Loading Saved Game...")

    # 4. Drawing / Rendering
    # A. Draw the Sky
    screen.fill(NIGHT_PURPLE)  

    # B. Draw the Large 8-bit Gray Skyscrapers
    for building in buildings:
        pygame.draw.rect(screen, GRAY_BUILDING, building) 
        
        # Grid of windows for the larger building widths
        if building.height > 100:  
            # Row 1 of windows
            pygame.draw.rect(screen, CYBER_CYAN, (building.x + 12, building.y + 30, 8, 8)) 
            pygame.draw.rect(screen, CYBER_CYAN, (building.x + 38, building.y + 30, 8, 8)) 
            # Row 2 of windows
            pygame.draw.rect(screen, CYBER_CYAN, (building.x + 12, building.y + 70, 8, 8)) 
            pygame.draw.rect(screen, CYBER_CYAN, (building.x + 38, building.y + 70, 8, 8)) 
            # Row 3 for extra tall structures
            if building.height > 180:
                pygame.draw.rect(screen, CYBER_CYAN, (building.x + 12, building.y + 110, 8, 8)) 
                pygame.draw.rect(screen, CYBER_CYAN, (building.x + 38, building.y + 110, 8, 8)) 

    # C. Draw Menu Interface (Title and Buttons)
    screen.blit(title_surface, title_rect)
    
    # --- Draw New Game Button ---
    if new_game_rect.collidepoint(mouse_pos):
        pygame.draw.rect(screen, CYBER_CYAN, new_game_rect) 
    else:
        pygame.draw.rect(screen, WHITE, new_game_rect) 
    screen.blit(new_game_text, new_game_text_rect)

    # --- Draw Continue Button ---
    if continue_rect.collidepoint(mouse_pos):
        pygame.draw.rect(screen, CYBER_CYAN, continue_rect)
    else:
        pygame.draw.rect(screen, WHITE, continue_rect)
    screen.blit(continue_text, continue_text_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()