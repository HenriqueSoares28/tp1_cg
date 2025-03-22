import pygame
import math
import sys

pygame.init()

# Configurações globais
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

class Shape:
    def __init__(self, shape_type, points, color, **kwargs):
        self.type = shape_type
        self.points = [tuple(p) for p in points]
        self.color = color
        self.radius = kwargs.get('radius', 0)
        self.selected = False
        self.thickness = kwargs.get('thickness', 2)
        self.bounding_box = self.calculate_bounding_box()

    def calculate_bounding_box(self):
        if self.type == 'line':
            x_coords = [p[0] for p in self.points]
            y_coords = [p[1] for p in self.points]
            return pygame.Rect(
                min(x_coords), min(y_coords),
                max(x_coords) - min(x_coords),
                max(y_coords) - min(y_coords)
            )
        elif self.type == 'circle':
            return pygame.Rect(
                self.points[0][0] - self.radius,
                self.points[0][1] - self.radius,
                self.radius * 2,
                self.radius * 2
            )
        return pygame.Rect(0, 0, 0, 0)

    def draw(self, screen):
        if self.type == 'line':
            pygame.draw.line(screen, self.color, self.points[0], self.points[1], self.thickness)
        elif self.type == 'circle':
            pygame.draw.circle(screen, self.color, self.points[0], self.radius, self.thickness)
        
        if self.selected:
            self.draw_selection(screen)

    def draw_selection(self, screen):
        if self.type == 'line':
            pygame.draw.line(screen, COLORS['highlight'], self.points[0], self.points[1], self.thickness + 2)
            pygame.draw.circle(screen, COLORS['selection'], self.points[0], 5)
            pygame.draw.circle(screen, COLORS['selection'], self.points[1], 5)
        elif self.type == 'circle':
            pygame.draw.circle(screen, COLORS['highlight'], self.points[0], self.radius + 2, 2)
            pygame.draw.rect(screen, COLORS['selection'], self.bounding_box.inflate(10, 10), 2)

