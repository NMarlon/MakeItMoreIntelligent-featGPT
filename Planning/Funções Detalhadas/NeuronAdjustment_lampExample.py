import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle
import matplotlib.animation as animation
from matplotlib.widgets import Slider, Button
import networkx as nx

# ====================== PARÂMETROS AJUSTÁVEIS ======================
N_NEURONS = 50
MIN_IN = 1
MAX_IN = 10
MIN_OUT = 1
MAX_OUT = 10

A_plus = 0.008
A_minus = 0.0085
tau_plus = 20.0
tau_minus = 20.0

# ====================== CRIAÇÃO DA REDE ======================
np.random.seed(42)
G = nx.DiGraph()

# Posições em círculo para visualização bonita
pos = {i: (np.cos(2*np.pi*i/N_NEURONS), np.sin(2*np.pi*i/N_NEURONS)) for i in range(N_NEURONS)}

# Adiciona neurônios e conexões aleatórias
for i in range(N_NEURONS):
    G.add_node(i, weight_history=[])
    num_out = np.random.randint(MIN_OUT, MAX_OUT + 1)
    targets = np.random.choice([j for j in range(N_NEURONS) if j != i], num_out, replace=False)
    for t in targets:
        weight = np.random.uniform(0.3, 0.8)
        # Cada sinapse guarda tambem quantos frames faltam para manter o "flash"
        # visual. Isso evita depender de metodos de leitura de cor que alguns
        # patches do matplotlib nao implementam.
        G.add_edge(i, t, weight=weight, last_delta=0.0, flash_frames=0)

# ====================== FUNÇÃO STDP ======================
def stdp_delta(pre_time, post_time):
    dt = post_time - pre_time
    if dt > 0:
        return A_plus * np.exp(-dt / tau_plus)
    else:
        return -A_minus * np.exp(dt / tau_minus)

# ====================== FIGURA E ANIMAÇÃO ======================
fig, ax = plt.subplots(figsize=(12, 10))
ax.set_xlim(-1.2, 1.2)
ax.set_ylim(-1.2, 1.2)
ax.axis('off')
plt.title('Simulação STDP - Sala das Lâmpadas (50 neurônios)\n'
          'Azul = LTP forte | Vermelho = LTD forte | Verde claro = ajuste positivo | Roxo = ajuste negativo', 
          fontsize=14, pad=30)

# Desenha neurônios (círculos)
circles = [Circle(pos[i], 0.04, color='lightgray', ec='black', lw=1.5) for i in range(N_NEURONS)]
for c in circles:
    ax.add_patch(c)

# Desenha setas (conexões) com espessura proporcional ao peso
arrows = []
arrow_texts = []
for u, v, data in G.edges(data=True):
    x1, y1 = pos[u]
    x2, y2 = pos[v]
    arrow = FancyArrowPatch((x1, y1), (x2, y2), 
                            arrowstyle='->', mutation_scale=15,
                            linewidth=data['weight']*4,
                            color='gray', alpha=0.7)
    ax.add_patch(arrow)
    arrows.append((arrow, u, v, data))
    
    # Texto do peso (pequeno)
    mx, my = (x1 + x2)/2, (y1 + y2)/2
    txt = ax.text(mx, my, f"{data['weight']:.2f}", fontsize=8, ha='center', va='center', color='darkblue')
    arrow_texts.append(txt)

# Variáveis de estado
last_spike_time = np.full(N_NEURONS, -1000.0)  # tempo do último spike de cada neurônio
current_frame = 0

