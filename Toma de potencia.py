import pygame
import pyaudio
import numpy as np
import sys
import random
import openpyxl  # Biblioteca para crear archivos Excel
from openpyxl import Workbook

pygame.init()

WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Juego de Voz")
clock = pygame.time.Clock()

# Colores
BLUE = (135, 206, 235)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Cargar imagen del pájaro
bird_img = pygame.image.load("codigo/bird.png").convert_alpha()
bird_rect = bird_img.get_rect(center=(WIDTH // 2, HEIGHT - bird_img.get_height() // 2))

# Cargar imagen de la nube
cloud_img = pygame.image.load("codigo/nube.png").convert_alpha()

# Escalar la imagen de la nube si es más grande que la pantalla
cloud_width = cloud_img.get_width()
cloud_height = cloud_img.get_height()

if cloud_width > WIDTH:
    scale_factor = WIDTH / cloud_width
    cloud_width = int(cloud_width * scale_factor)
    cloud_height = int(cloud_height * scale_factor)
    cloud_img = pygame.transform.scale(cloud_img, (cloud_width, cloud_height))

if cloud_height > HEIGHT:
    scale_factor = HEIGHT / cloud_height
    cloud_width = int(cloud_width * scale_factor)
    cloud_height = int(cloud_height * scale_factor)
    cloud_img = pygame.transform.scale(cloud_img, (cloud_width, cloud_height))

# Crear lista de nubes con posiciones aleatorias
clouds = []
for _ in range(5):
    x = random.randint(0, WIDTH - cloud_img.get_width())
    y = random.randint(0, HEIGHT)
    clouds.append([x, y])

cloud_speed_factor = 0.5

# Variables del juego
running = True
game_active = False
gravity = 0.5
bird_movement = 0

# Variables para el contador
time_in_air = 0
bird_in_air = False
font = pygame.font.SysFont(None, 36)

# Variables para la detección de vocales
DETECTION_WINDOW = 5
vowel_history = [False] * DETECTION_WINDOW
energy_history = []

# Variable para controlar el temporizador
timer_active = False  # Se detiene cuando no hay vocales
timer_stopped_at = 0  # Almacena el último valor antes de detener el temporizador

# Configuración de PyAudio
CHUNK = 1024
RATE = 44100
p = pyaudio.PyAudio()

# Función para detectar vocales usando la potencia (energía)
def detect_vowel(stream):
    data = np.frombuffer(stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
    
    # Calcular la energía del audio
    energy = np.linalg.norm(data)
    
    # Imprimir la energía para análisis
    print(f"Energía: {energy}")
    
    # Umbral ajustable de energía
    if energy > 10000:  # Este valor puede necesitar ajuste según tu entorno
        return True, energy
    else:
        return False, 0

# Iniciar flujo de audio
stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)

# Inicializar camera_offset para evitar el NameError
camera_offset = 0

# Función para ingresar datos de usuario
def get_user_input():
    input_active = [False, False, False]  # Tres campos de entrada
    name = ""
    rut = ""
    pathology = ""

    input_boxes = [pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 100, 200, 50),
                   pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 50),
                   pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 50)]
    
    input_text = ["", "", ""]
    input_titles = ["Nombre:", "RUT:", "Patología (sí/no):"]
    active_box = None  # Para rastrear qué cuadro está activo
    
    while True:
        screen.fill(BLUE)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Detectar clic en las cajas de texto
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, box in enumerate(input_boxes):
                    if box.collidepoint(event.pos):
                        active_box = i  # Activa la caja seleccionada
                        input_active = [False] * 3  # Desactiva otras cajas
                        input_active[i] = True

            # Entrada del teclado para el cuadro activo
            if event.type == pygame.KEYDOWN and active_box is not None:
                if event.key == pygame.K_RETURN:
                    if all(input_text):
                        name, rut, pathology = input_text
                        return name, rut, pathology  # Si todo está completo, salir
                elif event.key == pygame.K_BACKSPACE:
                    input_text[active_box] = input_text[active_box][:-1]
                else:
                    input_text[active_box] += event.unicode

        # Dibujar las cajas de texto
        for i, box in enumerate(input_boxes):
            color = WHITE if input_active[i] else BLACK  # Cambia de color si está activa
            pygame.draw.rect(screen, color, box, 2)
            text_surface = font.render(input_text[i], True, BLACK)
            screen.blit(text_surface, (box.x + 5, box.y + 5))

            title_surface = font.render(input_titles[i], True, BLACK)
            screen.blit(title_surface, (box.x - 150, box.y + 5))

        pygame.display.flip()

