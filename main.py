import random
from dataclasses import dataclass, field
from MegaIA import main_megaia

# Configurações de cenário (ajuste aqui):
GRID_ROWS = 4  # número de linhas do mapa
GRID_COLS = 4  # número de colunas do mapa
NUM_PITS = 3  # número de poços (obstáculos/perigo)

# Direções: 0=North,1=East,2=South,3=West
DIRECTION_LABELS = ['N', 'E', 'S', 'W']
MOVES = {0: (-1, 0), 1: (0, 1), 2: (1, 0), 3: (0, -1)}
BOT_ICON = {0: '^', 1: '>', 2: 'v', 3: '<'}

# Cores ANSI para terminal
ANSI_YELLOW = '\x1b[93m'
ANSI_RESET = '\x1b[0m'

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
    r, c = pos
    r = max(0, min(rows - 1, r))
    c = max(0, min(cols - 1, c))
    return (r, c)


@dataclass
class Bot:
    position: tuple[int, int]
    direction: int = 0
    alive: bool = True
    score: int = 0
    inventory: dict[str, bool] = field(default_factory=lambda: {'apple': False})

    def turn_left(self):
        self.direction = (self.direction - 1) % 4
        return 'virar_esquerda'

    def turn_right(self):
        self.direction = (self.direction + 1) % 4
        return 'virar_direita'

    def move_forward(self, rows, cols):
        dr, dc = MOVES[self.direction]
        new_pos = (self.position[0] + dr, self.position[1] + dc)
        new_pos = clamp_pos(new_pos, rows, cols)
        self.position = new_pos
        return 'avancar'

    def attack_forward(self):
        dr, dc = MOVES[self.direction]
        return (self.position[0] + dr, self.position[1] + dc)


class Dungeon:
    def __init__(self, rows=GRID_ROWS, cols=GRID_COLS, num_pits=NUM_PITS,
                 monster_can_move=MONSTER_CAN_MOVE, monster_astar_prob=MONSTER_ASTAR_PROB):
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
        all_cells = [(r, c) for r in range(self.rows) for c in range(self.cols)]
        random.shuffle(all_cells)
        bot_pos = all_cells.pop()
        monster_pos = all_cells.pop()
        apple_pos = all_cells.pop()
        pits = [all_cells.pop() for _ in range(min(self.num_pits, len(all_cells)))]
        bot = Bot(position=bot_pos)
        return {
            'bot': bot,
            'monsters': {monster_pos},
            'apple': apple_pos,
            'pits': set(pits),
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
        lines = ['Dungeon (B=bot, M=monstro, A=maçã, X=poço, .=vazio)']
        lines.append('+' + '---+' * self.cols)
        for r in range(self.rows):
            row_chars = []
            for c in range(self.cols):
                pos = (r, c)
                if pos == d['bot'].position:
                    cell = f' {BOT_ICON[d["bot"].direction]} '
                elif pos in d['monsters']:
                    cell = ' M '
                elif pos == d['apple']:
                    cell = ' A '
                elif pos in d['pits']:
                    cell = ' X '
                else:
                    cell = ' . '
                if pos in visible and pos != d['bot'].position:
                    cell = f'{ANSI_YELLOW}{cell}{ANSI_RESET}'
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
    print(dungeon.render())
    p = dungeon.perception()
    print(f"Posição: {p['position']} | Direção: {p['direction']} | Fome: {dungeon.state['hunger']}/{MAX_HUNGER} | Alive: {p['alive']}")
    print(f"Sensações: monstro próximo={p['near_monster']} poço próximo={p['near_pit']} maçã próxima={p['near_apple']}")
    print(f"Visíveis: {sorted(p['visible_positions'])}")
    print(f"Visíveis detalhado: {[ (pos, v['symbol'], v['relative']) for pos,v in sorted(p['visible_items'].items()) ]}")
    print(f"No chão: maçã={p['on_apple']} monstro={p['on_monster']} poço={p['on_pit']}")
    print(f"Inventário: {dungeon.state['bot'].inventory} | Score: {dungeon.state['bot'].score} | Maçãs colhidas: {dungeon.state['apples_collected']}")


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
    main_megaia(Dungeon, print_status)
