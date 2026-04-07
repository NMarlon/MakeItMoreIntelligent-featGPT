import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle
import matplotlib.animation as animation
from matplotlib.widgets import Slider, Button
import networkx as nx

# ====================== PARÂMETROS AJUSTÁVEIS ======================
N_NEURONS = 12
MIN_IN = 1
MAX_IN = 2
MIN_OUT = 1
MAX_OUT = 2          # conexões mais esparsas para ficar menos bagunçado

A_plus = 0.008
A_minus = 0.0085
tau_plus = 20.0
tau_minus = 20.0

# ====================== CRIAÇÃO DA REDE (corrigido) ======================
np.random.seed(42)
G = nx.DiGraph()

# Primeiro cria todos os nós com atributos zerados
for i in range(N_NEURONS):
    G.add_node(i, out_degree=0, in_degree=0)

# Agora adiciona as conexões
for i in range(N_NEURONS):
    num_out = np.random.randint(MIN_OUT, MAX_OUT + 1)
    possible_targets = [j for j in range(N_NEURONS) if j != i]
    targets = np.random.choice(possible_targets, num_out, replace=False)
    
    for t in targets:
        weight = np.random.uniform(0.3, 0.8)
        G.add_edge(i, t, weight=weight, last_delta=0.0, flash_frames=0)
        
        # Incrementa graus de forma segura
        G.nodes[i]['out_degree'] += 1
        G.nodes[t]['in_degree'] += 1

# ====================== LAYOUT AUTOMÁTICO (tipo Obsidian) ======================
pos = nx.spring_layout(G, k=0.4, iterations=200, seed=42)

# ====================== FIGURA ======================
fig, ax = plt.subplots(figsize=(13.5, 11.5))
ax.set_xlim(-1.2, 1.2)
ax.set_ylim(-1.2, 1.2)
ax.axis('off')
plt.title('Simulação STDP - Sala das Lâmpadas (Layout Automático Obsidian-style)\n'
          '■ Quadrado Azul = Neurônio com muitas ENTRADAS  |  ▲ Triângulo Vermelho = muitas SAÍDAS\n'
          'Verde/Cyan = LTP (+)  |  Magenta/Vermelho = LTD (-)', fontsize=14, pad=30)

# ====================== DESENHA NEURÔNIOS COM FORMAS ======================
neuron_patches = []
for i in range(N_NEURONS):
    x, y = pos[i]
    in_deg = G.nodes[i]['in_degree']
    out_deg = G.nodes[i]['out_degree']
    
    if in_deg >= 6:           # muitas entradas
        patch = Rectangle((x-0.048, y-0.048), 0.096, 0.096, 
                          color='royalblue', ec='black', lw=2)
    elif out_deg >= 6:        # muitas saídas
        patch = Polygon([[x, y+0.055], [x-0.05, y-0.04], [x+0.05, y-0.04]],
                        color='crimson', ec='black', lw=2)
    else:
        patch = plt.Circle((x, y), 0.043, color='lightgray', ec='black', lw=1.6)
    
    ax.add_patch(patch)
    neuron_patches.append(patch)

# ====================== DESENHA CONEXÕES ======================
arrows = []
arrow_texts = []
for u, v, data in G.edges(data=True):
    x1, y1 = pos[u]
    x2, y2 = pos[v]
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                            arrowstyle='->', mutation_scale=18,
                            linewidth=data['weight']*3.8,
                            color='gray', alpha=0.78, zorder=1)
    ax.add_patch(arrow)
    arrows.append((arrow, u, v, data))
    
    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2 + 0.018
    txt = ax.text(mx, my, f"{data['weight']:.2f}", fontsize=7.8, 
                  ha='center', va='center', color='navy', zorder=3)
    arrow_texts.append(txt)

# ====================== VARIÁVEIS DE ESTADO ======================
last_spike_time = np.full(N_NEURONS, -1000.0)

def stdp_delta(pre_time, post_time):
    dt = post_time - pre_time
    if dt > 0:
        return A_plus * np.exp(-dt / tau_plus)
    else:
        return -A_minus * np.exp(dt / tau_minus)

def update(frame):
    t = frame * 5.0

    # Inputs aleatórios (pré)
    active_pre = np.random.choice(N_NEURONS, np.random.randint(MIN_IN, MAX_IN+1), replace=False)
    
    for pre in active_pre:
        last_spike_time[pre] = t
        for _, v, data in G.out_edges(pre, data=True):
            if np.random.rand() < min(0.9, data['weight'] * 0.78):
                last_spike_time[v] = t + np.random.uniform(1.5, 13)

    # Aplica STDP
    for arrow_patch, u, v, data in arrows:
        pre_t = last_spike_time[u]
        post_t = last_spike_time[v]
        
        if abs(pre_t - t) < 130 and abs(post_t - t) < 130:
            dw = stdp_delta(pre_t, post_t)
            
            if abs(dw) > 0.00008:
                new_w = np.clip(data['weight'] + dw, 0.05, 1.3)
                data['weight'] = new_w
                data['last_delta'] = dw
                data['flash_frames'] = 3
                
                arrow_patch.set_linewidth(new_w * 3.8)
                
                if dw > 0.0015:
                    arrow_patch.set_color('lime')
                elif dw > 0.0001:
                    arrow_patch.set_color('cyan')
                elif dw < -0.0015:
                    arrow_patch.set_color('magenta')
                elif dw < -0.0001:
                    arrow_patch.set_color('red')

    # Atualiza aparência dos neurônios
    for i, patch in enumerate(neuron_patches):
        if abs(last_spike_time[i] - t) < 25:
            patch.set_color('gold')
            if isinstance(patch, plt.Circle):
                patch.set_radius(0.057)
        else:
            in_deg = G.nodes[i]['in_degree']
            out_deg = G.nodes[i]['out_degree']
            if in_deg >= 6:
                patch.set_color('royalblue')
            elif out_deg >= 6:
                patch.set_color('crimson')
            else:
                patch.set_color('lightgray')
            if isinstance(patch, plt.Circle):
                patch.set_radius(0.043)

    # Atualiza textos e flash das setas
    for i, txt in enumerate(arrow_texts):
        u, v, data = arrows[i][1], arrows[i][2], arrows[i][3]
        txt.set_text(f"{data['weight']:.2f}")
        
        if data.get('flash_frames', 0) > 0:
            data['flash_frames'] -= 1
        else:
            arrows[i][0].set_color('gray')
            arrows[i][0].set_alpha(0.78)

    return neuron_patches + [a[0] for a in arrows] + arrow_texts

# ====================== ANIMAÇÃO ======================
ani = animation.FuncAnimation(fig, update, frames=1500, interval=70, blit=False, repeat=True)

# ====================== CONTROLES ======================
ax_slider = plt.axes([0.15, 0.025, 0.6, 0.03])
slider = Slider(ax_slider, 'Velocidade (ms/frame)', 2, 30, valinit=5, valstep=1)

def update_speed(val):
    ani.event_source.interval = int(val * 8)
slider.on_changed(update_speed)

ax_reset = plt.axes([0.82, 0.025, 0.13, 0.045])
btn_reset = Button(ax_reset, 'Reset Pesos')

def reset(event):
    for _, _, data in G.edges(data=True):
        data['weight'] = np.random.uniform(0.3, 0.85)
        data['flash_frames'] = 0
    for arrow_patch, _, _, data in arrows:
        arrow_patch.set_linewidth(data['weight'] * 3.8)
        arrow_patch.set_color('gray')
        arrow_patch.set_alpha(0.78)
    print("Pesos resetados com sucesso!")
btn_reset.on_clicked(reset)

plt.show()