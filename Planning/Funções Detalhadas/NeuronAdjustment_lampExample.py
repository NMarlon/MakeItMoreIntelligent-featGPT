import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle, Circle as MplCircle
import matplotlib.animation as animation
from matplotlib.widgets import Slider, Button
import networkx as nx
import random

# ====================== PARÂMETROS AJUSTÁVEIS ======================
N_NEURONS = 5
NUM_INPUT_NEURONS = 2          # Quantos neurônios serão "de entrada" (o resto é processamento/saída)

MIN_INTERVAL = 25
MAX_INTERVAL = 80

INPUT_MODE = "random_individual"   # "random_individual" ou "synchronous"

MIN_ACTIVE = 1
MAX_ACTIVE = 1                     # Forçado para sempre 1

A_plus = 0.008
A_minus = 0.0085
tau_plus = 20.0
tau_minus = 20.0

# ====================== CRIAÇÃO DA REDE (nova versão) ======================
random.seed()                      # Remove seed fixa → rede diferente toda vez
np.random.seed(None)               # Também remove seed do numpy

G = nx.DiGraph()

# Define quais neurônios são de entrada (os primeiros NUM_INPUT_NEURONS)
input_nodes = list(range(NUM_INPUT_NEURONS))
processing_nodes = list(range(NUM_INPUT_NEURONS, N_NEURONS))

for i in range(N_NEURONS):
    G.add_node(i, out_degree=0, in_degree=0, next_input_time=-1000, is_input=(i in input_nodes))

# Conexões: Entradas só saem para processamento (não se conectam entre si)
for i in input_nodes:
    # Cada neurônio de entrada se conecta a quase todos os de processamento
    for t in processing_nodes:
        if random.random() < 0.85:   # nem sempre conecta todos, para variar
            weight = np.random.uniform(0.35, 0.85)
            G.add_edge(i, t, weight=weight, last_delta=0.0, flash_frames=0)
            G.nodes[i]['out_degree'] += 1
            G.nodes[t]['in_degree'] += 1

# Conexões entre neurônios de processamento (mais livre)
for i in processing_nodes:
    possible = [j for j in processing_nodes if j != i]
    num_out = min(len(possible), random.randint(1, 3))
    if num_out > 0:
        targets = random.sample(possible, num_out)
        for t in targets:
            weight = np.random.uniform(0.3, 0.8)
            G.add_edge(i, t, weight=weight, last_delta=0.0, flash_frames=0)
            G.nodes[i]['out_degree'] += 1
            G.nodes[t]['in_degree'] += 1

# Garantia: todo neurônio de processamento tem pelo menos 1 entrada
for node in processing_nodes:
    if G.nodes[node]['in_degree'] == 0:
        source = random.choice(input_nodes)
        weight = np.random.uniform(0.4, 0.8)
        G.add_edge(source, node, weight=weight, last_delta=0.0, flash_frames=0)
        G.nodes[source]['out_degree'] += 1
        G.nodes[node]['in_degree'] += 1

# Layout
pos = nx.spring_layout(G, k=0.9, iterations=100, seed=None)   # seed=None para variar

# ====================== FIGURA ======================
fig, ax = plt.subplots(figsize=(11, 10))
ax.set_xlim(-1.15, 1.15)
ax.set_ylim(-1.15, 1.15)
ax.axis('off')
plt.title(f'STDP - 5 Neurônios (Rede nova a cada execução)\n'
          f'Entradas externas: Sempre 1 por vez | Intervalo: {MIN_INTERVAL}-{MAX_INTERVAL} frames',
          fontsize=13, pad=25)

# Desenha neurônios
neuron_patches = []
extra_circles = []
for i in range(N_NEURONS):
    x, y = pos[i]
    is_input = G.nodes[i]['is_input']
    in_deg = G.nodes[i]['in_degree']
    out_deg = G.nodes[i]['out_degree']
    
    if is_input:
        patch = Rectangle((x-0.06, y-0.06), 0.12, 0.12, color='royalblue', ec='black', lw=2.8)
    elif out_deg >= 3:
        patch = Polygon([[x, y+0.07], [x-0.06, y-0.05], [x+0.06, y-0.05]], color='crimson', ec='black', lw=2.5)
    else:
        patch = plt.Circle((x, y), 0.055, color='lightgray', ec='black', lw=2)
    
    ax.add_patch(patch)
    neuron_patches.append(patch)
    
    ext = MplCircle((x, y), 0.082, fill=False, ec='lime', lw=3.2, alpha=0)
    ax.add_patch(ext)
    extra_circles.append(ext)

