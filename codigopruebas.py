import os
import pygame
import subprocess
import time
import shutil
from threading import Thread
import sys
import pyudev  # Nuevo import para manejo de eventos USB

# Configuración de rutas
ROM_DIR = "/home/ccjpmmGaming/Retroconsole/roms"
SPLASH_IMAGE = "/home/ccjpmmGaming/Retroconsole/splash/logo.png"
SPLASH_SOUND = "/home/ccjpmmGaming/Retroconsole/splash/sound.wav"
EMULATOR_CMD = "/usr/games/mednafen"

# Paleta de colores
COLOR_BG = (21, 67, 96)          # Fondo
COLOR_TEXT = (255, 255, 255)     # Texto blanco
COLOR_SELECTED = (20, 143, 119)  # Para selección
COLOR_TITLE = (255, 255, 255)    # Blanco para títulos
COLOR_HIGHLIGHT = (72, 201, 176) # Para destacar
COLOR_DISCONNECTED = (146, 43, 33) # Rojo brillante para mensajes de error
COLOR_KEY = (50, 50, 50)         # Color de las teclas
COLOR_KEY_PRESSED = (100, 100, 100) # Color de tecla presionada
COLOR_SEARCH_BG = (30, 80, 110)  # Fondo del área de búsqueda
COLOR_SEARCH_HIGHLIGHT = (100, 150, 200) # Color para tecla seleccionada

# Nuevas rutas para imágenes por consola
MAPPING_CONTROL_IMAGES = {
    '.gba': "/home/ccjpmmGaming/Retroconsole/splash/gba_controls.png",
    '.nes': "/home/ccjpmmGaming/Retroconsole/splash/nes_controls.png", 
    '.smc': "/home/ccjpmmGaming/Retroconsole/splash/snes_controls.png",
    '.sfc': "/home/ccjpmmGaming/Retroconsole/splash/snes_controls.png"
}

# Configuración adicional para USB
USB_MOUNT_DIR = "/home/ccjpmmGaming/usb"
USB_ROM_DIRS = {
    '.gba': '/home/ccjpmmGaming/Retroconsole/roms/GBA',
    '.nes': '/home/ccjpmmGaming/Retroconsole/roms/NES',
    '.smc': '/home/ccjpmmGaming/Retroconsole/roms/SNES',
    '.sfc': '/home/ccjpmmGaming/Retroconsole/roms/SNES'
}

#Variables globales
EMULATOR_RUNNING = False
EMULATOR_PROCESS = None

class GameState:
    def __init__(self):
        self.current_path = ROM_DIR
        self.selected = 0
        self.path_stack = [ROM_DIR]
        self.joystick = None
        self.selection_history = {}
        self.search_active = False
        self.search_text = ""
        self.search_results = []
        self.search_selected = 0
        self.keyboard_selected = 0
        self.last_input_time = time.time()
        self.keyboard_layout = [
            ['Q','W','E','R','T','Y','U','I','O','P'],
            ['A','S','D','F','G','H','J','K','L'],
            ['Z','X','C','V','B','N','M',"."],
            ['SPACE','DEL']
        ]
        self.input_delay = 0.1
        self.repeat_delay = 0.3
        self.repeat_rate = 0.1
        # Nuevas variables para notificación de copia
        self.copied_files = {}
        self.show_copy_notification = False

# ==============================================
# Funciones relacionadas con USB
# ==============================================

def check_and_mount_usb():
    """Verifica y monta una memoria USB si está conectada"""
    try:
        # Verificar si ya está montada
        if os.path.ismount(USB_MOUNT_DIR):
            return True
            
        # Crear directorio de montaje si no existe
        if not os.path.exists(USB_MOUNT_DIR):
            os.makedirs(USB_MOUNT_DIR)
            
        # Buscar dispositivos USB (generalmente /dev/sda1 o /dev/sdb1)
        for device in ['/dev/sda1', '/dev/sdb1', '/dev/sdc1']:
            if os.path.exists(device):
                # Montar el dispositivo
                subprocess.run(['sudo', 'mount', device, USB_MOUNT_DIR], check=True)
                print(f"Dispositivo USB montado en {USB_MOUNT_DIR}")
                return True
                
    except Exception as e:
        print(f"Error al montar USB: {e}")
    return False

def unmount_usb():
    """Desmonta la memoria USB"""
    try:
        if os.path.ismount(USB_MOUNT_DIR):
            subprocess.run(['sudo', 'umount', USB_MOUNT_DIR], check=True)
            print("Dispositivo USB desmontado")
    except Exception as e:
        print(f"Error al desmontar USB: {e}")

def copy_roms_from_usb():
    """Copia las ROMs desde la USB a los directorios correspondientes"""
    copied_files = {ext: [] for ext in USB_ROM_DIRS.keys()}
    found_roms = False  # Bandera para saber si se encontraron ROMs
    
    if not os.path.isdir(USB_MOUNT_DIR):
        return copied_files, False
        
    try:
        # Recorrer archivos en la raíz de la USB
        for filename in os.listdir(USB_MOUNT_DIR):
            filepath = os.path.join(USB_MOUNT_DIR, filename)
            
            # Verificar si es un archivo ROM
            for ext in USB_ROM_DIRS.keys():
                if filename.lower().endswith(ext):
                    found_roms = True  # Se encontró al menos una ROM
                    dest_dir = USB_ROM_DIRS[ext]
                    
                    # Crear directorio destino si no existe
                    if not os.path.exists(dest_dir):
                        os.makedirs(dest_dir)
                    
                    dest_path = os.path.join(dest_dir, filename)
                    
                    # Verificar si el archivo ya existe y si es diferente
                    should_copy = False
                    if not os.path.exists(dest_path):
                        should_copy = True
                    else:
                        # Comparar fechas de modificación
                        src_mtime = os.path.getmtime(filepath)
                        dst_mtime = os.path.getmtime(dest_path)
                        if src_mtime > dst_mtime:
                            should_copy = True
                    
                    # Copiar el archivo solo si es necesario
                    if should_copy:
                        shutil.copy2(filepath, dest_path)
                        copied_files[ext].append(filename)
                        print(f"Copiada {filename} a {dest_dir}")
                    break
                    
    except Exception as e:
        print(f"Error al copiar ROMs: {e}")
        
    return copied_files, found_roms

