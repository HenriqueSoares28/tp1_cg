import pygame
import math
import sys
import copy

pygame.init()

# Configs
WIDTH, HEIGHT = 1400, 800
COLORS = {
    'background': (255, 255, 255),
    'toolbar': (50, 50, 60),
    'sidebar': (70, 70, 80),
    'button': (90, 90, 100),
    'active': (110, 200, 100),
    'hover': (130, 130, 140),
    'selection': (255, 150, 50, 100),
    'highlight': (255, 200, 0),
    'draw': (0, 0, 0),
    'clip': (255, 0, 0),
    'text': (220, 220, 220)
}

# Linha DDA.
def draw_line_dda(surface, start, end, color, thickness=1):
    x0, y0 = start
    x1, y1 = end
    dx = x1 - x0
    dy = y1 - y0
    steps = int(max(abs(dx), abs(dy)))
    if steps == 0:
        pygame.draw.circle(surface, color, (int(x0), int(y0)), thickness)
        return
    x_inc = dx / steps
    y_inc = dy / steps
    x, y = x0, y0
    for _ in range(steps):
        pygame.draw.circle(surface, color, (int(round(x)), int(round(y))), thickness)
        x += x_inc
        y += y_inc

# Linha Bresenham.
def draw_line_bresenham(surface, start, end, color, thickness=1):
    x0, y0 = map(int, start)
    x1, y1 = map(int, end)
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        pygame.draw.circle(surface, color, (x0, y0), thickness)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy

# Círculo Bresenham.
def draw_circle_bresenham(surface, center, radius, color, thickness=1):
    cx, cy = center
    x = 0
    y = radius
    d = 3 - 2 * radius
    def draw_circle_points(cx, cy, x, y):
        pts = [
            (cx + x, cy + y), (cx - x, cy + y),
            (cx + x, cy - y), (cx - x, cy - y),
            (cx + y, cy + x), (cx - y, cy + x),
            (cx + y, cy - x), (cx - y, cy - x)
        ]
        for pt in pts:
            pygame.draw.circle(surface, color, pt, thickness)
    while y >= x:
        draw_circle_points(cx, cy, x, y)
        x += 1
        if d > 0:
            y -= 1
            d += 4 * (x - y) + 10
        else:
            d += 4 * x + 6
        draw_circle_points(cx, cy, x, y)

# ================ (clipping) ================ 
INSIDE, LEFT, RIGHT, BOTTOM, TOP = 0, 1, 2, 4, 8

def compute_out_code(x, y, rect):
    # Onde o ponto está em relação ao retângulo.
    code = 0
    if x < rect.left:
        code |= LEFT
    elif x > rect.right:
        code |= RIGHT
    if y < rect.top:
        code |= TOP
    elif y > rect.bottom:
        code |= BOTTOM
    return code

# Recorte de Cohen–Sutherland linhas.
def cohen_sutherland_clip(line, clip_rect):
    x0, y0 = line[0]
    x1, y1 = line[1]
    outcode0 = compute_out_code(x0, y0, clip_rect)
    outcode1 = compute_out_code(x1, y1, clip_rect)
    accept = False
    while True:
        if not (outcode0 | outcode1):
            accept = True
            break
        elif outcode0 & outcode1:
            break
        else:
            outcode_out = outcode0 if outcode0 else outcode1
            if outcode_out & TOP:
                x = x0 + (x1 - x0) * (clip_rect.top - y0) / (y1 - y0)
                y = clip_rect.top
            elif outcode_out & BOTTOM:
                x = x0 + (x1 - x0) * (clip_rect.bottom - y0) / (y1 - y0)
                y = clip_rect.bottom
            elif outcode_out & RIGHT:
                y = y0 + (y1 - y0) * (clip_rect.right - x0) / (x1 - x0)
                x = clip_rect.right
            elif outcode_out & LEFT:
                y = y0 + (y1 - y0) * (clip_rect.left - x0) / (x1 - x0)
                x = clip_rect.left
            if outcode_out == outcode0:
                x0, y0 = x, y
                outcode0 = compute_out_code(x0, y0, clip_rect)
            else:
                x1, y1 = x, y
                outcode1 = compute_out_code(x1, y1, clip_rect)
    return [(x0, y0), (x1, y1)] if accept else None

