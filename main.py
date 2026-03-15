import random

# Configurações de cenário (ajuste aqui):
GRID_ROWS = 8  # número de linhas do mapa
GRID_COLS = 8  # número de colunas do mapa
NUM_PITS = 3  # número de poços (obstáculos/perigo)


def create_dungeon(rows=GRID_ROWS, cols=GRID_COLS, num_pits=NUM_PITS):
    all_cells = [(r, c) for r in range(rows) for c in range(cols)]
    random.shuffle(all_cells)
    bot = all_cells.pop()
    monster = all_cells.pop()
    apple = all_cells.pop()
    pits = [all_cells.pop() for _ in range(num_pits)]
    return {"rows": rows, "cols": cols, "bot": bot, "monster": monster, "apple": apple, "pits": pits}

def render_dungeon(d):
    rows, cols = d["rows"], d["cols"]
    text = []
    text.append("Dungeon cenário (B=bot, M=monstro, A=maçã, X=poço, .=vazio)")
    text.append("+" + "---+" * cols)
    for r in range(rows):
        row_chars = []
        for c in range(cols):
            pos = (r, c)
            if pos == d["bot"]:
                row_chars.append(" B ")
            elif pos == d["monster"]:
                row_chars.append(" M ")
            elif pos == d["apple"]:
                row_chars.append(" A ")
            elif pos in d["pits"]:
                row_chars.append(" X ")
            else:
                row_chars.append(" . ")
        text.append("|" + "|".join(row_chars) + "|")
        text.append("+" + "---+" * cols)
    return "\n".join(text)

def show_scenario(rows=GRID_ROWS, cols=GRID_COLS, num_pits=NUM_PITS):
    dungeon = create_dungeon(rows=rows, cols=cols, num_pits=num_pits)
    print(render_dungeon(dungeon))
    print("\nPosições:")
    print(f"  Bot: {dungeon['bot']}")
    print(f"  Monstro: {dungeon['monster']}")
    print(f"  Maçã: {dungeon['apple']}")
    print(f"  Poços: {dungeon['pits']}")

def main():
    print("=== Dungeon inicial aleatória ===")
    show_scenario()
    while True:
        cmd = input("Gerar novo cenário? (s/n): ").strip().lower()
        if cmd in ("s", "y", "sim", "yes"):
            show_scenario()
        else:
            print("Fim.")
            break

if __name__ == "__main__":
    main()