# Conexões
arrows = []
arrow_texts = []
for u, v, data in G.edges(data=True):
    x1, y1 = pos[u]
    x2, y2 = pos[v]
    arrow = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='->', mutation_scale=22,
                            linewidth=data['weight']*5.5, color='gray', alpha=0.85)
    ax.add_patch(arrow)
    arrows.append((arrow, u, v, data))
    
    mx = (x1 + x2)/2
    my = (y1 + y2)/2 + 0.028
    txt = ax.text(mx, my, f"{data['weight']:.2f}", fontsize=9.5, ha='center', va='center', color='darkblue', weight='bold')
    arrow_texts.append(txt)

last_spike_time = np.full(N_NEURONS, -1000.0)
next_input_time = np.full(N_NEURONS, -1000)

def stdp_delta(pre, post):
    dt = post - pre
    if dt > 0:
        return A_plus * np.exp(-dt / tau_plus)
    return -A_minus * np.exp(dt / tau_minus)

def update(frame):
    t = frame

    # ====================== ENTRADAS EXTERNAS (sempre só 1) ======================
    active_pre = []
    
    if INPUT_MODE == "synchronous":
        if t % random.randint(MIN_INTERVAL, MAX_INTERVAL + 1) == 0:
            active_pre = [random.choice(input_nodes)]
    else:
        for i in input_nodes:                     # só neurônios de entrada podem receber input externo
            if t >= next_input_time[i]:
                if random.random() < 0.38:        # chance razoável
                    active_pre.append(i)
                    interval = random.randint(MIN_INTERVAL, MAX_INTERVAL + 1)
                    next_input_time[i] = t + interval
                    break                         # garante no máximo 1 por frame

    # Aplica a entrada (sempre no máximo 1)
    for pre in active_pre:
        last_spike_time[pre] = t
        extra_circles[pre].set_alpha(0.95)
        
        for _, v, data in G.out_edges(pre, data=True):
            if random.random() < min(0.95, data['weight'] * 0.88):
                last_spike_time[v] = t + random.uniform(2, 12)

    # STDP
    for arrow_patch, u, v, data in arrows:
        pre_t = last_spike_time[u]
        post_t = last_spike_time[v]
        if abs(pre_t - t) < 220 and abs(post_t - t) < 220:
            dw = stdp_delta(pre_t, post_t)
            if abs(dw) > 0.0001:
                new_w = np.clip(data['weight'] + dw, 0.05, 1.4)
                data['weight'] = new_w
                data['flash_frames'] = 4
                
                arrow_patch.set_linewidth(new_w * 5.5)
                if dw > 0.0015:   arrow_patch.set_color('lime')
                elif dw > 0.0002: arrow_patch.set_color('cyan')
                elif dw < -0.0015: arrow_patch.set_color('magenta')
                else:             arrow_patch.set_color('red')

    # Atualiza visual dos neurônios
    for i, patch in enumerate(neuron_patches):
        if abs(last_spike_time[i] - t) < 32:
            patch.set_color('gold')
        else:
            if G.nodes[i]['is_input']:
                patch.set_color('royalblue')
            elif G.nodes[i]['out_degree'] >= 3:
                patch.set_color('crimson')
            else:
                patch.set_color('lightgray')
        
        if extra_circles[i].get_alpha() > 0:
            extra_circles[i].set_alpha(max(0, extra_circles[i].get_alpha() - 0.16))

    # Atualiza textos e flash das setas
    for i, txt in enumerate(arrow_texts):
        u, v, data = arrows[i][1], arrows[i][2], arrows[i][3]
        txt.set_text(f"{data['weight']:.2f}")
        if data.get('flash_frames', 0) > 0:
            data['flash_frames'] -= 1
        else:
            arrows[i][0].set_color('gray')
            arrows[i][0].set_alpha(0.85)

    return neuron_patches + [a[0] for a in arrows] + arrow_texts + extra_circles

# ====================== ANIMAÇÃO ======================
ani = animation.FuncAnimation(fig, update, frames=4000, interval=55, blit=False, repeat=True)

# Controles
ax_slider = plt.axes([0.18, 0.03, 0.6, 0.03])
slider = Slider(ax_slider, 'Velocidade', 1, 40, valinit=9)
slider.on_changed(lambda v: setattr(ani.event_source, 'interval', int(v * 7)))

ax_reset = plt.axes([0.82, 0.03, 0.13, 0.05])
Button(ax_reset, 'Reset Pesos').on_clicked(lambda e: print("Pesos resetados!"))

plt.show()