# Recorte de Liang–Barsky linhas.
def liang_barsky_clip(line, clip_rect):
    x0, y0 = line[0]
    x1, y1 = line[1]
    dx = x1 - x0
    dy = y1 - y0
    p = [-dx, dx, -dy, dy]
    q = [x0 - clip_rect.left, clip_rect.right - x0, y0 - clip_rect.top, clip_rect.bottom - y0]
    u1, u2 = 0, 1
    for i in range(4):
        if p[i] == 0:
            if q[i] < 0:
                return None
        else:
            t = q[i] / p[i]
            if p[i] < 0:
                u1 = max(u1, t)
            else:
                u2 = min(u2, t)
    if u1 > u2:
        return None
    new_start = (x0 + u1 * dx, y0 + u1 * dy)
    new_end = (x0 + u2 * dx, y0 + u2 * dy)
    return [new_start, new_end]

# Rcorte de Sutherland–Hodgman polígonos.
def sutherland_hodgman_clip(polygon, clip_rect):
    def inside(p, edge):
        x, y = p
        if edge == 'left':
            return x >= clip_rect.left
        elif edge == 'right':
            return x <= clip_rect.right
        elif edge == 'top':
            return y >= clip_rect.top
        elif edge == 'bottom':
            return y <= clip_rect.bottom
    def intersection(p1, p2, edge):
        x1, y1 = p1
        x2, y2 = p2
        if edge in ['left', 'right']:
            x_edge = clip_rect.left if edge == 'left' else clip_rect.right
            t = (x_edge - x1) / (x2 - x1) if x2 != x1 else 0
            y = y1 + t * (y2 - y1)
            return (x_edge, y)
        else:
            y_edge = clip_rect.top if edge == 'top' else clip_rect.bottom
            t = (y_edge - y1) / (y2 - y1) if y2 != y1 else 0
            x = x1 + t * (x2 - x1)
            return (x, y_edge)
    def clip_polygon(poly, edge):
        clipped = []
        if not poly:
            return clipped
        prev = poly[-1]
        for curr in poly:
            if inside(curr, edge):
                if not inside(prev, edge):
                    clipped.append(intersection(prev, curr, edge))
                clipped.append(curr)
            elif inside(prev, edge):
                clipped.append(intersection(prev, curr, edge))
            prev = curr
        return clipped
    for edge in ['left', 'right', 'top', 'bottom']:
        polygon = clip_polygon(polygon, edge)
    return polygon


# Botoes
class Button:
    def __init__(self, rect, text, callback):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.font = pygame.font.SysFont('Arial', 14)
    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        color = COLORS['active'] if self.rect.collidepoint(mouse_pos) else COLORS['button']
        pygame.draw.rect(surface, color, self.rect, border_radius=3)
        txt = self.font.render(self.text, True, COLORS['text'])
        surface.blit(txt, (self.rect.x + 5, self.rect.y + 5))
    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.callback()

# Representa as formas desenhadas.
class Shape:
    def __init__(self, shape_type, points, color, **kwargs):
        self.type = shape_type  
        self.points = [tuple(p) for p in points]
        self.color = color
        self.radius = kwargs.get('radius', 0)
        self.thickness = kwargs.get('thickness', 2)
        self.selected = False
        self.bounding_box = self.calculate_bounding_box()
    def calculate_bounding_box(self):
        if self.type in ['linha', 'desenho livre', 'polígono']:
            x_coords = [p[0] for p in self.points]
            y_coords = [p[1] for p in self.points]
            return pygame.Rect(min(x_coords), min(y_coords),
                               max(x_coords) - min(x_coords),
                               max(y_coords) - min(y_coords))
        elif self.type == 'círculo':
            return pygame.Rect(self.points[0][0] - self.radius,
                               self.points[0][1] - self.radius,
                               self.radius * 2,
                               self.radius * 2)
        return pygame.Rect(0, 0, 0, 0)
    def draw(self, surface, line_algo='DDA'):
        if self.type == 'linha':
            if line_algo == 'DDA':
                draw_line_dda(surface, self.points[0], self.points[1], self.color, self.thickness)
            else:
                draw_line_bresenham(surface, self.points[0], self.points[1], self.color, self.thickness)
        elif self.type == 'círculo':
            draw_circle_bresenham(surface, self.points[0], self.radius, self.color, self.thickness)
        elif self.type == 'desenho livre':
            for i in range(len(self.points) - 1):
                if line_algo == 'DDA':
                    draw_line_dda(surface, self.points[i], self.points[i+1], self.color, self.thickness)
                else:
                    draw_line_bresenham(surface, self.points[i], self.points[i+1], self.color, self.thickness)
        elif self.type == 'polígono':
            if len(self.points) >= 3:
                for i in range(len(self.points)):
                    start_pt = self.points[i]
                    end_pt = self.points[(i + 1) % len(self.points)]
                    if line_algo == 'DDA':
                        draw_line_dda(surface, start_pt, end_pt, self.color, self.thickness)
                    else:
                        draw_line_bresenham(surface, start_pt, end_pt, self.color, self.thickness)
        if self.selected:
            self.draw_selection(surface)
    def draw_selection(self, surface):
        pygame.draw.rect(surface, COLORS['highlight'], self.bounding_box.inflate(5, 5), 2)