class GraphicsEditor:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Editor Gráfico - TP1")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 18)
        self.small_font = pygame.font.SysFont('Arial', 14)
        
        self.toolbar_rect = pygame.Rect(0, 0, WIDTH, 50)
        self.sidebar_rect = pygame.Rect(WIDTH - 300, 50, 300, HEIGHT - 50)
        self.drawing_area = pygame.Rect(0, 50, WIDTH - 300, HEIGHT - 50)
        
        self.modes = ['freehand', 'line', 'circle', 'select', 'transform', 'clip', 'brush']
        self.current_mode = 'line'
        self.shapes = []
        self.selected_shapes = []
        self.temp_points = []
        self.dragging = False
        self.selection_rect = None
        self.clipping_window = None
        self.brush_size = 2
        self.drawing = False
        self.selection_start = None

    def is_in_drawing_area(self, pos):
        return self.drawing_area.collidepoint(pos)

    def draw_toolbar(self):
        pygame.draw.rect(self.screen, COLORS['toolbar'], self.toolbar_rect)
        buttons = []
        for i, mode in enumerate(self.modes):
            x = 20 + i*120
            btn_rect = pygame.Rect(x, 10, 110, 30)
            color = COLORS['active'] if mode == self.current_mode else COLORS['button']
            if btn_rect.collidepoint(pygame.mouse.get_pos()):
                color = COLORS['hover']
            pygame.draw.rect(self.screen, color, btn_rect, border_radius=3)
            text = self.small_font.render(mode.upper(), True, COLORS['text'])
            self.screen.blit(text, (x + 5, 15))
            buttons.append(btn_rect)
        
        text = self.small_font.render(f'Tamanho: {self.brush_size}', True, COLORS['text'])
        self.screen.blit(text, (WIDTH - 400, 15))
        return buttons

    def draw_sidebar(self):
        pygame.draw.rect(self.screen, COLORS['sidebar'], self.sidebar_rect)
        title = self.font.render("Instruções", True, COLORS['text'])
        self.screen.blit(title, (WIDTH - 280, 70))
        
        instructions = [
            "[W/A/S/D] Mover",
            "[Q/E] Rotacionar linhas",
            "[Z/X] Escala",
            "[C] Limpar tela",
            "[R] Remover seleção",
            " ",
            "Modos:",
            "FREEHAND: Clique e arraste",
            "LINE: Dois cliques",
            "CIRCLE: Centro + raio",
            "SELECT: Clique e arraste",
            "TRANSFORM: Transformar seleção",
            "CLIP: Definir área de recorte",
            "BRUSH: Roda do mouse"
        ]
        
        y_pos = 120
        for line in instructions:
            text = self.small_font.render(line, True, COLORS['text'])
            self.screen.blit(text, (WIDTH - 280, y_pos))
            y_pos += 30 if line == " " else 25

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if mouse_pos[1] < 50:
                    for i, btn in enumerate(self.buttons):
                        if btn.collidepoint(mouse_pos):
                            self.current_mode = self.modes[i]
                            self.temp_points.clear()
                            self.selected_shapes.clear()
                elif self.is_in_drawing_area(mouse_pos):
                    if self.current_mode == 'select':
                        self.selection_start = mouse_pos
                        self.selection_rect = pygame.Rect(mouse_pos, (0, 0))
                        self.dragging = True
                        
                        # Seleção por clique único
                        for shape in reversed(self.shapes):
                            if shape.bounding_box.collidepoint(mouse_pos):
                                shape.selected = not shape.selected
                                if shape.selected and shape not in self.selected_shapes:
                                    self.selected_shapes.append(shape)
                                else:
                                    if shape in self.selected_shapes:
                                        self.selected_shapes.remove(shape)
                                break
                    else:
                        if self.current_mode == 'freehand':
                            self.drawing = True
                            self.temp_points.append(mouse_pos)
                        elif self.current_mode in ['line', 'circle', 'clip']:
                            if len(self.temp_points) < 2:
                                self.temp_points.append(mouse_pos)
                        elif self.current_mode == 'brush':
                            if event.button == 4:
                                self.brush_size = min(20, self.brush_size + 1)
                            elif event.button == 5:
                                self.brush_size = max(1, self.brush_size - 1)

            elif event.type == pygame.MOUSEBUTTONUP:
                if self.current_mode == 'select' and self.dragging:
                    self.dragging = False
                    self.finalize_selection()
                    self.selection_rect = None

                elif self.current_mode == 'freehand' and self.drawing:
                    self.drawing = False
                    if len(self.temp_points) > 1:
                        self.shapes.append(Shape('freehand', self.temp_points.copy(), COLORS['draw'], thickness=self.brush_size))
                    self.temp_points.clear()

                elif self.current_mode == 'line' and len(self.temp_points) == 2:
                    self.shapes.append(Shape('line', self.temp_points.copy(), COLORS['draw'], thickness=self.brush_size))
                    self.temp_points.clear()

                elif self.current_mode == 'circle' and len(self.temp_points) == 2:
                    radius = math.hypot(
                        self.temp_points[1][0] - self.temp_points[0][0],
                        self.temp_points[1][1] - self.temp_points[0][1])
                    self.shapes.append(Shape('circle', [self.temp_points[0]], COLORS['draw'], radius=int(radius), thickness=self.brush_size))
                    self.temp_points.clear()

                elif self.current_mode == 'clip' and len(self.temp_points) == 2:
                    self.clipping_window = pygame.Rect(
                        self.temp_points[0],
                        (self.temp_points[1][0] - self.temp_points[0][0],
                         self.temp_points[1][1] - self.temp_points[0][1]))
                    self.temp_points.clear()

            elif event.type == pygame.MOUSEMOTION:
                if self.current_mode == 'freehand' and self.drawing and self.is_in_drawing_area(mouse_pos):
                    self.temp_points.append(mouse_pos)
                elif self.current_mode == 'select' and self.dragging:
                    self.selection_rect.width = mouse_pos[0] - self.selection_rect.x
                    self.selection_rect.height = mouse_pos[1] - self.selection_rect.y

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    self.shapes.clear()
                    self.selected_shapes.clear()
                elif event.key == pygame.K_r:
                    self.selected_shapes.clear()
                    for shape in self.shapes:
                        shape.selected = False
                elif self.current_mode == 'transform':
                    # Debug: log do modo transform
                    print("Modo TRANSFORM ativo. Formas selecionadas: {}".format(len(self.selected_shapes)))
                    step = 5
                    scale_factor = 1.1
                    
                    if event.key == pygame.K_w:
                        print("Tecla W pressionada (translação para cima)")
                        self.transform_selected(dy=-step)
                    elif event.key == pygame.K_s:
                        print("Tecla S pressionada (translação para baixo)")
                        self.transform_selected(dy=step)
                    elif event.key == pygame.K_a:
                        print("Tecla A pressionada (translação para esquerda)")
                        self.transform_selected(dx=-step)
                    elif event.key == pygame.K_d:
                        print("Tecla D pressionada (translação para direita)")
                        self.transform_selected(dx=step)
                    elif event.key == pygame.K_q:
                        print("Tecla Q pressionada (rotação anti-horária)")
                        self.transform_selected(angle=-step)
                    elif event.key == pygame.K_e:
                        print("Tecla E pressionada (rotação horária)")
                        self.transform_selected(angle=step)
                    elif event.key == pygame.K_z:
                        print("Tecla Z pressionada (aumentar escala)")
                        self.transform_selected(scale=scale_factor)
                    elif event.key == pygame.K_x:
                        print("Tecla X pressionada (diminuir escala)")
                        self.transform_selected(scale=1/scale_factor)

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

    def transform_selected(self, dx=0, dy=0, angle=0, scale=1):
        print("Iniciando transform_selected -> dx: {}, dy: {}, angle: {}, scale: {}"
              .format(dx, dy, angle, scale))
        if not self.selected_shapes:
            print("Nenhuma forma selecionada!")
            return
        for shape in self.selected_shapes:
            print(">> Antes -> Tipo: {}, Pontos: {}, Raio: {}".format(shape.type, shape.points, shape.radius))
            
            # Translação
            if dx != 0 or dy != 0:
                print("Aplicando translação: dx={} | dy={}".format(dx, dy))
                if shape.type in ['line', 'freehand']:
                    shape.points = [(p[0] + dx, p[1] + dy) for p in shape.points]
                elif shape.type == 'circle':
                    shape.points[0] = (shape.points[0][0] + dx, shape.points[0][1] + dy)
            
            # Rotação (apenas para linhas)
            if angle != 0:
                if shape.type == 'line':
                    print("Aplicando rotação: angle={} graus".format(angle))
                    cx = (shape.points[0][0] + shape.points[1][0]) / 2
                    cy = (shape.points[0][1] + shape.points[1][1]) / 2
                elif shape.type == 'freehand' and len(shape.points) > 1:
                    # Para freehand, usa-se a média de todos os pontos como centro
                    cx = sum(p[0] for p in shape.points) / len(shape.points)
                    cy = sum(p[1] for p in shape.points) / len(shape.points)
                    print("Aplicando rotação (freehand): angle={} graus | Centro: ({}, {})".format(angle, cx, cy))
                else:
                    cx = cy = 0

                if shape.type in ['line', 'freehand'] and (shape.type == 'line' or len(shape.points) > 1):
                    angle_rad = math.radians(angle)
                    new_points = []
                    for p in shape.points:
                        # ponto relativo ao centro de rotação
                        rel_x = p[0] - cx
                        rel_y = p[1] - cy
                        rot_x = rel_x * math.cos(angle_rad) - rel_y * math.sin(angle_rad)
                        rot_y = rel_x * math.sin(angle_rad) + rel_y * math.cos(angle_rad)
                        new_points.append((rot_x + cx, rot_y + cy))
                    shape.points = new_points
                
            # Escala
            if scale != 1:
                print("Aplicando escala: scale={}".format(scale))
                if shape.type in ['line', 'freehand']:
                    if len(shape.points) >= 2:
                        # Usar o ponto central para escala
                        cx = sum(p[0] for p in shape.points) / len(shape.points)
                        cy = sum(p[1] for p in shape.points) / len(shape.points)
                        new_points = []
                        for p in shape.points:
                            new_points.append((cx + (p[0] - cx) * scale, cy + (p[1] - cy) * scale))
                        shape.points = new_points
                    else:
                        shape.points = [(p[0] * scale, p[1] * scale) for p in shape.points]
                elif shape.type == 'circle':
                    shape.radius = int(shape.radius * scale)
            
            # Atualizar bounding box
            shape.bounding_box = shape.calculate_bounding_box()
            print(">> Depois -> Tipo: {}, Pontos: {}, Raio: {}, Bounding Box: {}"
                  .format(shape.type, shape.points, shape.radius, shape.bounding_box))

    def draw_previews(self):
        if self.is_in_drawing_area(pygame.mouse.get_pos()):
            # Preview do freehand
            if self.current_mode == 'freehand' and len(self.temp_points) > 0:
                pygame.draw.lines(self.screen, COLORS['draw'], False, self.temp_points + [pygame.mouse.get_pos()], self.brush_size)
            
            # Preview da linha
            elif self.current_mode == 'line' and len(self.temp_points) == 1:
                pygame.draw.line(self.screen, COLORS['draw'], 
                               self.temp_points[0], pygame.mouse.get_pos(), 
                               self.brush_size)

            # Preview do círculo
            elif self.current_mode == 'circle' and len(self.temp_points) == 1:
                radius = math.hypot(pygame.mouse.get_pos()[0] - self.temp_points[0][0],
                                  pygame.mouse.get_pos()[1] - self.temp_points[0][1])
                pygame.draw.circle(self.screen, COLORS['draw'], 
                                 self.temp_points[0], int(radius), self.brush_size)

    def draw(self):
        self.screen.fill(COLORS['background'])
        self.buttons = self.draw_toolbar()
        self.draw_sidebar()

        # Desenhar formas
        for shape in self.shapes:
            shape.draw(self.screen)

        # Desenhar previews
        self.draw_previews()

        # Desenhar seleção
        if self.dragging and self.selection_rect:
            surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(surface, (255, 150, 50, 50), self.selection_rect)
            pygame.draw.rect(surface, COLORS['selection'], self.selection_rect, 2)
            self.screen.blit(surface, (0, 0))

        # Janela de recorte
        if self.clipping_window:
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