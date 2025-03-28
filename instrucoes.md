# Instruções para Rodar e Usar o Editor Gráfico - TP1

## Como Rodar

- **Pré-requisitos:**  
  Certifique-se de ter o Python 3 e a biblioteca [Pygame](https://www.pygame.org/) instalados.

- **Instalação do Pygame:**  
  Caso não tenha o Pygame, instale com o comando:

```cmd
    pip install pygame
```

- **Criando um Ambiente Virtual (Opcional):**  
Abra o terminal e execute:

```cmd
    python -m venv venv 
    venv\Scripts\activate
    pip install -r requirements.txt
```

- **Executando o Programa:**  
No terminal, execute:

```cmd
    python main.py
```

O editor abrirá em uma janela dividida em três áreas:

- **Barra de Ferramentas (Topo)**
- **Área de Desenho (Centro)**
- **Barra Lateral (Direita)**

## Como Usar

### Modos de Desenho

- **DESENHO LIVRE:**  
Clique e arraste na área de desenho para criar traços livres.

- **LINHA:**  
Clique duas vezes para definir os pontos inicial e final de uma linha.

- **CÍRCULO:**  
Clique para definir o centro e, em seguida, clique novamente para definir o raio.

- **POLÍGONO:**  
Clique para adicionar vértices; para finalizar, clique com o botão direito.

- **SELECIONAR:**  
Clique e arraste para selecionar objetos. A seleção é indicada por uma caixa amarela.

- **RECORTE:**  
Clique e arraste para definir uma janela de recorte (aparecerá um retângulo vermelho semi-transparente). Para aplicar o recorte, utilize os botões “Recorte (CS)” ou “Recorte (LB)” na barra lateral.

### Transformações (Barra Lateral)

- **Transladar:**  
Ative o modo “Transladar” e arraste a forma selecionada para movê-la.

- **Rotacionar:**  
Use os botões **Rot+5°** e **Rot-5°** (dispostos lado a lado na primeira linha da área de transformação) para aplicar a rotação imediatamente.

- **Refletir:**  
Utilize os botões “Refletir X”, “Refletir Y” e “Refletir Origem” para espelhar os objetos conforme necessário.

- **Recorte:**  
Os botões “Recorte (CS)” e “Recorte (LB)” aplicam os algoritmos de recorte (Cohen–Sutherland ou Liang–Barsky) para remover partes dos objetos que estão fora da janela definida.

### Ajuste do Tamanho do Pincel

Os botões **+** e **–** na barra de ferramentas ajustam a espessura do traço, ou seja, o “Tamanho” do pincel.

### Atalhos

- **Ctrl+Z:** Desfazer
- **Ctrl+Y:** Refazer
- **ESC:** Fecha a janela de recorte e desmarca os objetos selecionados

## Decisões de Implementação

- **Interface com Pygame:**  
O editor foi desenvolvido utilizando o Pygame, com uma interface dividida em três áreas (barra de ferramentas, área de desenho e barra lateral) para facilitar o uso.

- **Rasterização de Formas:**  
As linhas são desenhadas usando os algoritmos DDA e Bresenham, e os círculos são desenhados com o algoritmo de Bresenham. Essa escolha permite controlar a espessura do traço conforme o valor do pincel.

- **Recorte (Clipping):**  

  - ***Linhas:*** São recortadas utilizando os algoritmos Cohen–Sutherland e Liang–Barsky.  
  - **Polígonos:** São recortados utilizando o algoritmo Sutherland–Hodgman.
  - O recorte só é aplicado a linhas e polígonos.


- **Sistema de Desfazer/Refazer:**  
Os estados do desenho são salvos para ser possível usar ctrl z (undo) e ctrl y (redo)

- **Gerenciamento de Seleção:**  
A seleção de objetos é feita através de uma caixa de seleção que é automaticamente desmarcada ao trocar de modo ou ao pressionar ESC.