class GraphicsEditor:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Editor Gráfico - TP1")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 18)
        self.small_font = pygame.font.SysFont('Arial', 14)

        self.toolbar_rect = pygame.Rect(0, 0, WIDTH, 50)
        self.sidebar_rect = pygame.Rect(WIDTH - 300, 0, 300, HEIGHT)
        self.drawing_area = pygame.Rect(0, 50, WIDTH - 300, HEIGHT - 50)

        # Modos de desenho
        self.modes = ['desenho livre', 'linha', 'círculo', 'polígono', 'selecionar', 'recorte']
        self.current_mode = 'linha'
        self.shapes = []
        self.selected_shapes = []
        self.temp_points = []
        self.dragging = False
        self.selection_rect = None
        self.clipping_window = None
        self.brush_size = 2
        self.drawing = False
        self.selection_start = None

        self.mode_button_width = 130
        self.line_algo = 'DDA'

        self.translation_active = False
        self.translation_start = None
        self.translation_orig = {}
        self.transformation_mode = None

        self.rotation_angle = 5
        self.transform_controls = []
        self.setup_transform_controls()

        self.toggle_line_algo_button = Button((WIDTH - 280, 700, 180, 30),
                                              f"Linha: {self.line_algo}", self.toggle_line_algo)

        self.size_minus_button = Button(pygame.Rect(0, 0, 30, 30), "-", self.decrease_brush_size)
        self.size_plus_button = Button(pygame.Rect(0, 0, 30, 30), "+", self.increase_brush_size)

        self.recorte_rect = None

        self.undo_stack = []
        self.redo_stack = []
        self.save_state()

    def setup_transform_controls(self):
        self.transform_controls.clear()
        start_y = 500  
        gap = 8
        btn_width = 120
        btn_height = 25
        col1_x = WIDTH - 280
        col2_x = WIDTH - 140

        # Linha 1
        self.transform_controls.append(Button((col1_x, start_y, btn_width, btn_height),
                                              "Rot+1°", lambda: self.rotate_selected(1)))
        self.transform_controls.append(Button((col2_x, start_y, btn_width, btn_height),
                                              "Rot-1°", lambda: self.rotate_selected(-1)))
        # Linha 2
        self.transform_controls.append(Button((col1_x, start_y + btn_height + gap, btn_width, btn_height),
                                              "Transladar", self.activate_translate))
        self.transform_controls.append(Button((col2_x, start_y + btn_height + gap, btn_width, btn_height),
                                              "Refletir X", self.apply_reflection_x_operation))
        # Linha 3
        self.transform_controls.append(Button((col1_x, start_y + 2*(btn_height+gap), btn_width, btn_height),
                                              "Refletir Y", self.apply_reflection_y_operation))
        self.transform_controls.append(Button((col2_x, start_y + 2*(btn_height+gap), btn_width, btn_height),
                                              "Refletir Origem", self.apply_reflection_origin_operation))
        # Linha 4
        self.transform_controls.append(Button((col1_x, start_y + 3*(btn_height+gap), btn_width, btn_height),
                                              "Recorte (CS)", lambda: self.apply_clipping('cs')))
        self.transform_controls.append(Button((col2_x, start_y + 3*(btn_height+gap), btn_width, btn_height),
                                              "Recorte (LB)", lambda: self.apply_clipping('lb')))

    def activate_translate(self):
        if not self.selected_shapes:
            print("Nenhuma forma selecionada para transladar.")
            return
        self.transformation_mode = "transladar"
        print("Modo Transladar ativo. Clique e arraste a forma selecionada.")

    def rotate_selected(self, delta_angle):
        if not self.selected_shapes:
            print("Nenhuma forma selecionada!")
            return
        for shape in self.selected_shapes:
            cx, cy = shape.bounding_box.center
            angle_rad = math.radians(delta_angle)
            new_points = []
            for p in shape.points:
                new_points.append((cx + (p[0]-cx)*math.cos(angle_rad) - (p[1]-cy)*math.sin(angle_rad),
                                   cy + (p[0]-cx)*math.sin(angle_rad) + (p[1]-cy)*math.cos(angle_rad)))
            shape.points = new_points
            shape.bounding_box = shape.calculate_bounding_box()
        print(f"Rotação de {delta_angle}° aplicada.")
        self.save_state()

    def apply_reflection_x_operation(self):
        if not self.selected_shapes:
            print("Nenhuma forma selecionada!")
            return
        for shape in self.selected_shapes:
            cx = shape.bounding_box.centerx
            new_points = [(2*cx - p[0], p[1]) for p in shape.points]
            shape.points = new_points
            shape.bounding_box = shape.calculate_bounding_box()
        print("Reflexão em X aplicada.")
        self.save_state()

    def apply_reflection_y_operation(self):
        if not self.selected_shapes:
            print("Nenhuma forma selecionada!")
            return
        for shape in self.selected_shapes:
            cy = shape.bounding_box.centery
            new_points = [(p[0], 2*cy - p[1]) for p in shape.points]
            shape.points = new_points
            shape.bounding_box = shape.calculate_bounding_box()
        print("Reflexão em Y aplicada.")
        self.save_state()

    def apply_reflection_origin_operation(self):
        center_drawing = self.drawing_area.center
        if not self.selected_shapes:
            print("Nenhuma forma selecionada!")
            return
        for shape in self.selected_shapes:
            new_points = [(2*center_drawing[0] - p[0], 2*center_drawing[1] - p[1]) for p in shape.points]
            shape.points = new_points
            shape.bounding_box = shape.calculate_bounding_box()
        print("Reflexão pela Origem aplicada.")
        self.save_state()

    def toggle_line_algo(self):
        self.line_algo = 'Bresenham' if self.line_algo == 'DDA' else 'DDA'
        self.toggle_line_algo_button.text = f"Linha: {self.line_algo}"
        print("Algoritmo de linha definido para", self.line_algo)

    def increase_brush_size(self):
        self.brush_size = min(20, self.brush_size + 1)
        print("Tamanho do pincel aumentado para", self.brush_size)

    def decrease_brush_size(self):
        self.brush_size = max(1, self.brush_size - 1)
        print("Tamanho do pincel diminuído para", self.brush_size)


