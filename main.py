import pygame
import math

# Inicializa o Pygame
pygame.init()

# Configurações da tela
LARGURA, ALTURA = 800, 600
TAMANHO_PIXEL = 5  
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Computação Gráfica - TP1")

# Cores
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
VERMELHO = (255, 0, 0)
AZUL = (0, 0, 255)

fps = 60
clock = pygame.time.Clock()
WIDTH = 800
HEIGHT = 600







# Algoritmo de Rasterização - DDA
def desenhar_linha_dda(x1, y1, x2, y2, cor=PRETO):
    dx = x2 - x1
    dy = y2 - y1
    passos = max(abs(dx), abs(dy))

    x_inc = dx / passos
    y_inc = dy / passos

    x, y = x1, y1
    for _ in range(passos + 1):
        pygame.draw.rect(tela, cor, (round(x) * TAMANHO_PIXEL, round(y) * TAMANHO_PIXEL, TAMANHO_PIXEL, TAMANHO_PIXEL))
        x += x_inc
        y += y_inc

# Algoritmo de Rasterização - Bresenham
def desenhar_linha_bresenham(x1, y1, x2, y2, cor=PRETO):
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    while True:
        pygame.draw.rect(tela, cor, (x1 * TAMANHO_PIXEL, y1 * TAMANHO_PIXEL, TAMANHO_PIXEL, TAMANHO_PIXEL))
        if x1 == x2 and y1 == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy

# Transformações geométricas
def translacao(pontos, dx, dy):
    return [(x + dx, y + dy) for x, y in pontos]

def escala(pontos, sx, sy):
    return [(round(x * sx), round(y * sy)) for x, y in pontos]

def rotacao(pontos, angulo):
    rad = math.radians(angulo)
    return [
        (round(x * math.cos(rad) - y * math.sin(rad)), 
         round(x * math.sin(rad) + y * math.cos(rad))) 
        for x, y in pontos
    ]

# Captura de cliques para selecionar pontos
def capturar_clique(evento):
    if evento.type == pygame.MOUSEBUTTONDOWN:
        x, y = evento.pos
        x //= TAMANHO_PIXEL
        y //= TAMANHO_PIXEL
        pontos.append((x, y))

font = pygame.font.SysFont(None, 24)

def desenhar_menu():
    pygame.draw.rect(tela, (200, 200, 200), (0, 0, LARGURA, 30))
    texto = font.render("D - DDA | B - Bresenham | T - Translacao | E - Escala | R - Rotacao", True, PRETO)
    tela.blit(texto, (10, 5))

# Loop principal
rodando = True
while rodando:
    tela.fill(BRANCO)  # Limpa a tela
    desenhar_menu()
    desenhar_grade()   # Desenha a grade

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_d:
                modo_desenho = "DDA"
            elif evento.key == pygame.K_b:
                modo_desenho = "Bresenham"
            elif evento.key == pygame.K_t:
                pontos[:] = translacao(pontos, 5, 5)  # Move todos os pontos 5 pixels para a direita e para baixo
            elif evento.key == pygame.K_e:
                pontos[:] = escala(pontos, 1.5, 1.5)  # Aumenta o tamanho dos pontos em 1.5x
            elif evento.key == pygame.K_r:
                pontos[:] = rotacao(pontos, 45)  # Rotaciona os pontos em 45 graus
        capturar_clique(evento)

    # Desenha os pontos clicados
    for x, y in pontos:
        pygame.draw.rect(tela, VERMELHO, (x * TAMANHO_PIXEL, y * TAMANHO_PIXEL, TAMANHO_PIXEL, TAMANHO_PIXEL))

    # Se houver pelo menos dois pontos, desenha uma linha entre os dois primeiros
    if len(pontos) >= 2:
        x1, y1 = pontos[0]
        x2, y2 = pontos[1]

        if modo_desenho == "DDA":
            desenhar_linha_dda(x1, y1, x2, y2, AZUL)
        elif modo_desenho == "Bresenham":
            desenhar_linha_bresenham(x1, y1, x2, y2, AZUL)

    pygame.display.flip()  # Atualiza a tela

# Finaliza o Pygame
pygame.quit()
