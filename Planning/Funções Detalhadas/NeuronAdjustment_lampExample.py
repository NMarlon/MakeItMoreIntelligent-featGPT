import pygame
import sys
import numpy as np
import random
from pygame.math import Vector2

# ====================== PARÂMETROS AJUSTÁVEIS ======================
N_NEURONS = 10
NUM_INPUT_NEURONS = 2

# NOVO: Número de conexões por neurônio (ajustável)
MIN_CONNECTIONS_PER_NEURON = 1
MAX_CONNECTIONS_PER_NEURON = 3

MIN_INTERVAL = 1
MAX_INTERVAL = 150

A_plus = 0.012
A_minus = 0.014
tau_plus = 20.0
tau_minus = 20.0

WIDTH, HEIGHT = 1180, 900
FPS = 60

# Forças (valores que você gostou)
ATTRACTION = 0.0055
REPULSION_ALL = 60000
REPULSION_NON_CONNECTED = 150000

DAMPING = 0.84
MAX_SPEED = 5.5

# Cores
BG_COLOR = (8, 8, 18)
NEURON_PROC = (235, 235, 245)
INPUT_COLOR = (25, 95, 255)
SPIKE_COLOR = (255, 255, 110)
INPUT_FLASH_COLOR = (0, 255, 180)
LINE_DEFAULT = (160, 160, 200)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("STDP Sala das Lâmpadas - Zoom + Conexões Ajustáveis")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 18)
small_font = pygame.font.SysFont("consolas", 13)

# ====================== REDE ======================
random.seed()
G = {}

