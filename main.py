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
            x_values = [p[0] for p in self.points]
            y_values = [p[1] for p in self.points]
            return pygame.Rect(min(x_values), min(y_values),
                               max(x_values)-min(x_values), max(y_values)-min(y_values))
        elif self.type == 'circle':
            return pygame.Rect(self.points[0][0]-self.radius, self.points[0][1]-self.radius,
                               self.radius*2, self.radius*2)
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
            "[Q/E] Rotacionar",
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
                                    self.selected_shapes.remove(shape)
                                break
                    else:
                        if self.current_mode == 'freehand':
                            self.drawing = True
                            self.temp_points.append(mouse_pos)

                        elif self.current_mode == 'line':
                            if len(self.temp_points) < 2:
                                self.temp_points.append(mouse_pos)

                        elif self.current_mode == 'circle':
                            if len(self.temp_points) < 2:
                                self.temp_points.append(mouse_pos)

                        elif self.current_mode == 'clip':
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
                elif event.key == pygame.K_r:
                    self.selected_shapes.clear()
                    for shape in self.shapes:
                        shape.selected = False
                elif self.current_mode == 'transform' and self.selected_shapes:
                    if event.key == pygame.K_w:
                        self.transform_selected(0, -5)
                    elif event.key == pygame.K_s:
                        self.transform_selected(0, 5)
                    elif event.key == pygame.K_a:
                        self.transform_selected(-5, 0)
                    elif event.key == pygame.K_d:
                        self.transform_selected(5, 0)
                    elif event.key == pygame.K_q:
                        self.transform_selected(rotate=-5)
                    elif event.key == pygame.K_e:
                        self.transform_selected(rotate=5)
                    elif event.key == pygame.K_z:
                        self.transform_selected(scale=1.1)
                    elif event.key == pygame.K_x:
                        self.transform_selected(scale=0.9)

    def finalize_selection(self):
        for shape in self.shapes:
            if self.selection_rect.colliderect(shape.bounding_box):
                shape.selected = True
                if shape not in self.selected_shapes:
                    self.selected_shapes.append(shape)

    def transform_selected(self, dx=0, dy=0, rotate=0, scale=1):
        for shape in self.selected_shapes:
            # Translação
            if dx != 0 or dy != 0:
                shape.points = [(p[0] + dx, p[1] + dy) for p in shape.points]
            
            # Rotação
            if rotate != 0:
                angle = math.radians(rotate)
                cx, cy = shape.points[0]
                new_points = []
                for x, y in shape.points:
                    x -= cx
                    y -= cy
                    new_x = x * math.cos(angle) - y * math.sin(angle)
                    new_y = x * math.sin(angle) + y * math.cos(angle)
                    new_points.append((new_x + cx, new_y + cy))
                shape.points = new_points
            
            # Escala
            if scale != 1:
                cx, cy = shape.points[0]
                shape.points = [(cx + (x - cx) * scale, cy + (y - cy) * scale) for x, y in shape.points]
            
            shape.bounding_box = shape.calculate_bounding_box()

    def draw(self):
        self.screen.fill(COLORS['background'])
        self.buttons = self.draw_toolbar()
        self.draw_sidebar()

        # Desenhar formas
        for shape in self.shapes:
            shape.draw(self.screen)

        # Desenhar previews
        if self.is_in_drawing_area(pygame.mouse.get_pos()):
            if self.current_mode == 'line' and len(self.temp_points) == 1:
                pygame.draw.line(self.screen, COLORS['draw'], 
                               self.temp_points[0], pygame.mouse.get_pos(), 
                               self.brush_size)

            elif self.current_mode == 'circle' and len(self.temp_points) == 1:
                radius = math.hypot(pygame.mouse.get_pos()[0] - self.temp_points[0][0],
                                  pygame.mouse.get_pos()[1] - self.temp_points[0][1])
                pygame.draw.circle(self.screen, COLORS['draw'], 
                                 self.temp_points[0], int(radius), self.brush_size)

            elif self.current_mode == 'freehand' and len(self.temp_points) > 1:
                pygame.draw.lines(self.screen, COLORS['draw'], 
                                False, self.temp_points, self.brush_size)

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

    # Método run que estava faltando
    def run(self):
        while True:
            self.handle_events()
            self.draw()

if __name__ == "__main__":
    editor = GraphicsEditor()
    editor.run()