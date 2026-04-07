import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle, Circle as MplCircle
import matplotlib.animation as animation
from matplotlib.widgets import Slider, Button
import networkx as nx

# ====================== PARÂMETROS ======================
N_NEURONS = 5
MIN_IN = 1     # aumentei um pouco
MAX_IN = 1
MIN_OUT = 0
MAX_OUT = 0

A_plus = 0.008
A_minus = 0.0085
tau_plus = 20.0
tau_minus = 20.0

# ====================== CRIAÇÃO DA REDE ======================
np.random.seed(42)
G = nx.DiGraph()

for i in range(N_NEURONS):
    G.add_node(i, out_degree=0, in_degree=0)

for i in range(N_NEURONS):
    num_out = np.random.randint(MIN_OUT, MAX_OUT + 1)
    targets = np.random.choice([j for j in range(N_NEURONS) if j != i], num_out, replace=False)
    for t in targets:
        weight = np.random.uniform(0.3, 0.8)
        G.add_edge(i, t, weight=weight, last_delta=0.0, flash_frames=0)
        G.nodes[i]['out_degree'] += 1
        G.nodes[t]['in_degree'] += 1

# Garantia: todo nó tem pelo menos 1 entrada (ajuste se necessário)
for node in G.nodes():
    if G.nodes[node]['in_degree'] == 0:
        target = np.random.choice([j for j in range(N_NEURONS) if j != node])
        G.add_edge(target, node, weight=np.random.uniform(0.4, 0.7), last_delta=0.0, flash_frames=0)
        G.nodes[target]['out_degree'] += 1
        G.nodes[node]['in_degree'] += 1

# Layout automático
pos = nx.spring_layout(G, k=0.38, iterations=180, seed=42)

# ====================== FIGURA ======================
fig, ax = plt.subplots(figsize=(14, 12))
ax.set_xlim(-1.25, 1.25)
ax.set_ylim(-1.25, 1.25)
ax.axis('off')
plt.title('STDP - Sala das Lâmpadas (Corrigido)\n'
          '■ Quadrado Azul = Muitas Entradas | ▲ Triângulo Vermelho = Muitas Saídas\n'
          'Borda vermelha = Poucas entradas externas | Círculo verde externo = Input do mundo', 
          fontsize=14, pad=30)

# Desenha neurônios
neuron_patches = []
extra_circles = []  # para marcar input externo
for i in range(N_NEURONS):
    x, y = pos[i]
    in_deg = G.nodes[i]['in_degree']
    out_deg = G.nodes[i]['out_degree']
    
    if in_deg >= 6:
        patch = Rectangle((x-0.05, y-0.05), 0.1, 0.1, color='royalblue', ec='black', lw=2.2)
    elif out_deg >= 6:
        patch = Polygon([[x, y+0.058], [x-0.052, y-0.042], [x+0.052, y-0.042]], 
                        color='crimson', ec='black', lw=2.2)
    else:
        patch = plt.Circle((x, y), 0.044, color='lightgray', ec='black', lw=1.7)
    
    # Borda vermelha se tem poucas entradas
    if in_deg < 3:
        ec_patch = MplCircle((x, y), 0.055, fill=False, ec='red', lw=2.5, alpha=0.8)
        ax.add_patch(ec_patch)
    
    ax.add_patch(patch)
    neuron_patches.append(patch)
    
    # Círculo externo para marcar input do mundo (será ativado depois)
    ext = MplCircle((x, y), 0.065, fill=False, ec='lime', lw=2.5, alpha=0)
    ax.add_patch(ext)
    extra_circles.append(ext)