def setup_usb_monitor():
    """Configura el monitor de eventos USB"""
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem='block', device_type='disk')
    return monitor

def check_existing_usb():
    """Verifica si ya hay un USB conectado al iniciar"""
    try:
        return check_and_mount_usb()
    except Exception as e:
        print(f"Error al verificar USB existente: {e}")
        return False

def usb_event_handler(game_state):
    """Maneja eventos de conexión/desconexión de USB"""
    global EMULATOR_RUNNING, EMULATOR_PROCESS
    monitor = setup_usb_monitor()
    
    # Verificar si ya hay un USB conectado al iniciar
    if check_existing_usb():
        copied_files, found_roms = copy_roms_from_usb()
        # Detener emulación si está corriendo
        if EMULATOR_RUNNING and EMULATOR_PROCESS:
            EMULATOR_PROCESS.terminate()
            EMULATOR_PROCESS.wait()
            EMULATOR_RUNNING = False
            
        # Notificar al hilo principal independientemente de si hay ROMs o no
        game_state.copied_files = copied_files
        game_state.show_copy_notification = True
        unmount_usb()
    
    # Monitorear eventos
    for device in iter(monitor.poll, None):
        if device.action == 'add':
            print("Dispositivo USB conectado")
            if check_and_mount_usb():
                copied_files, found_roms = copy_roms_from_usb()
                # Detener emulación si está corriendo
                if EMULATOR_RUNNING and EMULATOR_PROCESS:
                    EMULATOR_PROCESS.terminate()
                    EMULATOR_PROCESS.wait()
                    EMULATOR_RUNNING = False
                
                # Notificar al hilo principal independientemente de si hay ROMs o no
                game_state.copied_files = copied_files
                game_state.show_copy_notification = True
                unmount_usb()
        elif device.action == 'remove':
            print("Dispositivo USB desconectado")

def start_usb_monitor(game_state):
    """Inicia el monitor de USB basado en eventos"""
    try:
        usb_thread = Thread(target=usb_event_handler, args=(game_state,), daemon=True)
        usb_thread.start()
        return usb_thread
    except Exception as e:
        print(f"Error al iniciar monitor USB: {e}")
        return None

