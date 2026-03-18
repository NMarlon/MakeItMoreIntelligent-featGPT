import random
from dataclasses import dataclass, field
from MegaIA import MegaCore, main_megaia
from tutorial import run_tutorial

# Configurações de cenário (ajuste aqui):
GRID_ROWS = 4  # número de linhas do mapa
GRID_COLS = 4  # número de colunas do mapa
NUM_PITS = 3  # número de poços (obstáculos/perigo)

# Direções: 0=North,1=East,2=South,3=West
DIRECTION_LABELS = ['N', 'E', 'S', 'W']
MOVES = {0: (-1, 0), 1: (0, 1), 2: (1, 0), 3: (0, -1)}
BOT_ICON = {0: '^', 1: '>', 2: 'v', 3: '<'}

# Cores ANSI para terminal
ANSI_RESET = '\x1b[0m'
ANSI_RED = '\x1b[91m'
ANSI_GREEN = '\x1b[92m'
ANSI_YELLOW = '\x1b[93m'
ANSI_BLUE = '\x1b[94m'
ANSI_MAGENTA = '\x1b[95m'
ANSI_CYAN = '\x1b[96m'
ANSI_WHITE = '\x1b[97m'

# Configurações do monstro
MONSTER_CAN_MOVE = True  # true/false para controlar se o monstro se move
MONSTER_ASTAR_PROB = 0.3  # probabilidade de usar A* para seguir o bot (0.0 a 1.0)

# Fome (valores ajustáveis)
MAX_HUNGER = 250
HUNGER_LOSS_PER_TURN = 1
APPLE_HUNGER_RECOVERY = 150

# Ataque do bot
BOT_CAN_ATTACK = True  # true/false para permitir o ataque
ATTACK_REWARD = 80
ATTACK_PENALTY = -10

# Respawn de monstro
MONSTER_RESPAWN_TURNS = 2  # espera após morte para respawn
MONSTER_RESPAWN_PER_TURN = 1  # quantos monstros aparecem por turno

# Respawn do bot e vidas
BOT_INITIAL_LIVES = 3  # 0 = infinitas
BOT_RESPAWN_MAP_POLICY = 'random'  # 'same', 'random', 'choice' (IA escolhe)


def clamp_pos(pos, rows, cols):
    """Garante que uma posição (linha, coluna) permaneça dentro dos limites do grid."""
    r, c = pos
    r = max(0, min(rows - 1, r))
    c = max(0, min(cols - 1, c))
    return (r, c)


@dataclass
class Bot:
    """Representa o agente (ou 'bot') no ambiente da dungeon."""
    position: tuple[int, int]
    direction: int = 0  # 0:N, 1:E, 2:S, 3:W
    alive: bool = True
    score: int = 0
    inventory: dict[str, bool] = field(default_factory=lambda: {'apple': False})

    def turn_left(self):
        """Gira o bot 90 graus para a esquerda."""
        self.direction = (self.direction - 1) % 4
        return 'virar_esquerda'

    def turn_right(self):
        """Gira o bot 90 graus para a direita."""
        self.direction = (self.direction + 1) % 4
        return 'virar_direita'

    def move_forward(self, rows, cols):
        """Move o bot uma casa para frente na direção atual."""
        dr, dc = MOVES[self.direction]
        new_pos = (self.position[0] + dr, self.position[1] + dc)
        # Garante que o bot não saia dos limites do mapa
        new_pos = clamp_pos(new_pos, rows, cols)
        self.position = new_pos
        return 'avancar'

    def attack_forward(self):
        """Retorna a coordenada da casa à frente do bot, alvo do ataque."""
        dr, dc = MOVES[self.direction]
        return (self.position[0] + dr, self.position[1] + dc)