# Desenha conexões (igual antes)
arrows = []
arrow_texts = []
for u, v, data in G.edges(data=True):
    x1, y1 = pos[u]
    x2, y2 = pos[v]
    arrow = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='->', mutation_scale=18,
                            linewidth=data['weight']*3.8, color='gray', alpha=0.78)
    ax.add_patch(arrow)
    arrows.append((arrow, u, v, data))
    
    mx = (x1+x2)/2
    my = (y1+y2)/2 + 0.02
    txt = ax.text(mx, my, f"{data['weight']:.2f}", fontsize=7.5, ha='center', va='center', color='navy')
    arrow_texts.append(txt)

last_spike_time = np.full(N_NEURONS, -1000.0)

def stdp_delta(pre, post):
    dt = post - pre
    if dt > 0:
        return A_plus * np.exp(-dt / tau_plus)
    return -A_minus * np.exp(dt / tau_minus)

def update(frame):
    t = frame * 5.0

    # === INPUTS EXTERNOS (do mundo) - agora mais visíveis ===
    num_external = np.random.randint(MIN_IN, MAX_IN+1)
    active_pre = np.random.choice(N_NEURONS, num_external, replace=False)
    
    for pre in active_pre:
        last_spike_time[pre] = t
        extra_circles[pre].set_alpha(0.9)   # círculo verde externo aparece forte
        # propaga
        for _, v, data in G.out_edges(pre, data=True):
            if np.random.rand() < min(0.92, data['weight']*0.8):
                last_spike_time[v] = t + np.random.uniform(1.5, 14)

    # STDP (igual antes)
    for arrow_patch, u, v, data in arrows:
        pre_t = last_spike_time[u]
        post_t = last_spike_time[v]
        if abs(pre_t - t) < 130 and abs(post_t - t) < 130:
            dw = stdp_delta(pre_t, post_t)
            if abs(dw) > 0.00008:
                new_w = np.clip(data['weight'] + dw, 0.05, 1.3)
                data['weight'] = new_w
                data['flash_frames'] = 3
                arrow_patch.set_linewidth(new_w * 3.8)
                if dw > 0.0015: arrow_patch.set_color('lime')
                elif dw > 0.0001: arrow_patch.set_color('cyan')
                elif dw < -0.0015: arrow_patch.set_color('magenta')
                else: arrow_patch.set_color('red')

    # Atualiza neurônios
    for i, patch in enumerate(neuron_patches):
        if abs(last_spike_time[i] - t) < 28:
            patch.set_color('gold')
        else:
            # volta cor normal
            in_deg = G.nodes[i]['in_degree']
            if in_deg >= 6:
                patch.set_color('royalblue')
            elif G.nodes[i]['out_degree'] >= 6:
                patch.set_color('crimson')
            else:
                patch.set_color('lightgray')
        
        # fade do círculo externo de input
        if extra_circles[i].get_alpha() > 0:
            extra_circles[i].set_alpha(max(0, extra_circles[i].get_alpha() - 0.12))

    # Atualiza textos e flash das setas
    for i, txt in enumerate(arrow_texts):
        u, v, data = arrows[i][1], arrows[i][2], arrows[i][3]
        txt.set_text(f"{data['weight']:.2f}")
        if data.get('flash_frames', 0) > 0:
            data['flash_frames'] -= 1
        else:
            arrows[i][0].set_color('gray')
            arrows[i][0].set_alpha(0.78)

    return neuron_patches + [a[0] for a in arrows] + arrow_texts + extra_circles

# Animação e controles (igual antes)
ani = animation.FuncAnimation(fig, update, frames=1500, interval=75, blit=False, repeat=True)

# Slider e Reset (mesmo código de antes - copiei para não ficar incompleto)
ax_slider = plt.axes([0.15, 0.03, 0.6, 0.03])
slider = Slider(ax_slider, 'Velocidade', 2, 30, valinit=5)
slider.on_changed(lambda val: setattr(ani.event_source, 'interval', int(val*8)))

ax_reset = plt.axes([0.82, 0.03, 0.13, 0.045])
Button(ax_reset, 'Reset Pesos').on_clicked(lambda e: print("Reset feito - implemente se quiser"))

plt.show()