for i in range(N_NEURONS):
    angle = i * (2 * np.pi / N_NEURONS) + random.uniform(-0.8, 0.8)
    r = 260 + random.uniform(-70, 110)
    G[i] = {
        'pos': Vector2(WIDTH//2 + r * np.cos(angle), HEIGHT//2 + r * np.sin(angle) * 0.75),
        'vel': Vector2(0, 0),
        'is_input': i < NUM_INPUT_NEURONS,
        'next_input_time': -1000
    }

# Conexões com quantidade ajustável
edges = []
for i in range(N_NEURONS):
    possible_targets = [j for j in range(N_NEURONS) if j != i]
    num_connections = random.randint(MIN_CONNECTIONS_PER_NEURON, MAX_CONNECTIONS_PER_NEURON)
    num_connections = min(num_connections, len(possible_targets))
    
    if num_connections > 0:
        targets = random.sample(possible_targets, num_connections)
        for t in targets:
            # Evita duplicatas e conexões de entrada → entrada
            if G[i]['is_input'] and G[t]['is_input']:
                continue
            weight = random.uniform(0.35, 0.92)
            edges.append({'from': i, 'to': t, 'weight': weight, 'last_delta': 0.0, 'flash': 0})

last_spike_time = {i: -1000 for i in range(N_NEURONS)}

def stdp_delta(pre, post):
    dt = post - pre
    if dt > 0:
        return A_plus * np.exp(-dt / tau_plus)
    return -A_minus * np.exp(dt / tau_minus)

# Variáveis de zoom
zoom = 1.0
camera_offset = Vector2(0, 0)

# ====================== LOOP ======================
frame = 0
running = True

while running:
    frame += 1
    t = frame

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEWHEEL:
            # Zoom com roda do mouse
            old_zoom = zoom
            zoom *= 1.08 if event.y > 0 else 0.93
            zoom = max(0.3, min(zoom, 4.0))

            # Zoom centrado no mouse
            mouse_pos = Vector2(pygame.mouse.get_pos())
            world_mouse = (mouse_pos - Vector2(WIDTH/2, HEIGHT/2)) / old_zoom + Vector2(WIDTH/2, HEIGHT/2)
            camera_offset = mouse_pos - (world_mouse - camera_offset) * zoom

    screen.fill(BG_COLOR)

    # Input externo (sempre 1)
    active_pre = []
    for i in range(NUM_INPUT_NEURONS):
        if t >= G[i]['next_input_time']:
            if random.random() < 0.48:
                active_pre.append(i)
                G[i]['next_input_time'] = t + random.randint(MIN_INTERVAL, MAX_INTERVAL)
                break

    for pre in active_pre:
        last_spike_time[pre] = t
        for edge in edges:
            if edge['from'] == pre:
                to = edge['to']
                if random.random() < min(0.96, edge['weight'] * 0.92):
                    last_spike_time[to] = t + random.uniform(1.8, 10)

    # STDP
    for edge in edges:
        u = edge['from']
        v = edge['to']
        pre_t = last_spike_time[u]
        post_t = last_spike_time[v]
        if abs(pre_t - t) < 300 and abs(post_t - t) < 300:
            dw = stdp_delta(pre_t, post_t)
            if abs(dw) > 0.0003:
                edge['weight'] = np.clip(edge['weight'] + dw, 0.05, 1.7)
                edge['last_delta'] = dw
                edge['flash'] = 12

    # Forças (mantidas fortes como você gostou)
    for i in range(N_NEURONS):
        for j in range(i + 1, N_NEURONS):
            delta = G[i]['pos'] - G[j]['pos']
            dist_sq = delta.length_squared()
            if dist_sq < 0.001: continue

            force = REPULSION_ALL / dist_sq
            repel = delta.normalize() * force
            G[i]['vel'] += repel * 0.7
            G[j]['vel'] -= repel * 0.7

            connected = any((e['from'] == i and e['to'] == j) or (e['from'] == j and e['to'] == i) for e in edges)
            if not connected:
                extra = REPULSION_NON_CONNECTED / dist_sq
                extra_repel = delta.normalize() * extra
                G[i]['vel'] += extra_repel
                G[j]['vel'] -= extra_repel

    for edge in edges:
        u = edge['from']
        v = edge['to']
        delta = G[v]['pos'] - G[u]['pos']
        dist = delta.length() + 0.001
        force = ATTRACTION * dist
        dir_force = delta.normalize() * force
        G[u]['vel'] += dir_force * 0.45
        G[v]['vel'] -= dir_force * 0.45

    # Atualiza posições
    for i in range(N_NEURONS):
        G[i]['vel'] *= DAMPING
        if G[i]['vel'].length() > MAX_SPEED:
            G[i]['vel'] = G[i]['vel'].normalize() * MAX_SPEED
        G[i]['pos'] += G[i]['vel']

        G[i]['pos'].x = max(100, min(WIDTH-100, G[i]['pos'].x))
        G[i]['pos'].y = max(100, min(HEIGHT-100, G[i]['pos'].y))

    # ====================== DESENHO COM ZOOM ======================
    for edge in edges:
        p1 = G[edge['from']]['pos']
        p2 = G[edge['to']]['pos']
        weight = edge['weight']
        flash = edge.get('flash', 0)

        if flash > 0:
            color = (80, 255, 150) if edge.get('last_delta', 0) > 0 else (255, 60, 210)
            edge['flash'] -= 1
        else:
            color = LINE_DEFAULT

        # Aplicar zoom e offset
        screen_p1 = (p1 - camera_offset) * zoom + Vector2(WIDTH/2, HEIGHT/2)
        screen_p2 = (p2 - camera_offset) * zoom + Vector2(WIDTH/2, HEIGHT/2)

        line_width = max(5, int(weight * 9))
        pygame.draw.line(screen, color, screen_p1, screen_p2, line_width)

        # Seta
        direction = (screen_p2 - screen_p1).normalize()
        arrow_base = screen_p2 - direction * 36
        perp = Vector2(-direction.y, direction.x)
        tip1 = arrow_base + perp * 15
        tip2 = arrow_base - perp * 15
        pygame.draw.polygon(screen, color, [screen_p2, tip1, tip2])

        mid = (screen_p1 + screen_p2) / 2
        txt = small_font.render(f"{weight:.2f}", True, (255, 255, 255))
        screen.blit(txt, mid + Vector2(-22, -16))

    # Neurônios com zoom
    for i in range(N_NEURONS):
        p = (G[i]['pos'] - camera_offset) * zoom + Vector2(WIDTH/2, HEIGHT/2)
        is_input = G[i]['is_input']
        is_spiking = abs(last_spike_time[i] - t) < 25

        radius = int(34 * zoom)
        color = INPUT_COLOR if is_input else SPIKE_COLOR if is_spiking else NEURON_PROC

        pygame.draw.circle(screen, color, (int(p.x), int(p.y)), radius)
        pygame.draw.circle(screen, (255,255,255), (int(p.x), int(p.y)), radius, int(4 * zoom))

        if i in active_pre:
            pygame.draw.circle(screen, INPUT_FLASH_COLOR, (int(p.x), int(p.y)), radius + int(18 * zoom), int(6 * zoom))

        label = "IN" if is_input else str(i)
        txt = font.render(label, True, (255, 255, 255))
        screen.blit(txt, (p.x - 22 * zoom, p.y - 55 * zoom))

    info = font.render(f"Frame: {frame} | Entrada: {'Sim' if active_pre else 'Não'} | FPS: {clock.get_fps():.1f} | Zoom: {zoom:.2f}", True, (180, 180, 200))
    screen.blit(info, (20, 15))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()