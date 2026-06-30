import random

# === GAME VARIABLES ====
coins = 16
turn = 1

# ARCADE MODE
ROWS = 20
COLS = 20

city = [[' ' for c in range(COLS)] for r in range(ROWS)]

# FREE PLAY MODE
free_rows = 5
free_cols = 5

free_city = [[' ' for c in range(free_cols)] for r in range(free_rows)]

free_turn = 1

# BUILDINGS

buildings = ['R', 'I', 'C', 'O', '*']

score = 0
profit = 0
# === GAME VARIABLES ====


# ====== MAIN MENU ======
def main_menu():

    while True:

        print("""
===================================
      NGEE ANN CITY BUILDER
===================================

1. Start New Arcade Game
2. Start New Free Play Game
3. Load Saved Game
              

4. Display High Scores
5. Exit Game

===================================
""")

        choice = input("Your choice? ")

        if choice == '1':
            arcade_mode()

        elif choice == '2':
            freeplay_mode()

        elif choice == '3':
            saved_game()

        elif choice == '4':
            display_scores()

        elif choice == '5':
            print("Thanks for playing!")
            break

        else:
            print("Invalid choice.")
# ====== MAIN MENU ======



# ==== MAP CREATION =====
def draw_city(city):

    print()

    # Column numbers
    print("    ", end='')

    for c in range(len(city[0])):
        print(f"{c+1:2}", end=' ')

    print()

    print("   +" + "---+" * len(city[0]))

    for r in range(len(city)):

        print(f"{r+1:2} |", end='')

        for c in range(len(city[0])):

            print(f" {city[r][c]} |", end='')

        print()

        print("   +" + "---+" * len(city[0]))
# ==== MAP CREATION =====



# ===== ARCADE MODE =====
def arcade_mode():

    global coins
    global turn

    while True:

        show_arcade_stats()

        draw_city(city)

        building1 = random.choice(buildings)
        building2 = random.choice(buildings)

        while building2 == building1:
            building2 = random.choice(buildings)

        print()
        print("Choose a building to construct")
        print("-------------------------------")
        print(f"1) {building1}")
        print(f"2) {building2}")
        print()
        print("0) Return to Main Menu")
        print("-------------------------------")

        choice = input("Your choice? ")

        if choice == '0':
            break

        elif choice == '1':
            place_building(building1, city)

            if board_full(city):
                final_score = calculate_score()

                print("\n====================")
                print("GAME OVER")
                print("====================")
                print(f"Final Score : {final_score}")

                input("\nPress Enter...")
                break

        elif choice == '2':
            place_building(building2, city)

            if board_full(city):
                final_score = calculate_score()

            print("\n====================")
            print("GAME OVER")
            print("====================")
            print(f"Final Score : {final_score}")

            input("\nPress Enter...")
            break
        
        else:
            print("Invalid choice.")
# ===== ARCADE MODE =====



# == ARCADE STATISTICS ==
def show_arcade_stats():

    print('''
========================================
Arcade Mode
========================================
Coins : {}
Turn  : {}
========================================
'''.format(coins, turn))
# == ARCADE STATISTICS ==



# === FREE PLAY MODE ====
def freeplay_mode():

    global free_turn
    print("Free Play Mode is under development.")
    while True:

        print('''===================
            Free Play Mode
        ===================''')
        print(f"Turn : {free_turn}")

        draw_city(free_city)

        print("0) Return to Main Menu")

        choice = input("Your choice? ")

        if choice == '0':
            break
# === FREE PLAY MODE ====



# ====== SAVE GAME ======
def saved_game():
    print("Load Saved Game is under development.")
# ====== SAVE GAME ======



# ====== END GAME =======
def board_full(city):

    for row in city:
        if ' ' in row:
            return False

    return True
# ====== END GAME =======



# ==== DISPLAY SCORES ===
def display_scores():
    print("High Scores are under development.")
# ==== DISPLAY SCORES ===



# == CALCULATE SCORES ===
def calculate_score():
    return 0
# == CALCULATE SCORES ===



# ====== PLACEMENT ======
def place_building(building, city):

    global coins
    global turn

    try:
        row = int(input("Row: ")) - 1
        col = int(input("Column: ")) - 1

    except ValueError:
        print("Invalid input.")
        return

    if row < 0 or row >= len(city) or col < 0 or col >= len(city[0]):
        print("Invalid location.")
        return

    if city[row][col] != ' ':
        print("Cell already occupied.")
        return

    city[row][col] = building

    coins -= 1
    turn += 1
# ====== PLACEMENT ======


# ===== MAIN PROGRAM =====
print('''
Welcome to Ngee Ann City, goal of this game is to build the happiest and most
prosperous city possible by scoring the most points.

There are 2 game modes, one Arcade mode with limited number of coins and grid, while the other is
Free Play mode with unlimited number of coins and grid.
''', end="")
main_menu()
# ===== MAIN PROGRAM =====