def show_copy_confirmation(screen, copied_files):
    """Muestra una pantalla de confirmación de copia de ROMs"""
    font_large = pygame.font.Font(None, 36)
    font_small = pygame.font.Font(None, 28)
    
    total_copied = sum(len(files) for files in copied_files.values())
    
    # Crear una superficie semitransparente
    overlay = pygame.Surface((640, 480), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # Negro semitransparente
    
    # Dibujar el cuadro de diálogo
    dialog_rect = pygame.Rect(70, 120, 500, 240)
    pygame.draw.rect(overlay, COLOR_BG, dialog_rect, border_radius=10)
    pygame.draw.rect(overlay, COLOR_HIGHLIGHT, dialog_rect, 3, border_radius=10)
    
    # Texto del título
    title = font_large.render("Memoria USB detectada.", True, COLOR_HIGHLIGHT)
    overlay.blit(title, (320 - title.get_width()//2, 150))
    
    # Mensaje principal
    if total_copied > 0:
        msg = font_small.render(f"Se copiaron {total_copied} ROMs:", True, COLOR_TEXT)
        overlay.blit(msg, (320 - msg.get_width()//2, 200))
        
        y_pos = 240
        for ext, files in copied_files.items():
            if files:
                ext_text = font_small.render(f"{ext.upper()}: {len(files)}", True, COLOR_TEXT)
                overlay.blit(ext_text, (320 - ext_text.get_width()//2, y_pos))
                y_pos += 30
    else:
        msg_lines = [
            "No se encontraron ROMs nuevas para copiar...",
            "Recuerda que para copiar ROMs estas deben",
            "estar en la raiz de la memoria.",
            "Archivos compatibles: .gba, .nes, .smc, .sfc"
        ]
        y_pos = 200
        for line in msg_lines:
            line_text = font_small.render(line, True, COLOR_TEXT)
            overlay.blit(line_text, (320 - line_text.get_width()//2, y_pos))
            y_pos += 30  # Espacio entre líneas

    
    # Instrucción para continuar (modificada para mencionar solo el botón A)
    instruction = font_small.render("Presiona el botón A para continuar", True, COLOR_HIGHLIGHT)
    overlay.blit(instruction, (320 - instruction.get_width()//2, 320))
    
    # Mostrar el overlay en la pantalla
    screen.blit(overlay, (0, 0))
    pygame.display.update()
    
    # Esperar a que el usuario presione específicamente el botón A
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN and event.button == 0:  # Solo botón A
                waiting = False
        time.sleep(0.1)

# ==============================================
# Funciones relacionadas con el menú principal
# ==============================================

def load_game_cover(game_name):
    """Carga la carátula del juego si existe"""
    # Obtener el nombre del juego sin extensión
    base_name = os.path.splitext(game_name)[0]
    
    # Mapeo de extensiones a carpetas de consola
    console_map = {
        '.gba': 'GBA',
        '.nes': 'NES',
        '.smc': 'SNES',
        '.sfc': 'SNES'
    }
    
    # Determinar la consola basada en la extensión del archivo
    for ext, console in console_map.items():
        if game_name.lower().endswith(ext):
            cover_dir = f"/home/ccjpmmGaming/Retroconsole/covers/{console}"
            break
    else:
        return None  # No es una extensión de juego conocida
    
    # Buscar archivo de carátula (puede tener diferentes extensiones)
    extensions = ['.png', '.jpg', '.jpeg', '.webp']
    for ext in extensions:
        cover_path = os.path.join(cover_dir, f"{base_name}{ext}")
        if os.path.exists(cover_path):
            try:
                # Cargar y devolver la imagen
                image = pygame.image.load(cover_path)
                return image
            except pygame.error as e:
                print(f"No se pudo cargar la carátula {cover_path}: {e}")
                return None
    return None

def load_roms_and_folders(current_path):
    """Carga las ROMs de todas las subcarpetas agrupadas por consola"""
    items = []
    console_map = {
        '.gba': 'GBA',
        '.nes': 'NES', 
        '.smc': 'SNES',
        '.sfc': 'SNES'
    }
    
    # Si estamos en la raíz, mostrar las ROMs agrupadas por consola
    if current_path == ROM_DIR:
        # Buscar ROMs en todas las subcarpetas
        roms_by_console = {}
        for root, dirs, files in os.walk(current_path):
            for file in files:
                for ext, console in console_map.items():
                    if file.lower().endswith(ext):
                        full_path = os.path.join(root, file)
                        if console not in roms_by_console:
                            roms_by_console[console] = []
                        roms_by_console[console].append(('rom', file, full_path))
                        break
        
        # Ordenar las consolas y sus ROMs
        for console in sorted(roms_by_console.keys()):
            # Agregar encabezado de consola
            items.append(('console', console, None))
            # Agregar ROMs de esta consola (ordenadas alfabéticamente)
            for rom in sorted(roms_by_console[console], key=lambda x: x[1]):
                items.append(rom)
    else:
        # Comportamiento normal si no estamos en la raíz
        try:
            for item in sorted(os.listdir(current_path)):
                full_path = os.path.join(current_path, item)
                if os.path.isdir(full_path):
                    items.append(('folder', item, full_path))
                elif os.path.isfile(full_path) and item.lower().endswith((".smc", ".sfc", ".gba", ".nes")):
                    items.append(('rom', item, full_path))
        except Exception as e:
            print(f"Error al cargar contenido de {current_path}: {e}")
            return [], current_path
    
    return items, current_path

def draw_menu(screen, items, selected, current_path, game_state):
    """Dibuja el menú principal con las ROMs agrupadas por consola"""
    # Configuración de fuentes (modificado el tamaño para la lista de ROMs)
    font = pygame.font.Font(None, 28)  # Reducido de 32 a 28 para las ROMs
    title_font = pygame.font.Font(None, 30)
    controls_font = pygame.font.Font(None, 26)
    console_font = pygame.font.Font(None, 28)  # Fuente para los encabezados de consola
    
    # Dibujar fondo
    screen.fill(COLOR_BG)
    
    # Área de título (parte superior)
    title_area = pygame.Rect(0, 0, 640, 60)
    pygame.draw.rect(screen, COLOR_SEARCH_BG, title_area)
    pygame.draw.line(screen, COLOR_HIGHLIGHT, (0, title_area.height), 
                   (640, title_area.height), 2)
    
    # Título con ruta actual
    rel_path = os.path.relpath(current_path, ROM_DIR)
    if rel_path == ".":
        rel_path = "Todas las ROMs"
    title = title_font.render(f"Ubicación: {rel_path}", True, COLOR_HIGHLIGHT)
    screen.blit(title, (320 - title.get_width()//2, 20))
    
    # Área de carátula (parte superior derecha)
    cover_area = pygame.Rect(400, 70, 200, 150)  # x, y, width, height
    
    # Cargar y mostrar carátula si el item seleccionado es una ROM
    if items and selected < len(items):
        item = items[selected]
        if item[0] == 'rom':
            cover_image = load_game_cover(item[1])
            if cover_image:
                # Escalar manteniendo relación de aspecto
                img_width, img_height = cover_image.get_size()
                ratio = min(cover_area.width/img_width, cover_area.height/img_height)
                new_size = (int(img_width * ratio), int(img_height * ratio))
                cover_image = pygame.transform.scale(cover_image, new_size)
                
                # Centrar la imagen en el área
                pos_x = cover_area.x + (cover_area.width - new_size[0]) // 2
                pos_y = cover_area.y + (cover_area.height - new_size[1]) // 2
                screen.blit(cover_image, (pos_x, pos_y))
            else:
                # Mostrar placeholder si no hay carátula
                pygame.draw.rect(screen, (50, 50, 50), cover_area)
                no_cover = font.render("Sin carátula", True, COLOR_TEXT)
                screen.blit(no_cover, (cover_area.centerx - no_cover.get_width()//2, 
                                     cover_area.centery - no_cover.get_height()//2))
                # Dibujar borde
                pygame.draw.rect(screen, COLOR_HIGHLIGHT, cover_area, 2)
    
    # Área de resultados (parte central)
    results_area = pygame.Rect(0, title_area.height, 640, 300)
    
    if not items:
        # Mensaje si no hay items
        no_results = font.render("No hay ROMs en esta carpeta", True, COLOR_TEXT)
        screen.blit(no_results, (320 - no_results.get_width()//2, 150))
    else:
        # Mostrar items agrupados por consola
        y_pos = 80
        start_idx = max(0, selected - 5)
        end_idx = min(len(items), start_idx + 10)
        
        for idx in range(start_idx, end_idx):
            item = items[idx]
            item_type, name, _ = item
            
            # Mostrar item
            color = COLOR_SELECTED if idx == selected else COLOR_TEXT
            prefix = "> " if idx == selected else "  "
            
            if item_type == 'console':
                # Mostrar encabezado de consola
                console_header = console_font.render(f"--- {name} ---", True, COLOR_HIGHLIGHT)
                screen.blit(console_header, (50, y_pos))
                y_pos += 30
            else:
                # Mostrar ROM (con fuente más pequeña)
                text = font.render(f"{prefix}{name}", True, color)
                screen.blit(text, (50, y_pos))
                y_pos += 28  # Espaciado reducido para coincidir con fuente más pequeña
    
    # Área de controles (parte inferior)
    controls_area = pygame.Rect(0, 400, 640, 80)
    pygame.draw.rect(screen, COLOR_SEARCH_BG, controls_area)
    pygame.draw.line(screen, COLOR_HIGHLIGHT, (0, controls_area.y), 
                    (640, controls_area.y), 2)
    
    # Título de controles
    controls_title = controls_font.render("Controles del Menú", True, COLOR_HIGHLIGHT)
    screen.blit(controls_title, (320 - controls_title.get_width()//2, controls_area.y + 10))
    
    # Organización de controles en dos filas
    a_text = controls_font.render("A : Seleccionar", True, COLOR_TEXT)
    b_text = controls_font.render("B : Atrás", True, COLOR_TEXT)
    nav_text = controls_font.render("↑/↓ : Navegar", True, COLOR_TEXT)
    search_text = controls_font.render("← : Buscar", True, COLOR_TEXT)
    shutdown_text = controls_font.render("SELECT+START : Apagar", True, (255, 100, 100))

    # Primera fila de controles
    screen.blit(a_text, (75, controls_area.y + 30))
    screen.blit(b_text, (225, controls_area.y + 30))
    screen.blit(nav_text, (325, controls_area.y + 30))
    screen.blit(search_text, (475, controls_area.y + 30))
    
    # Segunda fila (solo botón de apagado centrado)
    screen.blit(shutdown_text, (320 - shutdown_text.get_width()//2, controls_area.y + 60))
    
    return screen

def folder_menu(joystick, game_state):
    """Menú principal de navegación optimizado"""
    screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    
    # Configuración de tiempos para mejor respuesta
    input_cooldown = 0.1
    repeat_delay = 0.0
    repeat_rate = 0.1
    last_input_time = 0
    last_hat = (0, 0)
    
    # Variable para controlar la recarga de items
    reload_items = True
    
    while True:
        # Verificar si hay que mostrar notificación de copia
        if game_state.show_copy_notification:
            show_copy_confirmation(screen, game_state.copied_files)
            game_state.show_copy_notification = False
            reload_items = True  # Recargar items por si se copiaron nuevas ROMs
            
        if reload_items:
            # Cargar items para la ruta actual
            items, loaded_path = load_roms_and_folders(game_state.current_path)
            
            # Verificar que la ruta cargada coincide con la esperada
            if loaded_path != game_state.current_path:
                print(f"Advertencia: Ruta cargada ({loaded_path}) no coincide con current_path ({game_state.current_path})")
                game_state.current_path = loaded_path
            
            # Restaurar selección guardada para esta ruta
            if game_state.current_path in game_state.selection_history:
                saved_selection = game_state.selection_history[game_state.current_path]
                game_state.selected = saved_selection if saved_selection < len(items) else 0
            else:
                game_state.selected = 0
            
            reload_items = False

        # Mostrar mensaje si no hay items
        if not items:
            font = pygame.font.Font(None, 32)
            screen.fill(COLOR_BG)
            msg = font.render("No hay ROMs en esta carpeta", True, COLOR_TEXT)
            screen.blit(msg, (50, 50))
            back_msg = font.render("Presiona B para volver", True, COLOR_TEXT)
            screen.blit(back_msg, (50, 90))
            pygame.display.update()
            
            # Esperar input para volver
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        if event.button == 1:  # Botón B
                            if len(game_state.path_stack) > 1:
                                game_state.current_path = game_state.path_stack.pop()
                                reload_items = True
                                waiting = False
                            else:
                                return
                        elif event.button == 6 or event.button == 7:  # SELECT o START
                            if joystick.get_button(6) and joystick.get_button(7):
                                shutdown_raspberry()
                time.sleep(0.1)
            continue

        # Dibujar menú
        draw_menu(screen, items, game_state.selected, game_state.current_path, game_state)
        pygame.display.update()
        
        # Procesar eventos
        for event in pygame.event.get():
            if event.type == pygame.JOYHATMOTION:
                # Manejar movimiento del joystick
                hat = event.value
                current_time = time.time()
                
                if hat != (0, 0):
                    if hat != last_hat or current_time - last_input_time > repeat_delay:
                        if hat[1] == 1:  # Arriba
                            game_state.selected = max(0, game_state.selected - 1)
                        elif hat[1] == -1:  # Abajo
                            game_state.selected = min(len(items) - 1, game_state.selected + 1)
                        elif hat[0] == -1:  # Izquierda (buscar)
                            game_state.search_active = True
                            game_state.search_text = ""
                            game_state.search_results = []
                            handle_search_menu(game_state.joystick, game_state)
                            screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
                            pygame.mouse.set_visible(False)
                            reload_items = True
                        
                        last_input_time = current_time
                        last_hat = hat
            
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:  # Botón A
                    item = items[game_state.selected]
                    game_state.selection_history[game_state.current_path] = game_state.selected
                    
                    if item[0] == 'folder':
                        game_state.path_stack.append(game_state.current_path)
                        game_state.current_path = item[2]
                        reload_items = True
                    elif item[0] == 'rom':
                        launch_game(item[2], joystick)
                        screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
                        pygame.mouse.set_visible(False)
                
                elif event.button == 1:  # Botón B
                    if len(game_state.path_stack) > 1:
                        game_state.selection_history[game_state.current_path] = game_state.selected
                        game_state.current_path = game_state.path_stack.pop()
                        reload_items = True
                
                elif event.button == 6 or event.button == 7:  # SELECT o START
                    if joystick.get_button(6) and joystick.get_button(7):
                        shutdown_raspberry()
        
        # Verificar conexión del control
        if pygame.joystick.get_count() == 0:
            print("Control desconectado, esperando reconexión...")
            joystick = show_connect_controller(require_button_press=False)
            if joystick:
                print("Control reconectado, continuando...")
                reload_items = True
        
        # Pequeña pausa para evitar uso excesivo de CPU
        time.sleep(0.01)

# ==============================================
# Funciones relacionadas con el menú de búsqueda
# ==============================================

def search_roms(search_text, root_dir):
    """Busca ROMs en todas las subcarpetas y las clasifica por consola"""
    results = []
    search_lower = search_text.lower()
    
    # Mapeo de extensiones a nombres de consola
    console_map = {
        '.gba': 'GBA',
        '.nes': 'NES',
        '.smc': 'SNES',
        '.sfc': 'SNES'
    }
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            file_lower = file.lower()
            # Buscar la extensión que coincida
            for ext in console_map.keys():
                if file_lower.endswith(ext) and search_lower in file_lower:
                    console = console_map[ext]
                    results.append(('rom', file, os.path.join(root, file), console))
                    break
    
    # Ordenar primero por consola, luego por nombre de archivo
    results.sort(key=lambda x: (x[3], x[1]))
    return results

def draw_search_results(screen, game_state):
    """Dibuja los resultados de búsqueda clasificados por consola"""
    # Pre-renderizar fuentes
    font = pygame.font.Font(None, 32)
    title_font = pygame.font.Font(None, 30)
    controls_font = pygame.font.Font(None, 26)
    console_font = pygame.font.Font(None, 28)
    
    # Dibujar fondo
    screen.fill(COLOR_BG)
    
    # Área de título (parte superior)
    title_area = pygame.Rect(0, 0, 640, 60)
    pygame.draw.rect(screen, COLOR_SEARCH_BG, title_area)
    pygame.draw.line(screen, COLOR_HIGHLIGHT, (0, title_area.height), 
                    (640, title_area.height), 2)
    
    # Título de búsqueda
    title = title_font.render(f"Resultados para: '{game_state.search_text}'", True, COLOR_HIGHLIGHT)
    screen.blit(title, (320 - title.get_width()//2, 20))
    
    # Área de resultados (parte central)
    results_area = pygame.Rect(0, title_area.height, 640, 300)
    
    if not game_state.search_results:
        # Mensaje de no resultados
        no_results = font.render("No se encontraron ROMs", True, COLOR_TEXT)
        screen.blit(no_results, (320 - no_results.get_width()//2, 150))
        
        instruction = controls_font.render("Presiona A para regresar al menu principal", True, COLOR_HIGHLIGHT)
        screen.blit(instruction, (320 - instruction.get_width()//2, 200))
    else:
        # Mostrar resultados agrupados por consola
        y_pos = 80
        current_console = None
        start_idx = max(0, game_state.search_selected - 5)
        end_idx = min(len(game_state.search_results), start_idx + 10)
        
        for idx in range(start_idx, end_idx):
            item = game_state.search_results[idx]
            _, name, _, console = item
            
            # Mostrar encabezado de consola si cambió
            if console != current_console:
                current_console = console
                console_header = console_font.render(f"--- {console} ---", True, COLOR_HIGHLIGHT)
                screen.blit(console_header, (50, y_pos))
                y_pos += 30
            
            # Mostrar item
            color = COLOR_SELECTED if idx == game_state.search_selected else COLOR_TEXT
            text = font.render(f"  {name}", True, color)
            screen.blit(text, (50, y_pos))
            y_pos += 30
    
    # Área de controles con botón de apagado
    controls_area = pygame.Rect(0, 400, 640, 80)
    pygame.draw.rect(screen, COLOR_SEARCH_BG, controls_area)
    pygame.draw.line(screen, COLOR_HIGHLIGHT, (0, controls_area.y), 
                    (640, controls_area.y), 2)
    
    # Controles disponibles (solo mostrar los relevantes)
    if game_state.search_results:
        # Título de controles
        controls_title = controls_font.render("Controles de Búsqueda", True, COLOR_HIGHLIGHT)
        screen.blit(controls_title, (320 - controls_title.get_width()//2, controls_area.y + 10))
        
        # Organización de controles en dos filas si es necesario
        a_text = controls_font.render("A : Seleccionar", True, COLOR_TEXT)
        b_text = controls_font.render("B : Menú principal", True, COLOR_TEXT)
        nav_text = controls_font.render("↑/↓ : Navegar", True, COLOR_TEXT)
        shutdown_text = controls_font.render("SELECT+START : Apagar", True, (255, 100, 100))  # Rojo para destacar

        # Primera fila de controles
        screen.blit(a_text, (100, controls_area.y + 30))
        screen.blit(b_text, (250, controls_area.y + 30))
        screen.blit(nav_text, (420, controls_area.y + 30))
        
        # Segunda fila (solo botón de apagado centrado)
        screen.blit(shutdown_text, (320 - shutdown_text.get_width()//2, controls_area.y + 60))
        
    pygame.display.update()

def show_search_keyboard(screen, game_state):
    """Muestra el teclado virtual optimizado"""
    # Pre-renderizar fuentes
    font = pygame.font.Font(None, 28)
    small_font = pygame.font.Font(None, 22)
    title_font = pygame.font.Font(None, 30)
    warning_font = pygame.font.Font(None, 24)  # Fuente para el mensaje
    
    # Dibujar fondo
    screen.fill(COLOR_BG)
    
    # Dibujar mensaje amarillo (sin recuadro)
    line1 = warning_font.render("Importante. Si no se detecta la pulsación de las flechas para moverse", True, (255, 255, 0))  # Texto amarillo
    line2 = warning_font.render("por el teclado, por favor desconecta y conecta el control.", True, (255, 255, 0))  # Texto amarillo
    
    screen.blit(line1, (320 - line1.get_width() // 2, 10))
    screen.blit(line2, (320 - line2.get_width() // 2, 35))
    
    # Dibujar título
    title = title_font.render("BUSCAR ROMS", True, COLOR_HIGHLIGHT)
    screen.blit(title, (320 - title.get_width() // 2, 70))
    
    # Dibujar área de búsqueda
    search_rect = pygame.Rect(40, 110, 560, 50)
    pygame.draw.rect(screen, COLOR_SEARCH_BG, search_rect, border_radius=5)
    pygame.draw.rect(screen, COLOR_HIGHLIGHT, search_rect, 2, border_radius=5)
    
    # Texto de búsqueda
    display_text = game_state.search_text[-20:] if len(game_state.search_text) > 20 else game_state.search_text
    text_surface = font.render(display_text + "|", True, COLOR_TEXT)
    screen.blit(text_surface, (search_rect.x + 10, search_rect.y + 10))
    
    # Teclado modificado
    game_state.keyboard_layout = [
        ['Q','W','E','R','T','Y','U','I','O','P'],
        ['A','S','D','F','G','H','J','K','L'],
        ['Z','X','C','V','B','N','M',"."],
        ['SPACE','DEL']
    ]
    
    # Dibujar teclado
    key_width = 34
    key_height = 34
    key_margin = 6
    start_y = 180
    
    for row_idx, row in enumerate(game_state.keyboard_layout):
        row_width = sum(
            (key_width * (5 if key in ['SPACE'] else 3 if key in ['DEL'] else 1) + 
             key_margin * (4 if key in ['SPACE'] else 2 if key in ['DEL'] else 0))
            for key in row
        ) - key_margin
        
        start_x = (640 - row_width) // 2
        
        for col_idx, key in enumerate(row):
            if key == 'SPACE':
                key_rect = pygame.Rect(start_x, start_y + row_idx * (key_height + key_margin), 
                                     key_width * 5 + key_margin * 4, key_height)
                start_x += key_width * 5 + key_margin * 5
            elif key == 'DEL':
                key_rect = pygame.Rect(start_x, start_y + row_idx * (key_height + key_margin), 
                                     key_width * 3 + key_margin * 2, key_height)
                start_x += key_width * 3 + key_margin * 3
            else:
                key_rect = pygame.Rect(start_x, start_y + row_idx * (key_height + key_margin), 
                                     key_width, key_height)
                start_x += key_width + key_margin
            
            # Dibujar tecla
            is_selected = (row_idx, col_idx) == game_state.keyboard_selected
            key_color = COLOR_SEARCH_HIGHLIGHT if is_selected else COLOR_KEY
            pygame.draw.rect(screen, key_color, key_rect, border_radius=4)
            pygame.draw.rect(screen, COLOR_TEXT, key_rect, 2 if is_selected else 1, border_radius=4)
            
            # Texto de la tecla
            if key == 'SPACE':
                key_text = small_font.render("SPACE", True, COLOR_TEXT)
            elif key == 'DEL':
                key_text = small_font.render("DEL", True, COLOR_TEXT)
            else:
                key_text = font.render(key, True, COLOR_TEXT)
            
            screen.blit(key_text, (key_rect.centerx - key_text.get_width() // 2, 
                                key_rect.centery - key_text.get_height() // 2))
    
    # Instrucciones en dos columnas
    instructions = [
        ("START: Buscar", "B: Cancelar"),
        ("A: Seleccionar tecla", "Y: Espacio"),
        ("X: Borrar", "")  # Última fila con un elemento vacío para mantener el formato
    ]
    
    instruction_y = 380
    for row in instructions:
        # Primera instrucción del par
        if row[0]:  # Solo renderizar si no está vacío
            rendered1 = small_font.render(row[0], True, COLOR_TEXT)
            screen.blit(rendered1, (220 - rendered1.get_width() // 2, instruction_y))
        
        # Segunda instrucción del par
        if row[1]:  # Solo renderizar si no está vacío
            rendered2 = small_font.render(row[1], True, COLOR_TEXT)
            screen.blit(rendered2, (420 - rendered2.get_width() // 2, instruction_y))
        
        instruction_y += 30  # Espacio entre filas
    
    return []

def handle_search_menu(joystick, game_state):
    """Maneja la navegación en el teclado virtual con mejor respuesta a inputs"""
    screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    
    # Configuración de tiempos para mejor respuesta
    game_state.keyboard_selected = (0, 0)
    input_cooldown = 0.1
    last_input_time = 0
    last_hat = (0, 0)
    repeat_delay = 0.3
    repeat_rate = 0.1
    
    while game_state.search_active:
        # Verificar si hay que mostrar notificación de copia
        if game_state.show_copy_notification:
            show_copy_confirmation(screen, game_state.copied_files)
            game_state.show_copy_notification = False
            # Volver a dibujar el teclado después de cerrar la notificación
            show_search_keyboard(screen, game_state)
            pygame.display.update()

        # Verificar conexión del control
        if pygame.joystick.get_count() == 0:
            print("Control desconectado en teclado virtual, esperando reconexión...")
            joystick = show_connect_controller(require_button_press=False)
            if joystick:
                print("Control reconectado, continuando en teclado virtual...")
                game_state.joystick = joystick  # Actualiza referencia en game_state
                # No necesitamos recargar items aquí, pero mantenemos el joystick actualizado
                continue

        current_time = time.time()
        key_buttons = show_search_keyboard(screen, game_state)
        
        # Manejar eventos del joystick
        hat = joystick.get_hat(0)
        
        # Manejar movimiento continuo del joystick
        if hat != (0, 0):
            if hat != last_hat:
                last_input_time = current_time
                last_hat = hat
                should_move = True
            else:
                if current_time - last_input_time > repeat_delay:
                    if current_time - last_input_time > repeat_delay + repeat_rate:
                        last_input_time = current_time - repeat_rate
                    should_move = True
                else:
                    should_move = False
        else:
            last_hat = hat
            should_move = False
        
        # Si debemos mover la selección
        if should_move:
            row, col = game_state.keyboard_selected
            
            if hat[0] == 1:  # Derecha
                if col < len(game_state.keyboard_layout[row]) - 1:
                    col += 1
                else:
                    if row < len(game_state.keyboard_layout) - 1:
                        row += 1
                        col = 0
            elif hat[0] == -1:  # Izquierda
                if col > 0:
                    col -= 1
                else:
                    if row > 0:
                        row -= 1
                        col = len(game_state.keyboard_layout[row]) - 1
            elif hat[1] == 1:  # Arriba
                if row > 0:
                    row -= 1
                    col = min(col, len(game_state.keyboard_layout[row]) - 1)
            elif hat[1] == -1:  # Abajo
                if row < len(game_state.keyboard_layout) - 1:
                    row += 1
                    col = min(col, len(game_state.keyboard_layout[row]) - 1)
            
            if (row, col) != game_state.keyboard_selected:
                game_state.keyboard_selected = (row, col)
                last_input_time = current_time
        
        # Procesar botones
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:  # Botón A (seleccionar tecla)
                    row, col = game_state.keyboard_selected
                    key = game_state.keyboard_layout[row][col]
                    
                    if key == 'SPACE':
                        game_state.search_text += ' '
                    elif key == 'DEL':
                        game_state.search_text = game_state.search_text[:-1]
                    else:  # Letra normal o apóstrofe
                        game_state.search_text += key.lower()
                
                elif event.button == 3:  # Botón Y (espacio)
                    game_state.search_text += ' '
                
                elif event.button == 2:  # Botón X (borrar)
                    game_state.search_text = game_state.search_text[:-1]
                
                elif event.button == 1:  # Botón B (cancelar)
                    game_state.search_active = False
                    return
                
                elif event.button == 7:  # Botón START (buscar)
                    if game_state.search_text:
                        game_state.search_results = search_roms(game_state.search_text, ROM_DIR)
                        game_state.search_selected = 0
                        show_search_results_menu(joystick, game_state)
                        screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
                        pygame.mouse.set_visible(False)
        
        pygame.display.update()
        time.sleep(0.01)

def show_search_results_menu(joystick, game_state):
    """Muestra los resultados de búsqueda con mejor respuesta"""
    screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    
    # Configuración de tiempos optimizados
    input_cooldown = 0.1  # 100ms para primera pulsación
    repeat_delay = 0.3    # 300ms antes de repetir
    repeat_rate = 0.1      # 100ms entre repeticiones
    last_input_time = 0
    last_hat = (0, 0)
    
    while game_state.search_active:
        # Verificar si hay que mostrar notificación de copia
        if game_state.show_copy_notification:
            show_copy_confirmation(screen, game_state.copied_files)
            game_state.show_copy_notification = False
            # Volver a dibujar los resultados después de cerrar la notificación
            draw_search_results(screen, game_state)
            pygame.display.update()
            
        # Verificar conexión del control
        if pygame.joystick.get_count() == 0:
            print("Control desconectado en resultados de búsqueda, esperando reconexión...")
            joystick = show_connect_controller(require_button_press=False)
            if joystick:
                print("Control reconectado, continuando en resultados...")
                game_state.joystick = joystick
                # Volver a dibujar la pantalla
                draw_search_results(screen, game_state)
                pygame.display.update()
                continue

        current_time = time.time()
        draw_search_results(screen, game_state)
        
        # Si no hay resultados, esperar solo el botón A para regresar al teclado
        if not game_state.search_results:
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN and event.button == 0:  # Botón A
                    game_state.search_active = False  # Salir completamente del modo búsqueda
                    return
            pygame.display.update()
            time.sleep(0.01)
            continue
        
        # Manejar movimiento del joystick (solo si hay resultados)
        hat = joystick.get_hat(0)
        
        if hat != (0, 0):
            if hat != last_hat:
                # Nueva dirección, reiniciar temporizador
                last_input_time = current_time
                last_hat = hat
                should_move = True
            else:
                # Misma dirección, verificar si es tiempo de repetir
                if current_time - last_input_time > repeat_delay:
                    if current_time - last_input_time > repeat_delay + repeat_rate:
                        last_input_time = current_time - repeat_rate
                    should_move = True
                else:
                    should_move = False
        else:
            last_hat = hat
            should_move = False
        
        # Procesar movimiento
        if should_move:
            if hat[1] == 1:  # Arriba
                game_state.search_selected = max(0, game_state.search_selected - 1)
                last_input_time = current_time
            elif hat[1] == -1:  # Abajo
                game_state.search_selected = min(len(game_state.search_results) - 1, 
                                               game_state.search_selected + 1)
                last_input_time = current_time
        
        # Procesar botones
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:  # Botón A (seleccionar ROM)
                    if game_state.search_results:
                        selected_rom = game_state.search_results[game_state.search_selected]
                        _, ext = os.path.splitext(selected_rom[2])
                        launch_game(selected_rom[2], joystick)
                        screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
                        pygame.mouse.set_visible(False)
                        game_state.search_active = False
                        return
                
                elif event.button == 1:  # Botón B (volver al menú principal)
                    game_state.search_active = False
                    return

                elif event.button == 6 or event.button == 7:  # SELECT o START
                    # Verificar si ambos botones están presionados
                    if joystick.get_button(6) and joystick.get_button(7):
                        shutdown_raspberry()
        
        pygame.display.update()
        time.sleep(0.01)

# ==============================================
# Funciones relacionadas con el emulador
# ==============================================

def launch_game(rom_path, joystick):
    """Lanza el emulador con la ROM seleccionada"""
    global EMULATOR_RUNNING, EMULATOR_PROCESS
    try:
        # Obtener la extensión del archivo
        _, ext = os.path.splitext(rom_path)
        ext = ext.lower()  # Normalizar a minúsculas
        
        # Mostrar pantalla de controles específica antes de iniciar
        if not show_mapping_control_screen(joystick, ext):
            # Si el control se desconectó durante la pantalla de controles
            print("No se lanzó el juego porque el control se desconectó")
            return
            
        pygame.display.quit()
        pygame.display.init()
        pygame.mouse.set_visible(False)
        EMULATOR_PROCESS = subprocess.Popen([EMULATOR_CMD, rom_path])
        EMULATOR_RUNNING = True
        monitor_emulator(EMULATOR_PROCESS, joystick)
    except Exception as e:
        print(f"Error al lanzar el juego: {e}")
    finally:
        EMULATOR_RUNNING = False
        EMULATOR_PROCESS = None

def monitor_emulator(emulator_process, joystick):
    """Monitoriza el emulador durante su ejecución"""
    global EMULATOR_RUNNING
    if not emulator_process:
        return
        
    while EMULATOR_RUNNING and emulator_process.poll() is None:
        # Verificar si el control sigue conectado
        if pygame.joystick.get_count() == 0:
            print("Control desconectado durante el juego")
            emulator_process.terminate()
            emulator_process.wait()
            EMULATOR_RUNNING = False
            return
            
        # Procesar eventos del control
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                if joystick.get_button(6) and joystick.get_button(7):  # SELECT + START
                    emulator_process.terminate()
                    emulator_process.wait()
                    EMULATOR_RUNNING = False
                    return
        time.sleep(0.1)

def show_mapping_control_screen(joystick, rom_extension):
    """Muestra la pantalla de controles específica para la consola hasta que se presione el botón A"""
    pygame.display.init()
    screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    
    try:
        # Obtener la imagen correcta según la extensión
        image_path = MAPPING_CONTROL_IMAGES.get(rom_extension.lower(), "/home/pi/splash/default_controls.png")
        mapping_img = pygame.image.load(image_path)
        
        # Mostrar la imagen
        screen.blit(mapping_img, (0, 0))
        pygame.display.update()
        
        # Esperar a que se presione el botón A o se desconecte el control
        waiting = True
        while waiting:
            # Verificar si el control sigue conectado
            if pygame.joystick.get_count() == 0:
                print("Control desconectado durante pantalla de controles")
                waiting = False
                pygame.display.quit()
                return False  # Indicar que el control se desconectó
            
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN and event.button == 0:  # Botón A
                    waiting = False
            time.sleep(0.1)
            
        return True  # Indicar que todo fue bien
        
    except Exception as e:
        print(f"Error mostrando pantalla de controles: {e}")
        return False
    finally:
        pygame.display.quit()

# ==============================================
# Funciones relacionadas con el control/input
# ==============================================

def show_connect_controller(require_button_press=True):
    """Muestra pantalla de conexión del control con nuevo estilo"""
    pygame.display.init()
    screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    font_large = pygame.font.Font(None, 36)
    font_small = pygame.font.Font(None, 30)
    font_warning = pygame.font.Font(None, 26)  # Fuente un poco más pequeña para el mensaje
    
    pygame.joystick.init()
    joystick_connected = False
    button_pressed = not require_button_press
    
    while True:
        # Fondo semitransparente similar al de copia
        overlay = pygame.Surface((640, 480), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Negro semitransparente
        
        # Dibujar el cuadro de diálogo
        dialog_rect = pygame.Rect(70, 150, 500, 240)  # Movido un poco más abajo para el mensaje
        pygame.draw.rect(overlay, COLOR_BG, dialog_rect, border_radius=10)
        pygame.draw.rect(overlay, COLOR_HIGHLIGHT, dialog_rect, 3, border_radius=10)
        
        # Mostrar advertencia amarilla si se requiere presionar botón
        if require_button_press:
            line1 = font_warning.render(
                "Importante. La salida de audio de la consola",
                True, 
                (255, 255, 0)  # Amarillo
            )
            line2 = font_warning.render(
                "es por medio de la conexión de audífonos", 
                True, 
                (255, 255, 0)  # Amarillo
            )
            
            # Fondo para el mensaje (rectángulo semitransparente)
            warning_bg = pygame.Surface((600, 60), pygame.SRCALPHA)
            warning_bg.fill((20, 20, 0, 200))  # Fondo oscuro semitransparente
            overlay.blit(warning_bg, (20, 40))
            
            # Dibujar las dos líneas centradas
            overlay.blit(line1, (320 - line1.get_width()//2, 50))
            overlay.blit(line2, (320 - line2.get_width()//2, 80))
        
        # Resto del código permanece igual...
        # Actualizar estado de controles
        joystick_count = pygame.joystick.get_count()
        
        if joystick_count > 0:
            if not joystick_connected:
                joystick = pygame.joystick.Joystick(0)
                joystick.init()
                joystick_connected = True
                print(f"Control conectado: {joystick.get_name()}")
                
                if not require_button_press:
                    return joystick
            
            if require_button_press:
                title = font_large.render("Control Conectado", True, COLOR_HIGHLIGHT)
                instruction = font_small.render("Presiona el botón A para continuar", True, COLOR_TEXT)
            else:
                return joystick
        else:
            joystick_connected = False
            title = font_large.render("Control Desconectado", True, COLOR_DISCONNECTED)
            instruction = font_small.render("Conecta un control para continuar", True, COLOR_TEXT)
        
        # Posicionar texto en el overlay (ajustado por el nuevo espacio)
        overlay.blit(title, (320 - title.get_width()//2, 210))  # Ajustada posición Y
        overlay.blit(instruction, (320 - instruction.get_width()//2, 270))  # Ajustada posición Y
        
        # Mostrar el overlay en la pantalla
        screen.fill(COLOR_BG)
        screen.blit(overlay, (0, 0))
        pygame.display.update()
        
        # Procesar eventos
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN and joystick_connected and event.button == 0:
                button_pressed = True
                return pygame.joystick.Joystick(0)
        
        time.sleep(0.1)

def init_inputs():
    """Inicializa el sistema de entrada"""
    pygame.init()
    pygame.joystick.init()
    return show_connect_controller()

# ==============================================
# Funciones relacionadas con el splash screen
# ==============================================

def show_splash():
    """Muestra la pantalla de presentación"""
    pygame.display.init()
    screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    
    try:
        splash = pygame.image.load(SPLASH_IMAGE)
        screen.blit(splash, (0, 0))
        pygame.display.update()
        
        pygame.mixer.init()
        pygame.mixer.music.load(SPLASH_SOUND)
        pygame.mixer.music.play()
        
        time.sleep(8)
    except Exception as e:
        print(f"Error mostrando splash: {e}")
    finally:
        pygame.display.quit()

# ==============================================
# Funciones de sistema de apagado
# ==============================================

def shutdown_raspberry():
    """Apaga la Raspberry Pi de manera segura"""
    try:
        # Mostrar mensaje de apagado
        pygame.display.init()
        screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
        font = pygame.font.Font(None, 36)
        screen.fill((0, 0, 0))
        text = font.render("Apagando el sistema...", True, (255, 255, 255))
        screen.blit(text, (320 - text.get_width()//2, 240 - text.get_height()//2))
        pygame.display.update()
        time.sleep(5)
        pygame.quit()

        # Ejecutar comando de apagado
        os.system('sudo poweroff')
    except Exception as e:
        print(f"Error al intentar apagar: {e}")

# ==============================================
# Función principal
# ==============================================

def main():
    """Función principal"""
    try:
        if not os.path.exists(ROM_DIR):
            os.makedirs(ROM_DIR)
        
        pygame.init()
        pygame.joystick.init()
        
        show_splash()
        
        game_state = GameState()
        usb_thread = start_usb_monitor(game_state)  # Iniciar nuevo monitor USB basado en eventos
        
        while True:
            game_state.joystick = show_connect_controller()
            folder_menu(game_state.joystick, game_state)
              
    except Exception as e:
        print(f"Error en el programa: {e}")
    finally:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()
