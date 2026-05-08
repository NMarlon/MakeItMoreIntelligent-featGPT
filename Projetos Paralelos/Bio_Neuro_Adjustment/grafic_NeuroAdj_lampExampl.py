# grafic_NeuroAdj_lampExampl.py
import pygame
import pygame_gui
import sys
from pygame.math import Vector2
import NeuronAdjustment_lampExample as sim

pygame.init()
screen = pygame.display.set_mode((1380, 920), pygame.RESIZABLE)
pygame.display.set_caption("STDP - Sliders em Tempo Real")
clock = pygame.time.Clock()
manager = pygame_gui.UIManager((1380, 920))

# Painel de sliders
panel = pygame_gui.elements.UIPanel(relative_rect=pygame.Rect((1380 - 355, 10), (335, 900)), manager=manager)

def make_slider(y, text, default, minv, maxv, step=0.001):
    pygame_gui.elements.UILabel(relative_rect=pygame.Rect((10, y), (155, 25)), text=text, manager=manager, container=panel)
    return pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect((170, y), (150, 25)), start_value=default, value_range=(minv, maxv), manager=manager, container=panel)

s_n = make_slider(20, "N_NEURONS", 18, 5, 40, 1)
s_input = make_slider(55, "NUM_INPUT", 3, 1, 10, 1)
s_minconn = make_slider(90, "MIN_CONN", 1, 1, 8, 1)
s_maxconn = make_slider(125, "MAX_CONN", 3, 1, 12, 1)
s_minint = make_slider(160, "MIN_INTERVAL", 1, 1, 300, 1)
s_maxint = make_slider(195, "MAX_INTERVAL", 30, 1, 1000, 1)
s_aplus = make_slider(230, "A_plus (LTP)", 0.0085, 0.001, 0.05, 0.0005)
s_aminus = make_slider(265, "A_minus (LTD)", 0.022, 0.001, 0.1, 0.0005)
s_attr = make_slider(300, "ATTRACTION", 0.0055, 0.001, 0.03, 0.0005)
s_repall = make_slider(335, "REPULSION_ALL", 60000, 5000, 300000, 1000)
s_repnon = make_slider(370, "REP_NON_CONN", 150000, 20000, 500000, 5000)
s_damp = make_slider(405, "DAMPING", 0.84, 0.6, 0.98, 0.01)
s_margin = make_slider(440, "MARGIN", -250, -500, 400, 10)
s_r = make_slider(475, "R (raio)", 1150, 400, 2000, 10)

frame = 0
running = True

sim.reset_simulation()

while running:
    time_delta = clock.tick(60) / 1000.0
    frame = sim.frame = frame + 1
    t = frame

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEWHEEL:
            old = sim.zoom
            sim.zoom *= 1.08 if event.y > 0 else 0.93
            sim.zoom = max(0.25, min(sim.zoom, 6.0))
            mouse = Vector2(pygame.mouse.get_pos())
            world = (mouse - Vector2(1380/2, 920/2)) / old + Vector2(1380/2, 920/2)
            sim.camera_offset = mouse - (world - sim.camera_offset) * sim.zoom

        manager.process_events(event)

    manager.update(time_delta)

    # Atualiza parâmetros
    sim.N_NEURONS = int(s_n.get_current_value())
    sim.NUM_INPUT_NEURONS = int(s_input.get_current_value())
    sim.MIN_CONNECTIONS_PER_NEURON = int(s_minconn.get_current_value())
    sim.MAX_CONNECTIONS_PER_NEURON = int(s_maxconn.get_current_value())
    sim.MIN_INTERVAL = int(s_minint.get_current_value())
    sim.MAX_INTERVAL = int(s_maxint.get_current_value())
    sim.A_plus = s_aplus.get_current_value()
    sim.A_minus = s_aminus.get_current_value()
    sim.ATTRACTION = s_attr.get_current_value()
    sim.REPULSION_ALL = s_repall.get_current_value()
    sim.REPULSION_NON_CONNECTED = s_repnon.get_current_value()
    sim.DAMPING = s_damp.get_current_value()
    sim.MARGIN = int(s_margin.get_current_value())
    sim.R = int(s_r.get_current_value())

    sim.active_pre = sim.update_simulation()

    screen.fill(sim.BG_COLOR)
    sim.draw(screen)

    manager.draw_ui(screen)
    pygame.display.flip()

pygame.quit()
sys.exit()