class Dungeon:
    """
    Gerencia o estado do ambiente (o 'mapa'), incluindo a posição de todos os
    elementos e a física do jogo.
    """
    def __init__(self, rows=GRID_ROWS, cols=GRID_COLS, num_pits=NUM_PITS,
                 monster_can_move=MONSTER_CAN_MOVE, monster_astar_prob=MONSTER_ASTAR_PROB):
        """
        Inicializa a dungeon.
        
        Args:
            rows (int): Número de linhas no grid.
            cols (int): Número de colunas no grid.
            num_pits (int): Número de poços de perigo.
            monster_can_move (bool): Se o monstro pode se mover.
            monster_astar_prob (float): Probabilidade do monstro usar A* para perseguir.
        """
        self.rows = rows
        self.cols = cols
        self.num_pits = num_pits
        self.monster_can_move = monster_can_move
        self.monster_astar_prob = monster_astar_prob
        self.state = self.create_random()

    def _neighbors(self, pos):
        r, c = pos
        for dr, dc in MOVES.values():
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if (nr, nc) not in self.state['pits']:
                    yield (nr, nc)

    def _reconstruct_path(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def find_path_a_star(self, start, goal):
        import heapq

        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: abs(start[0] - goal[0]) + abs(start[1] - goal[1])}

        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal:
                return self._reconstruct_path(came_from, current)

            for neighbor in self._neighbors(current):
                tentative_g = g_score[current] + 1
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h = abs(neighbor[0] - goal[0]) + abs(neighbor[1] - goal[1])
                    f_score[neighbor] = tentative_g + h
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return None

    def move_monster(self):
        if not self.monster_can_move or self.state['done']:
            return
        if not self.state['monsters']:
            return

        bot_pos = self.state['bot'].position
        new_positions = set()

        for monster_pos in self.state['monsters']:
            use_astar = random.random() < self.monster_astar_prob
            next_pos = monster_pos
            if use_astar:
                path = self.find_path_a_star(monster_pos, bot_pos)
                if path and len(path) > 1:
                    next_pos = path[1]
            else:
                choices = list(self._neighbors(monster_pos))
                if choices:
                    next_pos = random.choice(choices)
            new_positions.add(next_pos)

        self.state['monsters'] = new_positions

    def spawn_monsters(self, count=1):
        occupied = {self.state['bot'].position, self.state['apple']} | self.state['pits'] | self.state['monsters']
        empty = [(r, c) for r in range(self.rows) for c in range(self.cols) if (r, c) not in occupied]
        random.shuffle(empty)
        for _ in range(min(count, len(empty))):
            self.state['monsters'].add(empty.pop())

    def create_random(self):
        """
        Cria um estado de jogo inicial aleatório, posicionando o bot, monstro,
        maçã e poços em locais aleatórios e não sobrepostos.
        
        Returns:
            dict: O dicionário de estado inicial do jogo.
        """
        all_cells = [(r, c) for r in range(self.rows) for c in range(self.cols)]
        random.shuffle(all_cells)
        
        # Garante que haja células suficientes para todos os objetos
        if len(all_cells) < 3 + self.num_pits:
            raise ValueError("Grid muito pequeno para o número de objetos e poços.")

        bot_pos = all_cells.pop()
        monster_pos = all_cells.pop()
        apple_pos = all_cells.pop()
        pits = {all_cells.pop() for _ in range(min(self.num_pits, len(all_cells)))}
        
        bot = Bot(position=bot_pos)
        
        return {
            'bot': bot,
            'monsters': {monster_pos},
            'apple': apple_pos,
            'pits': pits,
            'done': False,
            'reason': None,
            'apples_collected': 0,
            'hunger': MAX_HUNGER,
            'monster_respawn_timer': 0,
            'deaths': 0,
            'remaining_lives': BOT_INITIAL_LIVES,
        }

    def choose_respawn_map(self):
        if BOT_RESPAWN_MAP_POLICY == 'random':
            return 'random'
        if BOT_RESPAWN_MAP_POLICY == 'choice':
            return random.choice(['same', 'random'])
        return 'same'

    def random_empty_position(self):
        occupied = {self.state['bot'].position} | self.state['monsters'] | self.state['pits']
        if self.state['apple'] is not None:
            occupied.add(self.state['apple'])
        empties = [(r, c) for r in range(self.rows) for c in range(self.cols) if (r, c) not in occupied]
        if not empties:
            return self.state['bot'].position
        return random.choice(empties)

    def respawn_bot(self):
        policy = self.choose_respawn_map()
        if policy == 'random':
            old_deaths = self.state.get('deaths', 0)
            old_lives = self.state.get('remaining_lives', BOT_INITIAL_LIVES)
            self.state = self.create_random()
            self.state['deaths'] = old_deaths
            self.state['remaining_lives'] = old_lives
            return
        bot = self.state['bot']
        bot.position = self.random_empty_position()
        bot.direction = 0
        bot.alive = True
        bot.inventory = {'apple': False}
        self.state['hunger'] = MAX_HUNGER

    def spawn_apple(self):
        occupied = {self.state['bot'].position} | self.state['monsters'] | self.state['pits']
        empty = [(r, c) for r in range(self.rows) for c in range(self.cols) if (r, c) not in occupied]
        if not empty:
            return
        self.state['apple'] = random.choice(empty)

    def bot_vision(self):
        bot = self.state['bot']
        r, c = bot.position
        if bot.direction == 0:
            fov = [(r-1, c), (r-1, c-1), (r-1, c+1), (r-2, c), (r-2, c-1), (r-2, c+1)]
        elif bot.direction == 1:
            fov = [(r, c+1), (r-1, c+1), (r+1, c+1), (r, c+2), (r-1, c+2), (r+1, c+2)]
        elif bot.direction == 2:
            fov = [(r+1, c), (r+1, c-1), (r+1, c+1), (r+2, c), (r+2, c-1), (r+2, c+1)]
        else:
            fov = [(r, c-1), (r-1, c-1), (r+1, c-1), (r, c-2), (r-1, c-2), (r+1, c-2)]
        visible = set()
        for nr, nc in fov:
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                visible.add((nr, nc))
        return visible

    def render(self):
        d = self.state
        visible = self.bot_vision()
        lines = [f'Dungeon ({ANSI_CYAN}B=bot{ANSI_RESET}, {ANSI_RED}M=monstro{ANSI_RESET}, {ANSI_GREEN}A=maçã{ANSI_RESET}, {ANSI_RED}X=poço{ANSI_RESET}, .=vazio)']
        lines.append('+' + '---+' * self.cols)
        for r in range(self.rows):
            row_chars = []
            for c in range(self.cols):
                pos = (r, c)
                
                # Determine base cell content
                if pos == d['bot'].position:
                    cell_content = f' {BOT_ICON[d["bot"].direction]} '
                    color = ANSI_CYAN
                elif pos in d['monsters']:
                    cell_content = ' M '
                    color = ANSI_RED
                elif pos == d['apple']:
                    cell_content = ' A '
                    color = ANSI_GREEN
                elif pos in d['pits']:
                    cell_content = ' X '
                    color = ANSI_RED
                else:
                    cell_content = ' . '
                    color = ANSI_WHITE # Default color for empty space

                # Apply yellow highlight for visibility
                is_visible = pos in visible and pos != d['bot'].position
                if is_visible and color == ANSI_WHITE: # Only highlight empty visible cells
                    color = ANSI_YELLOW

                cell = f'{color}{cell_content}{ANSI_RESET}'
                row_chars.append(cell)
            lines.append('|' + '|'.join(row_chars) + '|')
            lines.append('+' + '---+' * self.cols)
        return '\n'.join(lines)

    def perception(self):
        bot = self.state['bot']
        r, c = bot.position
        visible_positions = self.bot_vision()
        visible_items = {}
        for pos in visible_positions:
            if pos == bot.position:
                symbol = BOT_ICON[bot.direction]
            elif pos in self.state['monsters']:
                symbol = 'M'
            elif pos == self.state['apple']:
                symbol = 'A'
            elif pos in self.state['pits']:
                symbol = 'X'
            else:
                symbol = '.'
            visible_items[pos] = { 'symbol': symbol, 'relative': (pos[0]-r, pos[1]-c) }
        senses = {
            'near_monster': False,
            'near_pit': False,
            'near_apple': False,
            'visible_positions': visible_positions,
            'visible_items': visible_items,
        }
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            p = (r+dr, c+dc)
            if p in self.state['monsters']:
                senses['near_monster'] = True
            if p in self.state['pits']:
                senses['near_pit'] = True
            if p == self.state['apple']:
                senses['near_apple'] = True
        senses['on_apple'] = bot.position == self.state['apple']
        senses['on_monster'] = bot.position in self.state['monsters']
        senses['on_pit'] = bot.position in self.state['pits']
        senses['direction'] = DIRECTION_LABELS[bot.direction]
        senses['position'] = bot.position
        senses['alive'] = bot.alive
        return senses

    def step(self, action: str):
        if self.state['done']:
            return {'status': 'finished', 'reward': 0, 'info': 'Jogo encerrado'}
        bot = self.state['bot']
        reward = -1
        self.state['hunger'] -= HUNGER_LOSS_PER_TURN
        if self.state['hunger'] <= 0:
            bot.alive = False
            self.state['done'] = True
            self.state['reason'] = 'morreu_fome'
            reward = -100
            bot.score += reward
            return { 'status': 'ok', 'reward': reward, 'done': self.state['done'], 'reason': self.state['reason'], 'perception': self.perception() }
        if action == 'avancar':
            bot.move_forward(self.rows, self.cols)
        elif action == 'virar_esquerda':
            bot.turn_left(); reward = 0
        elif action == 'virar_direita':
            bot.turn_right(); reward = 0
        elif action == 'pegar':
            if self.state['apple'] is not None and bot.position == self.state['apple']:
                bot.inventory['apple'] = True
                self.state['apple'] = None
                self.state['apples_collected'] += 1
                self.state['hunger'] = min(MAX_HUNGER, self.state['hunger'] + APPLE_HUNGER_RECOVERY)
                reward = 50
                self.spawn_apple()
            else:
                reward = -5
        elif action == 'atacar':
            if not BOT_CAN_ATTACK:
                reward = -5
            else:
                target = bot.attack_forward()
                if target in self.state['monsters']:
                    self.state['monsters'].remove(target)
                    self.state['monster_respawn_timer'] = 0
                    reward = ATTACK_REWARD
                else:
                    reward = ATTACK_PENALTY
        else:
            reward = -5
        if self.monster_can_move and not self.state['done']:
            self.move_monster()
        if bot.position in self.state['monsters']:
            bot.alive = False; self.state['done'] = True; self.state['reason'] = 'monstro'; reward = -100
        elif bot.position in self.state['pits']:
            bot.alive = False; self.state['done'] = True; self.state['reason'] = 'poço'; reward = -100
        if not self.state['done'] and not self.state['monsters']:
            self.state['monster_respawn_timer'] += 1
            if self.state['monster_respawn_timer'] >= MONSTER_RESPAWN_TURNS:
                self.spawn_monsters(MONSTER_RESPAWN_PER_TURN); self.state['monster_respawn_timer'] = 0
        bot.score += reward
        return { 'status': 'ok', 'reward': reward, 'done': self.state['done'], 'reason': self.state.get('reason'), 'perception': self.perception() }