# Obtener los datos del usuario
user_name, user_rut, user_pathology = get_user_input()

# Función para mostrar la pantalla de inicio
def show_start_screen():
    screen.fill(BLUE)
    font_start = pygame.font.SysFont(None, 48)
    text = font_start.render("¡Bienvenido! Presiona 'Espacio' para comenzar.", True, (0, 0, 0))
    rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, rect)
    pygame.display.flip()

show_start_screen()

# Crear el libro de Excel
wb = Workbook()
ws = wb.active
ws.append(["Nombre", "RUT", "Patología", "Energía"])

# Variable para controlar si los datos del usuario ya se guardaron
user_data_saved = False

# Bucle principal del juego
while running:
    dt = clock.tick(60) / 1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                game_active = True
                bird_rect.center = (WIDTH // 2, HEIGHT - bird_img.get_height() // 2)
                bird_movement = 0
                time_in_air = 0
                bird_in_air = False
                vowel_history = [False] * DETECTION_WINDOW
                energy_history.clear()
                timer_active = False  # Reiniciamos el temporizador cuando se inicia de nuevo
                timer_stopped_at = 0  # Reinicia el temporizador al tocar el suelo

            elif event.key == pygame.K_p:
                running = False

    if game_active:
        vowel_detected, energy = detect_vowel(stream)
        vowel_history.append(vowel_detected)
        vowel_history.pop(0)
        energy_history.append(energy if vowel_detected else 0)

        vowel_average = sum(vowel_history) / DETECTION_WINDOW

        if vowel_average > 0.6:
            bird_movement = -5
            timer_active = True  # Activamos el temporizador si se detecta una vocal
        else:
            bird_movement += gravity
            timer_active = False  # Detenemos el temporizador si no hay vocal

        bird_rect.y += bird_movement

        for cloud in clouds:
            cloud[1] += -bird_movement * cloud_speed_factor

        if bird_rect.top <= 200:
            camera_offset += -bird_movement

        if camera_offset < 0:
            camera_offset = 0

        if bird_rect.bottom < HEIGHT:
            if not bird_in_air:
                bird_in_air = True
                if timer_active:  # Si el micrófono detecta vocal, continuar el temporizador
                    time_in_air += dt
            else:
                if timer_active:  # Si el temporizador está activo, continuar contando
                    time_in_air += dt
        else:
            if bird_in_air:
                bird_in_air = False
                print(f"Tiempo en el aire: {time_in_air:.2f} segundos")
            bird_rect.bottom = HEIGHT
            bird_movement = 0
            camera_offset = 0
            time_in_air = 0  # Reiniciamos el temporizador cuando toca el suelo
            timer_stopped_at = 0

        # Dibujar el fondo
        screen.fill(BLUE)

        for cloud in clouds:
            cloud_draw_y = cloud[1] + camera_offset
            if cloud_draw_y > HEIGHT:
                cloud[1] = -cloud_img.get_height() - camera_offset
                cloud[0] = random.randint(0, WIDTH - cloud_img.get_width())
            elif cloud_draw_y < -cloud_img.get_height():
                cloud[1] = HEIGHT - camera_offset
                cloud[0] = random.randint(0, WIDTH - cloud_img.get_width())
            screen.blit(cloud_img, (cloud[0], cloud_draw_y))

        bird_draw_rect = bird_rect.copy()
        bird_draw_rect.y += camera_offset
        screen.blit(bird_img, bird_draw_rect)

        # Mostrar el temporizador en pantalla
        if timer_active:
            time_text = font.render(f"Tiempo en el aire: {time_in_air:.2f} s", True, (0, 0, 0))
        else:
            time_text = font.render(f"Último tiempo en el aire: {time_in_air:.2f} s", True, (0, 0, 0))
        
        screen.blit(time_text, (10, 10))

        pygame.display.flip()
    else:
        show_start_screen()

# Guardar los datos en Excel al terminar
for energy in energy_history:
    if energy != 0:  # Solo guardamos las energías mayores que 0
        if not user_data_saved:
            # Guardamos los datos del usuario solo una vez
            ws.append([user_name, user_rut, user_pathology, energy])
            user_data_saved = True  # Evita que se guarde de nuevo
        else:
            # Solo se guarda la energía
            ws.append(["", "", "", energy])

# Guardar el archivo con el nombre del usuario
wb.save(f"{user_name}_tes.xlsx")

# Cerrar PyAudio y Pygame
stream.stop_stream()
stream.close()
p.terminate()
pygame.quit()
