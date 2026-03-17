import random
from dataclasses import dataclass, field

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

        monster_pos = self.state['monster']
        bot_pos = self.state['bot'].position

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

        self.state['monster'] = next_pos

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
            'monster': monster_pos,
            'apple': apple_pos,
            'pits': set(pits),
            'done': False,
            'reason': None,
            'apples_collected': 0,
            'hunger': MAX_HUNGER,
        }

    def spawn_apple(self):
        occupied = {self.state['bot'].position, self.state['monster']} | self.state['pits']
        empty = [(r, c) for r in range(self.rows) for c in range(self.cols) if (r, c) not in occupied]
        if not empty:
            return
        self.state['apple'] = random.choice(empty)

    def bot_vision(self):
        bot = self.state['bot']
        r, c = bot.position
        fov = []
        if bot.direction == 0:  # norte
            fov = [(r-1, c), (r-1, c-1), (r-1, c+1), (r-2, c), (r-2, c-1), (r-2, c+1)]
        elif bot.direction == 1:  # leste
            fov = [(r, c+1), (r-1, c+1), (r+1, c+1), (r, c+2), (r-1, c+2), (r+1, c+2)]
        elif bot.direction == 2:  # sul
            fov = [(r+1, c), (r+1, c-1), (r+1, c+1), (r+2, c), (r+2, c-1), (r+2, c+1)]
        else:  # oeste
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
                elif pos == d['monster']:
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

        d = self.state
        lines = ['Dungeon (B=bot, M=monstro, A=maçã, X=poço, .=vazio)']
        lines.append('+' + '---+' * self.cols)
        for r in range(self.rows):
            row_chars = []
            for c in range(self.cols):
                pos = (r, c)
                if pos == d['bot'].position:
                    row_chars.append(' B ')
                elif pos == d['monster']:
                    row_chars.append(' M ')
                elif pos == d['apple']:
                    row_chars.append(' A ')
                elif pos in d['pits']:
                    row_chars.append(' X ')
                else:
                    row_chars.append(' . ')
            lines.append('|' + '|'.join(row_chars) + '|')
            lines.append('+' + '---+' * self.cols)
        return '\n'.join(lines)

    def perception(self):
        bot = self.state['bot']
        r, c = bot.position
        senses = {'near_monster': False, 'near_pit': False, 'near_apple': False}
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            p = (r + dr, c + dc)
            if p == self.state['monster']:
                senses['near_monster'] = True
            if p in self.state['pits']:
                senses['near_pit'] = True
            if p == self.state['apple']:
                senses['near_apple'] = True
        senses['on_apple'] = bot.position == self.state['apple']
        senses['on_monster'] = bot.position == self.state['monster']
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

        # perda de fome a cada turno
        self.state['hunger'] -= HUNGER_LOSS_PER_TURN
        if self.state['hunger'] <= 0:
            bot.alive = False
            self.state['done'] = True
            self.state['reason'] = 'morreu_fome'
            reward = -100
            bot.score += reward
            return {
                'status': 'ok',
                'reward': reward,
                'done': self.state['done'],
                'reason': self.state['reason'],
                'perception': self.perception(),
            }

        if action == 'avancar':
            bot.move_forward(self.rows, self.cols)
        elif action == 'virar_esquerda':
            bot.turn_left()
            reward = 0
        elif action == 'virar_direita':
            bot.turn_right()
            reward = 0
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
        else:
            reward = -5

        # Movimento do monstro (após ação do bot)
        if self.monster_can_move and not self.state['done']:
            self.move_monster()

        # Verificação de eventos após ações do bot e do monstro
        if bot.position == self.state['monster']:
            bot.alive = False
            self.state['done'] = True
            self.state['reason'] = 'monstro'
            reward = -100
        elif bot.position in self.state['pits']:
            bot.alive = False
            self.state['done'] = True
            self.state['reason'] = 'poço'
            reward = -100

        bot.score += reward
        return {
            'status': 'ok',
            'reward': reward,
            'done': self.state['done'],
            'reason': self.state.get('reason'),
            'perception': self.perception(),
        }


def print_status(dungeon):
    print(dungeon.render())
    p = dungeon.perception()
    print(f"Posição: {p['position']} | Direção: {p['direction']} | Fome: {dungeon.state['hunger']}/{MAX_HUNGER} | Alive: {p['alive']}")
    print(f"Sensações: monstro próximo={p['near_monster']} poço próximo={p['near_pit']} maçã próxima={p['near_apple']}")
    print(f"No chão: maçã={p['on_apple']} monstro={p['on_monster']} poço={p['on_pit']}")
    print(f"Inventário: {dungeon.state['bot'].inventory} | Score: {dungeon.state['bot'].score} | Maçãs colhidas: {dungeon.state['apples_collected']}")


def main():
    dungeon = Dungeon(rows=GRID_ROWS, cols=GRID_COLS, num_pits=NUM_PITS)
    print('=== Dungeon com Bot (classes) ===')
    print_status(dungeon)

    while not dungeon.state['done']:
        cmd = input('Ação (avancar/virar_esquerda/virar_direita/pegar/quit): ').strip().lower()
        if cmd == 'quit':
            break
        if cmd not in ('avancar', 'virar_esquerda', 'virar_direita', 'pegar'):
            print('Ação inválida.')
            continue
        result = dungeon.step(cmd)
        print('Reward:', result['reward'], 'Done:', result.get('done'), 'Reason:', result.get('reason'))
        print_status(dungeon)

    print('Fim do jogo. Razão:', dungeon.state.get('reason'), 'Score final:', dungeon.state['bot'].score)


if __name__ == '__main__':
    main()