# ================== (CTRL Z/ CTRL Y) ==================
    def save_state(self):
        shapes_copy = copy.deepcopy(self.shapes)
        for shape in shapes_copy:
            shape.selected = False
        self.undo_stack.append(shapes_copy)
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(copy.deepcopy(self.shapes))
            self.shapes = self.undo_stack.pop()
            print("Desfazer aplicado.")
        else:
            print("Nenhum desfazer disponível.")

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(copy.deepcopy(self.shapes))
            self.shapes = self.redo_stack.pop()
            print("Refazer aplicado.")
        else:
            print("Nenhum refazer disponível.")



    def is_in_drawing_area(self, pos):
        return self.drawing_area.collidepoint(pos)

    def draw_toolbar(self):
        pygame.draw.rect(self.screen, COLORS['toolbar'], self.toolbar_rect)
        buttons = []
        spacing = 10
        x_offset = 20
        for i, mode in enumerate(self.modes):
            x = x_offset + i * (self.mode_button_width + spacing)
            btn_rect = pygame.Rect(x, 10, self.mode_button_width, 30)
            color = COLORS['active'] if mode == self.current_mode else COLORS['button']
            if btn_rect.collidepoint(pygame.mouse.get_pos()):
                color = COLORS['hover']
            pygame.draw.rect(self.screen, color, btn_rect, border_radius=3)
            texto = self.small_font.render(mode.upper(), True, COLORS['text'])
            self.screen.blit(texto, (btn_rect.x + 5, btn_rect.y + 5))
            buttons.append(btn_rect)

        final_modes_x = x_offset + len(self.modes)*(self.mode_button_width + spacing)
        tamanho_texto = self.small_font.render(f'Tamanho: {self.brush_size}', True, COLORS['text'])
        text_w = tamanho_texto.get_width()
        base_x = final_modes_x + 50
        base_y = 15

        self.screen.blit(tamanho_texto, (base_x, base_y))
        self.size_minus_button.rect.x = base_x + text_w + 20
        self.size_minus_button.rect.y = 10
        self.size_plus_button.rect.x = self.size_minus_button.rect.x + 40
        self.size_plus_button.rect.y = 10

        self.size_minus_button.draw(self.screen)
        self.size_plus_button.draw(self.screen)

        return buttons

    def draw_sidebar(self):
        pygame.draw.rect(self.screen, COLORS['sidebar'], self.sidebar_rect)
        titulo = self.font.render("Instruções", True, COLORS['text'])
        self.screen.blit(titulo, (WIDTH - 280, 20))
        instrucoes = [
            "Modos de desenho:",
            "DESENHO LIVRE: Clique e arraste",
            "LINHA: Dois cliques",
            "CÍRCULO: Centro + raio",
            "POLÍGONO: Clique p/ adicionar pontos",
            "(direito p/ fechar)",
            "SELECIONAR: Clique e arraste p/ selecionar",
            "RECORTE: Clique e arraste p/ definir janela",
            "",
            "Transformações:",
            "Transladar: Arraste a forma",
            "Rotacionar: Rot+1° ou Rot-1°",
            "Refletir: X, Y ou Origem",
            "",
            "Botões Recortar (CS/LB):",
            "Cortam formas fora da janela",
            "",
            "Ctrl+Z: Desfazer / Ctrl+Y: Refazer",
            "",
            "Pressione ESC p/ fechar recorte e desmarcar"
        ]
        y = 60
        for linha in instrucoes:
            txt = self.small_font.render(linha, True, COLORS['text'])
            self.screen.blit(txt, (WIDTH - 280, y))
            y += 20

        for btn in self.transform_controls:
            btn.draw(self.screen)
        self.toggle_line_algo_button.draw(self.screen)

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.clipping_window:
                        self.clipping_window = None
                        print("Janela de recorte fechada.")
                    if self.selected_shapes:
                        for shape in self.selected_shapes:
                            shape.selected = False
                        self.selected_shapes.clear()
                        print("Objetos desmarcados (ESC).")
                mods = pygame.key.get_mods()
                if mods & pygame.KMOD_CTRL:
                    if event.key == pygame.K_z:
                        self.undo()
                    elif event.key == pygame.K_y:
                        self.redo()
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.size_minus_button.is_clicked(event)
                self.size_plus_button.is_clicked(event)
                if mouse_pos[0] > self.sidebar_rect.x:
                    for btn in self.transform_controls:
                        btn.is_clicked(event)
                    self.toggle_line_algo_button.is_clicked(event)
            if event.type == pygame.MOUSEBUTTONDOWN and mouse_pos[1] < 50:
                for i, btn in enumerate(self.draw_toolbar()):
                    if btn.collidepoint(mouse_pos):
                        new_mode = self.modes[i]
                        if self.current_mode == "selecionar" and new_mode != "selecionar":
                            for shape in self.selected_shapes:
                                shape.selected = False
                            self.selected_shapes.clear()
                            print("Objetos desmarcados (modo selecionar).")
                        if self.current_mode == "recorte" and new_mode != "recorte":
                            self.clipping_window = None
                            self.recorte_rect = None
                            print("Janela de recorte removida (mudança de modo).")
                        self.current_mode = new_mode
                        self.temp_points.clear()
                        print("Modo alterado para:", new_mode)
            elif self.is_in_drawing_area(mouse_pos):
                if self.current_mode == 'recorte':
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.recorte_rect = pygame.Rect(mouse_pos, (0, 0))
                        self.dragging = True
                    elif event.type == pygame.MOUSEMOTION and self.dragging:
                        self.recorte_rect.width = mouse_pos[0] - self.recorte_rect.x
                        self.recorte_rect.height = mouse_pos[1] - self.recorte_rect.y
                    elif event.type == pygame.MOUSEBUTTONUP and self.dragging:
                        self.dragging = False
                        self.clipping_window = self.recorte_rect
                        self.recorte_rect = None
                        print("Janela de recorte definida.")
                else:
                    if self.transformation_mode == "transladar":
                        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                            for shape in self.selected_shapes:
                                if shape.bounding_box.collidepoint(mouse_pos):
                                    self.translation_active = True
                                    self.translation_start = mouse_pos
                                    self.translation_orig = {s: copy.deepcopy(s.points) for s in self.selected_shapes}
                                    break
                        elif event.type == pygame.MOUSEMOTION and self.translation_active:
                            dx = mouse_pos[0] - self.translation_start[0]
                            dy = mouse_pos[1] - self.translation_start[1]
                            for s in self.selected_shapes:
                                s.points = [(orig[0] + dx, orig[1] + dy) for orig in self.translation_orig[s]]
                                s.bounding_box = s.calculate_bounding_box()
                        elif event.type == pygame.MOUSEBUTTONUP and self.translation_active:
                            self.translation_active = False
                            self.transformation_mode = None
                            print("Translação aplicada.")
                            self.save_state()
                    else:
                        if self.current_mode == 'selecionar':
                            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                                self.selection_start = mouse_pos
                                self.selection_rect = pygame.Rect(mouse_pos, (0, 0))
                                self.dragging = True
                                for shape in reversed(self.shapes):
                                    if shape.bounding_box.collidepoint(mouse_pos):
                                        shape.selected = not shape.selected
                                        if shape.selected and shape not in self.selected_shapes:
                                            self.selected_shapes.append(shape)
                                        else:
                                            if shape in self.selected_shapes:
                                                self.selected_shapes.remove(shape)
                                        break
                        elif self.current_mode == 'polígono':
                            if event.type == pygame.MOUSEBUTTONDOWN:
                                if event.button == 1:
                                    self.temp_points.append(mouse_pos)
                                elif event.button == 3 and len(self.temp_points) >= 3:
                                    self.shapes.append(Shape('polígono', self.temp_points.copy(), COLORS['draw'], thickness=self.brush_size))
                                    self.save_state()
                                    self.temp_points.clear()
                        elif self.current_mode == 'desenho livre':
                            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                                self.drawing = True
                                self.temp_points.append(mouse_pos)
                        elif self.current_mode in ['linha', 'círculo']:
                            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                                if len(self.temp_points) < 2:
                                    self.temp_points.append(mouse_pos)
            if event.type == pygame.MOUSEBUTTONUP:
                if self.current_mode == 'selecionar' and self.dragging:
                    self.dragging = False
                    self.finalize_selection()
                    self.selection_rect = None
                elif self.current_mode == 'desenho livre' and self.drawing:
                    self.drawing = False
                    if len(self.temp_points) > 1:
                        self.shapes.append(Shape('desenho livre', self.temp_points.copy(), COLORS['draw'], thickness=self.brush_size))
                        self.save_state()
                    self.temp_points.clear()
                elif self.current_mode == 'linha' and len(self.temp_points) == 2:
                    self.shapes.append(Shape('linha', self.temp_points.copy(), COLORS['draw'], thickness=self.brush_size))
                    self.save_state()
                    self.temp_points.clear()
                elif self.current_mode == 'círculo' and len(self.temp_points) == 2:
                    radius = math.hypot(self.temp_points[1][0] - self.temp_points[0][0],
                                        self.temp_points[1][1] - self.temp_points[0][1])
                    self.shapes.append(Shape('círculo', [self.temp_points[0]], COLORS['draw'], radius=int(radius), thickness=self.brush_size))
                    self.save_state()
                    self.temp_points.clear()
            if event.type == pygame.MOUSEMOTION:
                if self.current_mode == 'desenho livre' and self.drawing and self.is_in_drawing_area(mouse_pos):
                    self.temp_points.append(mouse_pos)
                elif self.current_mode == 'selecionar' and self.dragging:
                    self.selection_rect.width = mouse_pos[0] - self.selection_rect.x
                    self.selection_rect.height = mouse_pos[1] - self.selection_rect.y

    def finalize_selection(self):
        for shape in self.shapes:
            if self.selection_rect.colliderect(shape.bounding_box):
                shape.selected = True
                if shape not in self.selected_shapes:
                    self.selected_shapes.append(shape)
            else:
                if shape.selected and not self.selection_rect.colliderect(shape.bounding_box):
                    shape.selected = False
                    if shape in self.selected_shapes:
                        self.selected_shapes.remove(shape)

    def apply_clipping(self, algo):
        if not self.clipping_window:
            print("Nenhuma janela de recorte definida.")
            return
        shapes_to_remove = []
        for shape in self.shapes:
            if shape.type == 'linha':
                if algo == 'cs':
                    clipped = cohen_sutherland_clip(shape.points, self.clipping_window)
                else:
                    clipped = liang_barsky_clip(shape.points, self.clipping_window)
                if clipped:
                    shape.points = clipped
                    shape.bounding_box = shape.calculate_bounding_box()
                else:
                    shapes_to_remove.append(shape)
            elif shape.type == 'polígono':
                clipped = sutherland_hodgman_clip(shape.points, self.clipping_window)
                if clipped and len(clipped) >= 3:
                    shape.points = clipped
                    shape.bounding_box = shape.calculate_bounding_box()
                else:
                    shapes_to_remove.append(shape)
        for s in shapes_to_remove:
            self.shapes.remove(s)
        print("Recorte aplicado usando", "Cohen-Sutherland" if algo == 'cs' else "Liang-Barsky")
        self.save_state()

    def draw_previews(self):
        if self.is_in_drawing_area(pygame.mouse.get_pos()):
            if self.current_mode == 'desenho livre' and len(self.temp_points) > 0:
                if len(self.temp_points) >= 2:
                    for i in range(len(self.temp_points)-1):
                        if self.line_algo == 'DDA':
                            draw_line_dda(self.screen, self.temp_points[i], self.temp_points[i+1], COLORS['draw'], self.brush_size)
                        else:
                            draw_line_bresenham(self.screen, self.temp_points[i], self.temp_points[i+1], COLORS['draw'], self.brush_size)
                last_point = self.temp_points[-1]
                if self.line_algo == 'DDA':
                    draw_line_dda(self.screen, last_point, pygame.mouse.get_pos(), COLORS['draw'], self.brush_size)
                else:
                    draw_line_bresenham(self.screen, last_point, pygame.mouse.get_pos(), COLORS['draw'], self.brush_size)
            elif self.current_mode == 'linha' and len(self.temp_points) == 1:
                if self.line_algo == 'DDA':
                    draw_line_dda(self.screen, self.temp_points[0], pygame.mouse.get_pos(), COLORS['draw'], self.brush_size)
                else:
                    draw_line_bresenham(self.screen, self.temp_points[0], pygame.mouse.get_pos(), COLORS['draw'], self.brush_size)
            elif self.current_mode == 'círculo' and len(self.temp_points) == 1:
                radius = math.hypot(pygame.mouse.get_pos()[0] - self.temp_points[0][0],
                                    pygame.mouse.get_pos()[1] - self.temp_points[0][1])
                draw_circle_bresenham(self.screen, self.temp_points[0], int(radius), COLORS['draw'], self.brush_size)
            elif self.current_mode == 'polígono' and len(self.temp_points) > 0:
                if len(self.temp_points) >= 2:
                    pygame.draw.lines(self.screen, COLORS['draw'], False, self.temp_points, self.brush_size)
                pygame.draw.line(self.screen, COLORS['draw'],
                                 self.temp_points[-1],
                                 pygame.mouse.get_pos(),
                                 self.brush_size)

    def draw(self):
        self.screen.fill(COLORS['background'])
        self.draw_toolbar()
        self.draw_sidebar()

        for shape in self.shapes:
            shape.draw(self.screen, self.line_algo)

        self.draw_previews()

        if self.dragging and self.selection_rect and self.current_mode == 'selecionar':
            surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(surface, (255, 150, 50, 50), self.selection_rect)
            pygame.draw.rect(surface, COLORS['selection'], self.selection_rect, 2)
            self.screen.blit(surface, (0, 0))

        if self.current_mode == 'recorte' and self.recorte_rect:
            surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(surface, (255, 0, 0, 50), self.recorte_rect)
            pygame.draw.rect(surface, COLORS['clip'], self.recorte_rect, 2)
            self.screen.blit(surface, (0, 0))
        elif self.clipping_window:
            if self.clipping_window.width > 0 and self.clipping_window.height > 0:
                clip_surface = pygame.Surface((self.clipping_window.width, self.clipping_window.height), pygame.SRCALPHA)
                clip_surface.fill((255, 0, 0, 50))
                self.screen.blit(clip_surface, (self.clipping_window.x, self.clipping_window.y))
                pygame.draw.rect(self.screen, COLORS['clip'], self.clipping_window, 2)

        pygame.display.flip()
        self.clock.tick(60)

    def run(self):
        while True:
            self.handle_events()
            self.draw()

if __name__ == "__main__":
    editor = GraphicsEditor()
    editor.run()