def print_status(dungeon):
    """Imprime o estado atual do jogo de forma colorida e formatada."""
    print(dungeon.render())
    p = dungeon.perception()

    # --- Cores para o status ---
    LBL_COLOR = ANSI_WHITE  # Cor para as etiquetas (e.g., "Posição:")
    VAL_COLOR = ANSI_CYAN   # Cor padrão para valores
    GOOD_COLOR = ANSI_GREEN
    BAD_COLOR = ANSI_RED
    NEUTRAL_COLOR = ANSI_YELLOW

    def color_bool(val, is_good=True):
        """Colore um booleano (Verde para True/bom, Vermelho para True/ruim)."""
        if val:
            return f"{GOOD_COLOR if is_good else BAD_COLOR}{val}{ANSI_RESET}"
        return f"{ANSI_WHITE}{val}{ANSI_RESET}"

    # --- Linha 1: Posição, Direção, Fome, Status ---
    pos_str = f"{LBL_COLOR}Posição:{ANSI_RESET} {VAL_COLOR}{p['position']}{ANSI_RESET}"
    dir_str = f"{LBL_COLOR}Direção:{ANSI_RESET} {VAL_COLOR}{p['direction']}{ANSI_RESET}"
    
    hunger = dungeon.state['hunger']
    hunger_color = GOOD_COLOR if hunger > MAX_HUNGER * 0.4 else (NEUTRAL_COLOR if hunger > MAX_HUNGER * 0.15 else BAD_COLOR)
    hunger_str = f"{LBL_COLOR}Fome:{ANSI_RESET} {hunger_color}{hunger}/{MAX_HUNGER}{ANSI_RESET}"
    
    alive_str = f"{LBL_COLOR}Alive:{ANSI_RESET} {color_bool(p['alive'])}"
    print(f"{pos_str} | {dir_str} | {hunger_str} | {alive_str}")

    # --- Linha 2: Sensações Próximas ---
    near_m = color_bool(p['near_monster'], is_good=False)
    near_p = color_bool(p['near_pit'], is_good=False)
    near_a = color_bool(p['near_apple'])
    print(f"{LBL_COLOR}Sensações:{ANSI_RESET} monstro próximo={near_m} poço próximo={near_p} maçã próxima={near_a}")

    # --- Linha 3: Visibilidade Detalhada ---
    def color_symbol(s):
        if s == 'M' or s == 'X': return f"{BAD_COLOR}{s}{ANSI_RESET}"
        if s == 'A': return f"{GOOD_COLOR}{s}{ANSI_RESET}"
        if s in ('^', '>', 'v', '<'): return f"{VAL_COLOR}{s}{ANSI_RESET}"
        return s
        
    visible_details = [f"({pos}, {color_symbol(v['symbol'])}, {v['relative']})" for pos, v in sorted(p['visible_items'].items())]
    print(f"{LBL_COLOR}Visíveis detalhado:{ANSI_RESET} [{', '.join(visible_details)}]")

    # --- Linha 4: No Chão ---
    on_a = color_bool(p['on_apple'])
    on_m = color_bool(p['on_monster'], is_good=False)
    on_p = color_bool(p['on_pit'], is_good=False)
    print(f"{LBL_COLOR}No chão:{ANSI_RESET} maçã={on_a} monstro={on_m} poço={on_p}")

    # --- Linha 5: Inventário e Score ---
    inventory_val = color_bool(dungeon.state['bot'].inventory.get('apple', False))
    inventory_str = f"{LBL_COLOR}Inventário:{ANSI_RESET} {{'apple': {inventory_val}}}"
    
    score = dungeon.state['bot'].score
    score_color = GOOD_COLOR if score >= 0 else BAD_COLOR
    score_str = f"{LBL_COLOR}Score:{ANSI_RESET} {score_color}{score}{ANSI_RESET}"

    apples_collected = dungeon.state['apples_collected']
    apples_color = GOOD_COLOR if apples_collected > 0 else ANSI_WHITE
    apples_str = f"{LBL_COLOR}Maçãs colhidas:{ANSI_RESET} {apples_color}{apples_collected}{ANSI_RESET}"
    
    print(f"{inventory_str} | {score_str} | {apples_str}")


def main():
    dungeon = Dungeon(rows=GRID_ROWS, cols=GRID_COLS, num_pits=NUM_PITS)
    print('=== Dungeon com Bot (classes) ===')
    print_status(dungeon)
    while not dungeon.state['done']:
        cmd = input('Ação (avancar/virar_esquerda/virar_direita/pegar/atacar/quit): ').strip().lower()
        if cmd == 'quit':
            break
        if cmd not in ('avancar', 'virar_esquerda', 'virar_direita', 'pegar', 'atacar'):
            print('Ação inválida.')
            continue
        result = dungeon.step(cmd)
        print('Reward:', result['reward'], 'Done:', result.get('done'), 'Reason:', result.get('reason'))
        print_status(dungeon)
    print('Fim do jogo. Razão:', dungeon.state.get('reason'), 'Score final:', dungeon.state['bot'].score)


if __name__ == '__main__':
    # Cria o cérebro da MegaIA
    core = MegaCore()
    
    # Executa o pré-tutorial para ensinar o básico
    run_tutorial(core)
    
    # Inicia a simulação principal com o cérebro pré-treinado
    main_megaia(Dungeon, print_status, core_instance=core, interactive=False)