def update(frame):
    global current_frame
    current_frame = frame
    t = frame * 5.0  # tempo simulado em ms (cada frame ~5 ms)

    # 1. Escolhe aleatoriamente 1 a 10 neurônios para "piscar" como input (pré)
    active_pre = np.random.choice(N_NEURONS, np.random.randint(MIN_IN, MAX_IN+1), replace=False)
    
    # 2. Para cada pré ativo, atualiza tempo e verifica quais pós vão disparar
    for pre in active_pre:
        last_spike_time[pre] = t
        # Propaga para todos os alvos (pós)
        for _, v, data in G.out_edges(pre, data=True):
            # Simula se o pós dispara (probabilidade proporcional ao peso)
            if np.random.rand() < data['weight'] * 0.7:
                last_spike_time[v] = t + np.random.uniform(1, 15)  # pequeno delay

    # 3. Aplica STDP em TODAS as sinapses
    for arrow_patch, u, v, data in arrows:
        pre_t = last_spike_time[u]
        post_t = last_spike_time[v]
        
        if abs(pre_t - t) < 100 and abs(post_t - t) < 100:  # só atualiza se houve atividade recente
            dt = post_t - pre_t
            dw = stdp_delta(pre_t, post_t)
            
            if abs(dw) > 0.0001:  # só ajusta se houver mudança significativa
                old_w = data['weight']
                new_w = np.clip(old_w + dw, 0.05, 1.2)
                data['weight'] = new_w
                data['last_delta'] = dw
                
                # Atualiza visual da seta
                arrow_patch.set_linewidth(new_w * 4)
                
                # Mudança de cor temporária (pisca)
                if dw > 0.001:
                    arrow_patch.set_color('lime')      # ajuste positivo forte
                elif dw > 0.0001:
                    arrow_patch.set_color('cyan')      # positivo leve
                elif dw < -0.001:
                    arrow_patch.set_color('magenta')   # negativo forte
                elif dw < -0.0001:
                    arrow_patch.set_color('red')       # negativo leve
                # Mantem a cor por alguns frames para o olho humano conseguir ver
                # o ajuste antes da seta voltar ao estado neutro.
                data['flash_frames'] = 2
                arrow_patch.set_alpha(0.95)

    # 4. Atualiza cores dos neurônios (piscam quando disparam)
    for i, circle in enumerate(circles):
        if abs(last_spike_time[i] - t) < 20:
            circle.set_color('yellow')
            circle.set_radius(0.055)
        else:
            circle.set_color('lightgray')
            circle.set_radius(0.04)

    # 5. Atualiza textos dos pesos
    for i, txt in enumerate(arrow_texts):
        u, v, data = arrows[i][1], arrows[i][2], arrows[i][3]
        txt.set_text(f"{data['weight']:.2f}")
        # Controla o flash por estado proprio da sinapse, em vez de consultar a
        # cor atual do patch. FancyArrowPatch nao implementa get_color().
        if data['flash_frames'] > 0:
            data['flash_frames'] -= 1
        else:
            arrows[i][0].set_color('gray')
            arrows[i][0].set_alpha(0.7)

    return circles + [a[0] for a in arrows] + arrow_texts

# ====================== ANIMAÇÃO ======================
ani = animation.FuncAnimation(fig, update, frames=800, interval=80, blit=False, repeat=True)

# ====================== CONTROLES ======================
ax_slider = plt.axes([0.2, 0.02, 0.6, 0.03])
slider = Slider(ax_slider, 'Velocidade (ms/frame)', 1, 20, valinit=5, valstep=1)

def update_speed(val):
    ani.event_source.interval = int(val * 10)  # ajusta velocidade

slider.on_changed(update_speed)

# Botão Reset
ax_reset = plt.axes([0.85, 0.02, 0.1, 0.04])
btn_reset = Button(ax_reset, 'Reset Pesos')

def reset(event):
    for arrow_patch, _, _, data in arrows:
        data['weight'] = np.random.uniform(0.3, 0.8)
        data['last_delta'] = 0.0
        data['flash_frames'] = 0
        # O reset precisa restaurar tambem a aparencia da conexao, senao o estado
        # visual pode ficar diferente do peso real ate o proximo ajuste STDP.
        arrow_patch.set_linewidth(data['weight'] * 4)
        arrow_patch.set_color('gray')
        arrow_patch.set_alpha(0.7)
    print("Pesos resetados!")

btn_reset.on_clicked(reset)

plt.show()
