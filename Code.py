"""
Proyecto final para la materia Sistemas Embebidos impartida en la Facultad de Ingenieria de la UNAM

RetroConsole ccjpmmGaming - Sistema completo de emulación de videojuegos retro

Autores:
- Cortés Hernández José César: Gestión de USB y controles
- Montes Suarez Manuel Alejandro: Ejecución de emulación y pantallas previas
- Peralta Rodriguez Juan Manuel: Menús y sistema de búsqueda

Este sistema permite:
1. Navegar por una colección de ROMs organizadas por consola
2. Copiar ROMs desde memorias USB automáticamente
3. Mostrar información y controles antes de ejecutar juegos
4. Buscar juegos mediante teclado virtual
5. Gestionar controles USB de juego
"""

import os
import pygame
import subprocess
import time
import shutil
from threading import Thread
import sys
import pyudev

# =============================================
# CONFIGURACIÓN GLOBAL
# =============================================
ROM_DIR = "/home/ccjpmmGaming/Retroconsole/roms"
SPLASH_IMAGE = "/home/ccjpmmGaming/Retroconsole/splash/logo.png"
SPLASH_SOUND = "/home/ccjpmmGaming/Retroconsole/splash/sound.wav"
EMULATOR_CMD = "/usr/games/mednafen"

# Paleta de colores para la interfaz
COLOR_BG = (21, 67, 96)            # Color de fondo principal
COLOR_TEXT = (255, 255, 255)       # Texto normal
COLOR_SELECTED = (20, 143, 119)    # Elemento seleccionado
COLOR_TITLE = (255, 255, 255)      # Títulos
COLOR_HIGHLIGHT = (72, 201, 176)   # Destacados
COLOR_DISCONNECTED = (146, 43, 33) # Estado desconectado
COLOR_KEY = (50, 50, 50)           # Teclas no presionadas
COLOR_KEY_PRESSED = (100, 100, 100)# Teclas presionadas
COLOR_SEARCH_BG = (30, 80, 110)    # Fondo de búsqueda
COLOR_SEARCH_HIGHLIGHT = (100, 150, 200) # Resultados destacados

# Mapeo de imágenes de controles por extensión de ROM
MAPPING_CONTROL_IMAGES = {
    '.gba': "/home/ccjpmmGaming/Retroconsole/splash/gba_controls.png",
    '.nes': "/home/ccjpmmGaming/Retroconsole/splash/nes_controls.png", 
    '.smc': "/home/ccjpmmGaming/Retroconsole/splash/snes_controls.png",
    '.sfc': "/home/ccjpmmGaming/Retroconsole/splash/snes_controls.png"
}

# Configuración de directorios USB
USB_MOUNT_DIR = "/home/ccjpmmGaming/usb"
USB_ROM_DIRS = {
    '.gba': '/home/ccjpmmGaming/Retroconsole/roms/GBA',
    '.nes': '/home/ccjpmmGaming/Retroconsole/roms/NES',
    '.smc': '/home/ccjpmmGaming/Retroconsole/roms/SNES',
    '.sfc': '/home/ccjpmmGaming/Retroconsole/roms/SNES'
}

# Estado global del emulador
EMULATOR_RUNNING = False
EMULATOR_PROCESS = None

# =============================================
# CLASE PRINCIPAL DE ESTADO DEL JUEGO
# =============================================
class GameState:
    """
    Mantiene el estado global de la aplicación:
    - Navegación por directorios
    - Historial de selecciones
    - Estado de búsqueda
    - Configuración de teclado virtual
    - Notificaciones de copia de ROMs
    """
    def __init__(self):
        self.current_path = ROM_DIR          # Ruta actual en el navegador
        self.selected = 0                   # Índice del elemento seleccionado
        self.path_stack = [ROM_DIR]          # Pila de navegación (para botón Atrás)
        self.joystick = None                # Referencia al control conectado
        self.selection_history = {}         # Historial de selecciones por ruta
        self.search_active = False          # Estado del modo búsqueda
        self.search_text = ""               # Texto ingresado en búsqueda
        self.search_results = []            # Resultados de búsqueda
        self.search_selected = 0            # Índice seleccionado en resultados
        self.keyboard_selected = 0          # Tecla seleccionada en teclado virtual
        self.last_input_time = time.time()  # Última interacción del usuario
        self.keyboard_layout = [            # Distribución del teclado virtual
            ['Q','W','E','R','T','Y','U','I','O','P'],
            ['A','S','D','F','G','H','J','K','L'],
            ['Z','X','C','V','B','N','M',"."],
            ['SPACE','DEL']
        ]
        self.input_delay = 0.1      # Retardo inicial para repetición de teclas
        self.repeat_delay = 0.3     # Retardo antes de repetir teclas
        self.repeat_rate = 0.1      # Tasa de repetición de teclas
        self.copied_files = {}      # Archivos copiados desde USB
        self.show_copy_notification = False  # Mostrar notificación de copia

# =============================================
# SECCIÓN 1: GESTIÓN DE USB Y CONTROLES
# =============================================

def check_existing_usb():
    """
    Verifica si hay un USB conectado al iniciar el sistema.
    Retorna True si se encuentra y monta correctamente.
    """
    try:
        return check_and_mount_usb()
    except Exception as e:
        print(f"Error al verificar USB existente: {e}")
        return False

def check_and_mount_usb():
    """
    Verifica y monta un dispositivo USB en el directorio especificado.
    Retorna True si se montó correctamente.
    """
    try:
        # Verificar si ya está montado
        if os.path.ismount(USB_MOUNT_DIR):
            return True
            
        # Crear directorio de montaje si no existe
        if not os.path.exists(USB_MOUNT_DIR):
            os.makedirs(USB_MOUNT_DIR)
            
        # Intentar montar dispositivos comunes
        for device in ['/dev/sda1', '/dev/sdb1', '/dev/sdc1']:
            if os.path.exists(device):
                subprocess.run(['sudo', 'mount', device, USB_MOUNT_DIR], check=True)
                print(f"Dispositivo USB montado en {USB_MOUNT_DIR}")
                return True
                
    except Exception as e:
        print(f"Error al montar USB: {e}")
    return False

def unmount_usb():
    """Desmonta el dispositivo USB de forma segura."""
    try:
        if os.path.ismount(USB_MOUNT_DIR):
            subprocess.run(['sudo', 'umount', USB_MOUNT_DIR], check=True)
            print("Dispositivo USB desmontado")
    except Exception as e:
        print(f"Error al desmontar USB: {e}")

def copy_roms_from_usb():
    """
    Copia ROMs desde el USB a los directorios correspondientes según su extensión.
    Retorna un diccionario con los archivos copiados y un booleano si se encontraron ROMs.
    """
    copied_files = {ext: [] for ext in USB_ROM_DIRS.keys()}
    found_roms = False
    
    if not os.path.isdir(USB_MOUNT_DIR):
        return copied_files, False
        
    try:
        # Recorrer archivos en el USB
        for filename in os.listdir(USB_MOUNT_DIR):
            filepath = os.path.join(USB_MOUNT_DIR, filename)
            
            # Verificar extensiones compatibles
            for ext in USB_ROM_DIRS.keys():
                if filename.lower().endswith(ext):
                    found_roms = True
                    dest_dir = USB_ROM_DIRS[ext]
                    
                    # Crear directorio de destino si no existe
                    if not os.path.exists(dest_dir):
                        os.makedirs(dest_dir)
                    
                    dest_path = os.path.join(dest_dir, filename)
                    
                    # Determinar si se debe copiar (nuevo o modificado)
                    should_copy = False
                    if not os.path.exists(dest_path):
                        should_copy = True
                    else:
                        src_mtime = os.path.getmtime(filepath)
                        dst_mtime = os.path.getmtime(dest_path)
                        if src_mtime > dst_mtime:
                            should_copy = True
                    
                    # Copiar archivo si es necesario
                    if should_copy:
                        shutil.copy2(filepath, dest_path)
                        copied_files[ext].append(filename)
                        print(f"Copiada {filename} a {dest_dir}")
                    break
                    
    except Exception as e:
        print(f"Error al copiar ROMs: {e}")
        
    return copied_files, found_roms

def setup_usb_monitor():
    """Configura el monitor de eventos USB usando pyudev."""
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem='block', device_type='disk')
    return monitor

def usb_event_handler(game_state):
    """
    Maneja eventos de conexión/desconexión de USB.
    Se ejecuta en un hilo separado para monitoreo en tiempo real.
    """
    global EMULATOR_RUNNING, EMULATOR_PROCESS
    monitor = setup_usb_monitor()
    
    # Verificar si ya hay un USB conectado al iniciar
    if check_existing_usb():
        copied_files, found_roms = copy_roms_from_usb()
        if EMULATOR_RUNNING and EMULATOR_PROCESS:
            EMULATOR_PROCESS.terminate()
            EMULATOR_PROCESS.wait()
            EMULATOR_RUNNING = False
            
        game_state.copied_files = copied_files
        game_state.show_copy_notification = True
        unmount_usb()
    
    # Monitorear eventos de dispositivos
    for device in iter(monitor.poll, None):
        if device.action == 'add':
            print("Dispositivo USB conectado")
            if check_and_mount_usb():
                copied_files, found_roms = copy_roms_from_usb()
                if EMULATOR_RUNNING and EMULATOR_PROCESS:
                    EMULATOR_PROCESS.terminate()
                    EMULATOR_PROCESS.wait()
                    EMULATOR_RUNNING = False
                
                game_state.copied_files = copied_files
                game_state.show_copy_notification = True
                unmount_usb()
        elif device.action == 'remove':
            print("Dispositivo USB desconectado")

def start_usb_monitor(game_state):
    """
    Inicia el hilo de monitoreo USB.
    Retorna la referencia al hilo o None si falla.
    """
    try:
        usb_thread = Thread(target=usb_event_handler, args=(game_state,), daemon=True)
        usb_thread.start()
        return usb_thread
    except Exception as e:
        print(f"Error al iniciar monitor USB: {e}")
        return None

def show_copy_confirmation(screen, copied_files):
    """
    Muestra una notificación con los archivos copiados desde USB.
    Espera confirmación del usuario para continuar.
    """
    font_large = pygame.font.Font(None, 36)
    font_small = pygame.font.Font(None, 28)
    
    total_copied = sum(len(files) for files in copied_files.values())
    
    # Crear overlay semitransparente
    overlay = pygame.Surface((640, 480), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    
    # Dibujar cuadro de diálogo
    dialog_rect = pygame.Rect(70, 120, 500, 240)
    pygame.draw.rect(overlay, COLOR_BG, dialog_rect, border_radius=10)
    pygame.draw.rect(overlay, COLOR_HIGHLIGHT, dialog_rect, 3, border_radius=10)
    
    # Mostrar título
    title = font_large.render("Memoria USB detectada.", True, COLOR_HIGHLIGHT)
    overlay.blit(title, (320 - title.get_width()//2, 150))
    
    # Mostrar lista de archivos copiados o mensaje si no hay
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
            y_pos += 30

    # Instrucción para continuar
    instruction = font_small.render("Presiona el botón A para continuar", True, COLOR_HIGHLIGHT)
    overlay.blit(instruction, (320 - instruction.get_width()//2, 320))
    
    screen.blit(overlay, (0, 0))
    pygame.display.update()
    
    # Esperar confirmación del usuario
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN and event.button == 0:
                waiting = False
        time.sleep(0.1)

def show_connect_controller(require_button_press=True):
    """
    Muestra pantalla de conexión de control y espera hasta que esté conectado.
    Si require_button_press es True, espera que el usuario presione un botón.
    Retorna el joystick conectado.
    """
    pygame.display.init()
    screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    font_large = pygame.font.Font(None, 36)
    font_small = pygame.font.Font(None, 30)
    font_warning = pygame.font.Font(None, 26)
    
    pygame.joystick.init()
    joystick_connected = False
    button_pressed = not require_button_press
    
    while True:
        # Crear overlay semitransparente
        overlay = pygame.Surface((640, 480), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        
        # Dibujar cuadro de diálogo
        dialog_rect = pygame.Rect(70, 150, 500, 240)
        pygame.draw.rect(overlay, COLOR_BG, dialog_rect, border_radius=10)
        pygame.draw.rect(overlay, COLOR_HIGHLIGHT, dialog_rect, 3, border_radius=10)
        
        # Mostrar advertencia importante si es necesario
        if require_button_press:
            line1 = font_warning.render(
                "Importante. La salida de audio de la consola",
                True, 
                (255, 255, 0))
            line2 = font_warning.render(
                "es por medio de la conexión de audífonos", 
                True, 
                (255, 255, 0))
            
            warning_bg = pygame.Surface((600, 60), pygame.SRCALPHA)
            warning_bg.fill((20, 20, 0, 200))
            overlay.blit(warning_bg, (20, 40))
            
            overlay.blit(line1, (320 - line1.get_width()//2, 50))
            overlay.blit(line2, (320 - line2.get_width()//2, 80))
        
        # Verificar estado del control
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
        
        # Mostrar título e instrucciones
        overlay.blit(title, (320 - title.get_width()//2, 210))
        overlay.blit(instruction, (320 - instruction.get_width()//2, 270))
        
        screen.fill(COLOR_BG)
        screen.blit(overlay, (0, 0))
        pygame.display.update()
        
        # Manejar eventos de botón
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN and joystick_connected and event.button == 0:
                button_pressed = True
                return pygame.joystick.Joystick(0)
        
        time.sleep(0.1)

def init_inputs():
    """Inicializa los sistemas de entrada y muestra pantalla de conexión de control."""
    pygame.init()
    pygame.joystick.init()
    return show_connect_controller()

# =============================================
# SECCIÓN 2: EMULACIÓN Y PANTALLAS PREVIAS
# =============================================

def launch_game(rom_path, joystick):
    """
    Inicia la emulación del juego especificado.
    Muestra pantalla de controles antes de iniciar.
    """
    global EMULATOR_RUNNING, EMULATOR_PROCESS
    try:
        _, ext = os.path.splitext(rom_path)
        ext = ext.lower()
        
        # Mostrar pantalla de controles y verificar conexión
        if not show_mapping_control_screen(joystick, ext):
            print("No se lanzó el juego porque el control se desconectó")
            return
            
        # Configurar pantalla para el emulador
        pygame.display.quit()
        pygame.display.init()
        pygame.mouse.set_visible(False)
        
        # Iniciar emulador
        EMULATOR_PROCESS = subprocess.Popen([EMULATOR_CMD, rom_path])
        EMULATOR_RUNNING = True
        
        # Monitorear estado del emulador
        monitor_emulator(EMULATOR_PROCESS, joystick)
    except Exception as e:
        print(f"Error al lanzar el juego: {e}")
    finally:
        EMULATOR_RUNNING = False
        EMULATOR_PROCESS = None

def monitor_emulator(emulator_process, joystick):
    """
    Monitorea el estado del emulador durante la ejecución.
    Detecta desconexión de controles o comando de apagado.
    """
    global EMULATOR_RUNNING
    if not emulator_process:
        return
        
    while EMULATOR_RUNNING and emulator_process.poll() is None:
        # Verificar conexión del control
        if pygame.joystick.get_count() == 0:
            print("Control desconectado durante el juego")
            emulator_process.terminate()
            emulator_process.wait()
            EMULATOR_RUNNING = False
            return
            
        # Verificar comando de apagado (SELECT+START)
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                if joystick.get_button(6) and joystick.get_button(7):
                    emulator_process.terminate()
                    emulator_process.wait()
                    EMULATOR_RUNNING = False
                    return
        time.sleep(0.1)

def show_mapping_control_screen(joystick, rom_extension):
    """
    Muestra la pantalla con los controles mapeados para el sistema emulado.
    Espera confirmación del usuario antes de continuar.
    Retorna False si el control se desconecta durante la espera.
    """
    pygame.display.init()
    screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    
    try:
        # Cargar imagen de controles según extensión
        image_path = MAPPING_CONTROL_IMAGES.get(rom_extension.lower(), "/home/pi/splash/default_controls.png")
        mapping_img = pygame.image.load(image_path)
        
        screen.blit(mapping_img, (0, 0))
        pygame.display.update()
        
        # Esperar confirmación del usuario
        waiting = True
        while waiting:
            if pygame.joystick.get_count() == 0:
                print("Control desconectado durante pantalla de controles")
                waiting = False
                pygame.display.quit()
                return False
            
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN and event.button == 0:
                    waiting = False
            time.sleep(0.1)
            
        return True
        
    except Exception as e:
        print(f"Error mostrando pantalla de controles: {e}")
        return False
    finally:
        pygame.display.quit()

# =============================================
# SECCIÓN 3: MENÚS Y BÚSQUEDA
# =============================================

def show_splash():
    """
    Muestra la pantalla de inicio con logo y sonido.
    Dura aproximadamente 8 segundos.
    """
    pygame.display.init()
    screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    
    try:
        # Cargar y mostrar imagen de splash
        splash = pygame.image.load(SPLASH_IMAGE)
        screen.blit(splash, (0, 0))
        pygame.display.update()
        
        # Reproducir sonido de inicio
        pygame.mixer.init()
        pygame.mixer.music.load(SPLASH_SOUND)
        pygame.mixer.music.play()
        
        time.sleep(8)
    except Exception as e:
        print(f"Error mostrando splash: {e}")
    finally:
        pygame.display.quit()

def load_game_cover(game_name):
    """
    Carga la imagen de portada para el juego especificado.
    Busca en directorios organizados por consola.
    Retorna la imagen cargada o None si no se encuentra.
    """
    base_name = os.path.splitext(game_name)[0].lower()
    
    # Mapeo de extensiones a consolas
    console_map = {
        '.gba': 'GBA',
        '.nes': 'NES',
        '.smc': 'SNES',
        '.sfc': 'SNES'
    }
    
    # Determinar consola según extensión
    for ext, console in console_map.items():
        if game_name.lower().endswith(ext):
            cover_dir = f"/home/ccjpmmGaming/Retroconsole/covers/{console}"
            break
    else:
        return None
    
    # Extensiones de imagen soportadas
    extensions = ['.png', '.jpg', '.jpeg', '.webp']
    
    try:
        # Buscar archivo de carátula coincidente
        for filename in os.listdir(cover_dir):
            filename_lower = filename.lower()
            
            if base_name in filename_lower:
                for ext in extensions:
                    if filename_lower.endswith(ext):
                        cover_path = os.path.join(cover_dir, filename)
                        try:
                            image = pygame.image.load(cover_path)
                            return image
                        except pygame.error as e:
                            print(f"No se pudo cargar la carátula {cover_path}: {e}")
                            return None
    except Exception as e:
        print(f"Error al buscar carátulas: {e}")
    
    return None

def load_roms_and_folders(current_path):
    """
    Carga el contenido del directorio actual, organizando ROMs por consola.
    Retorna lista de items y la ruta cargada.
    """
    items = []
    console_map = {
        '.gba': 'GBA',
        '.nes': 'NES', 
        '.smc': 'SNES',
        '.sfc': 'SNES'
    }
    
    # Vista especial para el directorio raíz
    if current_path == ROM_DIR:
        roms_by_console = {}
        
        # Recorrer estructura de directorios
        for root, dirs, files in os.walk(current_path):
            for file in files:
                # Clasificar ROMs por consola
                for ext, console in console_map.items():
                    if file.lower().endswith(ext):
                        full_path = os.path.join(root, file)
                        if console not in roms_by_console:
                            roms_by_console[console] = []
                        roms_by_console[console].append(('rom', file, full_path))
                        break
        
        # Construir lista organizada por consola
        for console in sorted(roms_by_console.keys()):
            items.append(('console', console, None))
            for rom in sorted(roms_by_console[console], key=lambda x: x[1]):
                items.append(rom)
    else:
        # Vista normal para subdirectorios
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
    """
    Renderiza la interfaz del menú principal.
    Incluye navegación, vista previa de carátulas y controles.
    """
    font = pygame.font.Font(None, 24)
    title_font = pygame.font.Font(None, 30)
    controls_font = pygame.font.Font(None, 26)
    console_font = pygame.font.Font(None, 28)
    
    screen.fill(COLOR_BG)
    
    # Área de título
    title_area = pygame.Rect(0, 0, 640, 60)
    pygame.draw.rect(screen, COLOR_SEARCH_BG, title_area)
    pygame.draw.line(screen, COLOR_HIGHLIGHT, (0, title_area.height), (640, title_area.height), 2)
    
    # Mostrar ruta actual
    rel_path = os.path.relpath(current_path, ROM_DIR)
    title_text = "Todas las ROMs" if rel_path == "." else f"Ubicación: {rel_path}"
    title = title_font.render(title_text, True, COLOR_HIGHLIGHT)
    screen.blit(title, (320 - title.get_width()//2, 20))

    # Mostrar mensaje si no hay items
    if not items:
        no_results = font.render("No hay ROMs en esta carpeta", True, COLOR_TEXT)
        screen.blit(no_results, (320 - no_results.get_width()//2, 150))
    else:
        # Asegurar que el seleccionado no sea un encabezado de consola
        while selected < len(items) and items[selected][0] == 'console':
            selected += 1
            if selected >= len(items):
                selected = 0
        
        # Configuración de desplazamiento
        item_height = 24
        console_header_height = 28
        max_items_visible = 13
        
        # Renderizar items visibles
        y_pos = 80
        start_idx = max(0, selected - (max_items_visible // 2))
        end_idx = min(len(items), start_idx + max_items_visible)
        
        for idx in range(start_idx, end_idx):
            item_type, name, _ = items[idx]
            
            if item_type == 'console':
                # Encabezado de consola
                text = console_font.render(f"--- {name} ---", True, COLOR_HIGHLIGHT)
                screen.blit(text, (50, y_pos))
                y_pos += console_header_height
            else:
                # Item normal (ROM o carpeta)
                color = COLOR_SELECTED if idx == selected else COLOR_TEXT
                prefix = "> " if idx == selected else "  "
                text = font.render(f"{prefix}{name}", True, color)
                screen.blit(text, (50, y_pos))
                y_pos += item_height

    # Mostrar carátula del juego seleccionado
    if items and selected < len(items) and items[selected][0] == 'rom':
        cover_area = pygame.Rect(460, 70, 165, 150)
        
        # Fondo para carátula
        cover_bg = pygame.Surface((cover_area.width, cover_area.height), pygame.SRCALPHA)
        cover_bg.fill((30, 30, 30, 200))
        screen.blit(cover_bg, cover_area.topleft)
        
        # Cargar y mostrar carátula
        cover_image = load_game_cover(items[selected][1])
        if cover_image:
            # Escalar imagen manteniendo proporciones
            img_ratio = min(cover_area.width/cover_image.get_width(), 
                           cover_area.height/cover_image.get_height())
            new_width = int(cover_image.get_width() * img_ratio)
            new_height = int(cover_image.get_height() * img_ratio)
            scaled_cover = pygame.transform.scale(cover_image, (new_width, new_height))
            
            # Centrar imagen
            pos_x = cover_area.x + (cover_area.width - new_width) // 2
            pos_y = cover_area.y + (cover_area.height - new_height) // 2
            screen.blit(scaled_cover, (pos_x, pos_y))
        else:
            # Mensaje si no hay carátula
            no_cover = font.render("Sin carátula", True, COLOR_TEXT)
            screen.blit(no_cover, (cover_area.centerx - no_cover.get_width()//2, 
                                 cover_area.centery - no_cover.get_height()//2))
        
        # Borde para el área de carátula
        pygame.draw.rect(screen, COLOR_HIGHLIGHT, cover_area, 2, border_radius=5)

    # Área de controles
    controls_area = pygame.Rect(0, 400, 640, 80)
    pygame.draw.rect(screen, COLOR_SEARCH_BG, controls_area)
    pygame.draw.line(screen, COLOR_HIGHLIGHT, (0, controls_area.y), (640, controls_area.y), 2)
    
    # Instrucciones de controles
    controls_title = controls_font.render("Controles del Menú", True, COLOR_HIGHLIGHT)
    screen.blit(controls_title, (320 - controls_title.get_width()//2, controls_area.y + 10))
    
    a_text = controls_font.render("A : Seleccionar", True, COLOR_TEXT)
    nav_text = controls_font.render("↑/↓ : Navegar", True, COLOR_TEXT)
    search_text = controls_font.render("← : Buscar", True, COLOR_TEXT)
    shutdown_text = controls_font.render("SELECT+START : Apagar", True, (255, 100, 100))

    screen.blit(a_text, (125, controls_area.y + 30))
    screen.blit(nav_text, (275, controls_area.y + 30))
    screen.blit(search_text, (425, controls_area.y + 30))
    
    screen.blit(shutdown_text, (320 - shutdown_text.get_width()//2, controls_area.y + 60))

    return screen

def folder_menu(joystick, game_state):
    """
    Maneja el menú principal de navegación por directorios.
    Controla la interacción del usuario y la navegación.
    """
    screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    
    input_cooldown = 0.1
    repeat_delay = 0.0
    repeat_rate = 0.1
    last_input_time = 0
    last_hat = (0, 0)
    
    reload_items = True
    
    while True:
        # Mostrar notificación de copia si es necesario
        if game_state.show_copy_notification:
            show_copy_confirmation(screen, game_state.copied_files)
            game_state.show_copy_notification = False
            reload_items = True
            
        # Recargar items si es necesario
        if reload_items:
            items, loaded_path = load_roms_and_folders(game_state.current_path)
            
            if loaded_path != game_state.current_path:
                print(f"Advertencia: Ruta cargada ({loaded_path}) no coincide con current_path ({game_state.current_path})")
                game_state.current_path = loaded_path
            
            # Restaurar selección guardada para esta ruta
            if game_state.current_path in game_state.selection_history:
                saved_selection = game_state.selection_history[game_state.current_path]
                while saved_selection < len(items) and items[saved_selection][0] == 'console':
                    saved_selection += 1
                    if saved_selection >= len(items):
                        saved_selection = 0
                game_state.selected = saved_selection if saved_selection < len(items) else 0
            else:
                game_state.selected = 0
            
            reload_items = False

        # Manejar caso de directorio vacío
        if not items:
            font = pygame.font.Font(None, 32)
            screen.fill(COLOR_BG)
            msg = font.render("No hay ROMs en esta carpeta", True, COLOR_TEXT)
            screen.blit(msg, (50, 50))
            back_msg = font.render("Presiona B para volver", True, COLOR_TEXT)
            screen.blit(back_msg, (50, 90))
            pygame.display.update()
            
            # Esperar acción del usuario
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
                        elif event.button == 6 or event.button == 7:  # SELECT+START
                            if joystick.get_button(6) and joystick.get_button(7):
                                shutdown_raspberry()
                time.sleep(0.1)
            continue

        # Dibujar menú y manejar entrada
        draw_menu(screen, items, game_state.selected, game_state.current_path, game_state)
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.JOYHATMOTION:
                hat = event.value
                current_time = time.time()
                
                # Manejar movimiento del D-Pad
                if hat != (0, 0):
                    if hat != last_hat or current_time - last_input_time > repeat_delay:
                        if hat[1] == 1:  # Arriba
                            game_state.selected = max(0, game_state.selected - 1)
                            while game_state.selected > 0 and items[game_state.selected][0] == 'console':
                                game_state.selected -= 1
                        elif hat[1] == -1:  # Abajo
                            game_state.selected = min(len(items) - 1, game_state.selected + 1)
                            while game_state.selected < len(items) - 1 and items[game_state.selected][0] == 'console':
                                game_state.selected += 1
                        elif hat[0] == -1:  # Izquierda (activar búsqueda)
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
                    if item[0] != 'console':
                        # Guardar selección actual en el historial
                        game_state.selection_history[game_state.current_path] = game_state.selected
                        
                        if item[0] == 'folder':
                            # Navegar a subdirectorio
                            game_state.path_stack.append(game_state.current_path)
                            game_state.current_path = item[2]
                            reload_items = True
                        elif item[0] == 'rom':
                            # Iniciar juego
                            launch_game(item[2], joystick)
                            screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
                            pygame.mouse.set_visible(False)
                
                elif event.button == 1:  # Botón B
                    if len(game_state.path_stack) > 1:
                        # Volver al directorio anterior
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
        
        time.sleep(0.01)

def search_roms(search_text, root_dir):
    """
    Busca ROMs en el sistema de archivos que coincidan con el texto.
    Retorna lista de resultados organizados por consola.
    """
    results = []
    search_lower = search_text.lower()
    
    # Mapeo de extensiones a consolas
    console_map = {
        '.gba': 'GBA',
        '.nes': 'NES',
        '.smc': 'SNES',
        '.sfc': 'SNES'
    }
    
    # Buscar recursivamente en el directorio raíz
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            file_lower = file.lower()
            # Verificar extensiones compatibles y coincidencia en nombre
            for ext in console_map.keys():
                if file_lower.endswith(ext) and search_lower in file_lower:
                    console = console_map[ext]
                    results.append(('rom', file, os.path.join(root, file), console))
                    break
    
    # Ordenar resultados por consola y nombre
    results.sort(key=lambda x: (x[3], x[1]))
    return results

def draw_search_results(screen, game_state):
    """
    Renderiza la pantalla de resultados de búsqueda.
    Muestra lista de juegos encontrados y vista previa de carátula.
    """
    font = pygame.font.Font(None, 22)
    title_font = pygame.font.Font(None, 30)
    controls_font = pygame.font.Font(None, 26)
    console_font = pygame.font.Font(None, 28)
    
    screen.fill(COLOR_BG)
    
    # Área de título
    title_area = pygame.Rect(0, 0, 640, 60)
    pygame.draw.rect(screen, COLOR_SEARCH_BG, title_area)
    pygame.draw.line(screen, COLOR_HIGHLIGHT, (0, title_area.height), 
                    (640, title_area.height), 2)
    
    # Mostrar texto de búsqueda
    title = title_font.render(f"Resultados para: '{game_state.search_text}'", True, COLOR_HIGHLIGHT)
    screen.blit(title, (320 - title.get_width()//2, 20))
    
    results_area = pygame.Rect(0, title_area.height, 640, 300)
    
    # Manejar caso sin resultados
    if not game_state.search_results:
        no_results = font.render("No se encontraron ROMs", True, COLOR_TEXT)
        screen.blit(no_results, (320 - no_results.get_width()//2, 150))
        
        instruction = controls_font.render("Presiona A para regresar al menu principal", True, COLOR_HIGHLIGHT)
        screen.blit(instruction, (320 - instruction.get_width()//2, 200))
    else:
        # Mostrar lista de resultados
        y_pos = 80
        current_console = None
        start_idx = max(0, game_state.search_selected - 5)
        end_idx = min(len(game_state.search_results), start_idx + 10)
        
        for idx in range(start_idx, end_idx):
            item = game_state.search_results[idx]
            _, name, _, console = item
            
            # Encabezado de consola si cambió
            if console != current_console:
                current_console = console
                console_header = console_font.render(f"--- {console} ---", True, COLOR_HIGHLIGHT)
                screen.blit(console_header, (50, y_pos))
                y_pos += 30
            
            # Item de resultado
            color = COLOR_SELECTED if idx == game_state.search_selected else COLOR_TEXT
            text = font.render(f"  {name}", True, color)
            screen.blit(text, (50, y_pos))
            y_pos += 22
    
    # Mostrar carátula del resultado seleccionado
    if game_state.search_results and game_state.search_selected < len(game_state.search_results):
        cover_area = pygame.Rect(400, 70, 200, 150)
        
        # Fondo para carátula
        cover_bg = pygame.Surface((cover_area.width, cover_area.height), pygame.SRCALPHA)
        cover_bg.fill((30, 30, 30, 200))
        screen.blit(cover_bg, cover_area.topleft)
        
        # Cargar y mostrar carátula
        selected_item = game_state.search_results[game_state.search_selected]
        cover_image = load_game_cover(selected_item[1])
        
        if cover_image:
            # Escalar manteniendo proporciones
            img_ratio = min(cover_area.width/cover_image.get_width(), 
                           cover_area.height/cover_image.get_height())
            new_width = int(cover_image.get_width() * img_ratio)
            new_height = int(cover_image.get_height() * img_ratio)
            scaled_cover = pygame.transform.scale(cover_image, (new_width, new_height))
            
            # Centrar imagen
            pos_x = cover_area.x + (cover_area.width - new_width) // 2
            pos_y = cover_area.y + (cover_area.height - new_height) // 2
            screen.blit(scaled_cover, (pos_x, pos_y))
        else:
            # Mensaje si no hay carátula
            no_cover = font.render("Sin carátula", True, COLOR_TEXT)
            screen.blit(no_cover, (cover_area.centerx - no_cover.get_width()//2, 
                                 cover_area.centery - no_cover.get_height()//2))
        
        # Borde para el área de carátula
        pygame.draw.rect(screen, COLOR_HIGHLIGHT, cover_area, 2, border_radius=5)
    
    # Área de controles
    controls_area = pygame.Rect(0, 400, 640, 80)
    pygame.draw.rect(screen, COLOR_SEARCH_BG, controls_area)
    pygame.draw.line(screen, COLOR_HIGHLIGHT, (0, controls_area.y), 
                    (640, controls_area.y), 2)
    
    # Mostrar instrucciones de controles si hay resultados
    if game_state.search_results:
        controls_title = controls_font.render("Controles de Búsqueda", True, COLOR_HIGHLIGHT)
        screen.blit(controls_title, (320 - controls_title.get_width()//2, controls_area.y + 10))
        
        a_text = controls_font.render("A : Seleccionar", True, COLOR_TEXT)
        b_text = controls_font.render("B : Menú principal", True, COLOR_TEXT)
        nav_text = controls_font.render("↑/↓ : Navegar", True, COLOR_TEXT)
        shutdown_text = controls_font.render("SELECT+START : Apagar", True, (255, 100, 100))

        screen.blit(a_text, (100, controls_area.y + 30))
        screen.blit(b_text, (250, controls_area.y + 30))
        screen.blit(nav_text, (420, controls_area.y + 30))
        
        screen.blit(shutdown_text, (320 - shutdown_text.get_width()//2, controls_area.y + 60))
        
    pygame.display.update()

def show_search_keyboard(screen, game_state):
    """
    Muestra el teclado virtual para ingresar texto de búsqueda.
    Retorna lista de teclas renderizadas (no utilizada en esta implementación).
    """
    font = pygame.font.Font(None, 28)
    small_font = pygame.font.Font(None, 22)
    title_font = pygame.font.Font(None, 30)
    warning_font = pygame.font.Font(None, 24)
    
    screen.fill(COLOR_BG)
    
    # Mostrar advertencia importante
    line1 = warning_font.render("Importante. Si no se detecta la pulsación de las flechas para moverse", True, (255, 255, 0))
    line2 = warning_font.render("por el teclado, por favor desconecta y conecta el control.", True, (255, 255, 0))
    
    screen.blit(line1, (320 - line1.get_width() // 2, 10))
    screen.blit(line2, (320 - line2.get_width() // 2, 35))
    
    # Título de la pantalla
    title = title_font.render("BUSCAR ROMS", True, COLOR_HIGHLIGHT)
    screen.blit(title, (320 - title.get_width() // 2, 70))
    
    # Área de texto de búsqueda
    search_rect = pygame.Rect(40, 110, 560, 50)
    pygame.draw.rect(screen, COLOR_SEARCH_BG, search_rect, border_radius=5)
    pygame.draw.rect(screen, COLOR_HIGHLIGHT, search_rect, 2, border_radius=5)
    
    # Mostrar texto ingresado (últimos 20 caracteres si es muy largo)
    display_text = game_state.search_text[-20:] if len(game_state.search_text) > 20 else game_state.search_text
    text_surface = font.render(display_text + "|", True, COLOR_TEXT)
    screen.blit(text_surface, (search_rect.x + 10, search_rect.y + 10))
    
    # Configurar distribución del teclado
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
        # Calcular ancho total de la fila para centrarla
        row_width = sum(
            (key_width * (5 if key in ['SPACE'] else 3 if key in ['DEL'] else 1) + 
             key_margin * (4 if key in ['SPACE'] else 2 if key in ['DEL'] else 0))
            for key in row
        ) - key_margin
        
        start_x = (640 - row_width) // 2
        
        # Dibujar cada tecla en la fila
        for col_idx, key in enumerate(row):
            # Determinar tamaño de tecla especial
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
            
            # Resaltar tecla seleccionada
            is_selected = (row_idx, col_idx) == game_state.keyboard_selected
            key_color = COLOR_SEARCH_HIGHLIGHT if is_selected else COLOR_KEY
            pygame.draw.rect(screen, key_color, key_rect, border_radius=4)
            pygame.draw.rect(screen, COLOR_TEXT, key_rect, 2 if is_selected else 1, border_radius=4)
            
            # Dibujar texto de la tecla
            if key == 'SPACE':
                key_text = small_font.render("SPACE", True, COLOR_TEXT)
            elif key == 'DEL':
                key_text = small_font.render("DEL", True, COLOR_TEXT)
            else:
                key_text = font.render(key, True, COLOR_TEXT)
            
            screen.blit(key_text, (key_rect.centerx - key_text.get_width() // 2, 
                                key_rect.centery - key_text.get_height() // 2))
    
    # Mostrar instrucciones de controles
    instructions = [
        ("START: Buscar", "B: Cancelar"),
        ("A: Seleccionar tecla", "Y: Espacio"),
        ("X: Borrar", "")
    ]
    
    instruction_y = 380
    for row in instructions:
        if row[0]:
            rendered1 = small_font.render(row[0], True, COLOR_TEXT)
            screen.blit(rendered1, (220 - rendered1.get_width() // 2, instruction_y))
        
        if row[1]:
            rendered2 = small_font.render(row[1], True, COLOR_TEXT)
            screen.blit(rendered2, (420 - rendered2.get_width() // 2, instruction_y))
        
        instruction_y += 30
    
    return []

def handle_search_menu(joystick, game_state):
    """
    Maneja la interacción con el teclado virtual de búsqueda.
    Controla la navegación y entrada de texto.
    """
    screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    
    game_state.keyboard_selected = (0, 0)
    input_cooldown = 0.1
    last_input_time = 0
    last_hat = (0, 0)
    repeat_delay = 0.3
    repeat_rate = 0.1
    
    while game_state.search_active:
        # Mostrar notificación de copia si es necesario
        if game_state.show_copy_notification:
            show_copy_confirmation(screen, game_state.copied_files)
            game_state.show_copy_notification = False
            show_search_keyboard(screen, game_state)
            pygame.display.update()

        # Verificar conexión del control
        if pygame.joystick.get_count() == 0:
            print("Control desconectado en teclado virtual, esperando reconexión...")
            joystick = show_connect_controller(require_button_press=False)
            if joystick:
                print("Control reconectado, continuando en teclado virtual...")
                game_state.joystick = joystick
                continue

        current_time = time.time()
        key_buttons = show_search_keyboard(screen, game_state)
        
        # Manejar entrada del D-Pad
        hat = joystick.get_hat(0)
        
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
        
        # Mover selección del teclado según D-Pad
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
        
        # Manejar eventos de botones
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:  # Botón A
                    row, col = game_state.keyboard_selected
                    key = game_state.keyboard_layout[row][col]
                    
                    # Manejar teclas especiales
                    if key == 'SPACE':
                        game_state.search_text += ' '
                    elif key == 'DEL':
                        game_state.search_text = game_state.search_text[:-1]
                    else:
                        game_state.search_text += key.lower()
                
                elif event.button == 3:  # Botón Y (Espacio alternativo)
                    game_state.search_text += ' '
                
                elif event.button == 2:  # Botón X (Borrar alternativo)
                    game_state.search_text = game_state.search_text[:-1]
                
                elif event.button == 1:  # Botón B (Cancelar)
                    game_state.search_active = False
                    return
                
                elif event.button == 7:  # Botón START (Buscar)
                    if game_state.search_text:
                        # Realizar búsqueda y mostrar resultados
                        game_state.search_results = search_roms(game_state.search_text, ROM_DIR)
                        game_state.search_selected = 0
                        show_search_results_menu(joystick, game_state)
                        screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
                        pygame.mouse.set_visible(False)
        
        pygame.display.update()
        time.sleep(0.01)

def show_search_results_menu(joystick, game_state):
    """
    Maneja la pantalla de resultados de búsqueda.
    Permite navegar y seleccionar juegos encontrados.
    """
    screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    
    input_cooldown = 0.1
    repeat_delay = 0.3
    repeat_rate = 0.1
    last_input_time = 0
    last_hat = (0, 0)
    
    while game_state.search_active:
        # Mostrar notificación de copia si es necesario
        if game_state.show_copy_notification:
            show_copy_confirmation(screen, game_state.copied_files)
            game_state.show_copy_notification = False
            draw_search_results(screen, game_state)
            pygame.display.update()
            
        # Verificar conexión del control
        if pygame.joystick.get_count() == 0:
            print("Control desconectado en resultados de búsqueda, esperando reconexión...")
            joystick = show_connect_controller(require_button_press=False)
            if joystick:
                print("Control reconectado, continuando en resultados...")
                game_state.joystick = joystick
                draw_search_results(screen, game_state)
                pygame.display.update()
                continue

        current_time = time.time()
        draw_search_results(screen, game_state)
        
        # Manejar caso sin resultados
        if not game_state.search_results:
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN and event.button == 0:
                    game_state.search_active = False
                    return
            pygame.display.update()
            time.sleep(0.01)
            continue
        
        # Manejar entrada del D-Pad
        hat = joystick.get_hat(0)
        
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
        
        # Mover selección en resultados
        if should_move:
            if hat[1] == 1:  # Arriba
                game_state.search_selected = max(0, game_state.search_selected - 1)
                last_input_time = current_time
            elif hat[1] == -1:  # Abajo
                game_state.search_selected = min(len(game_state.search_results) - 1, 
                                               game_state.search_selected + 1)
                last_input_time = current_time
        
        # Manejar eventos de botones
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:  # Botón A (Seleccionar)
                    if game_state.search_results:
                        selected_rom = game_state.search_results[game_state.search_selected]
                        _, ext = os.path.splitext(selected_rom[2])
                        launch_game(selected_rom[2], joystick)
                        screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
                        pygame.mouse.set_visible(False)
                        game_state.search_active = False
                        return
                
                elif event.button == 1:  # Botón B (Volver)
                    game_state.search_active = False
                    return

                elif event.button == 6 or event.button == 7:  # SELECT+START (Apagar)
                    if joystick.get_button(6) and joystick.get_button(7):
                        shutdown_raspberry()
        
        pygame.display.update()
        time.sleep(0.01)

# =============================================
# FUNCIÓN PRINCIPAL Y DE APAGADO
# =============================================

def shutdown_raspberry():
    """
    Muestra mensaje de apagado y apaga el sistema de forma segura.
    """
    try:
        pygame.display.init()
        screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)
        font = pygame.font.Font(None, 36)
        screen.fill((0, 0, 0))
        text = font.render("Apagando el sistema...", True, (255, 255, 255))
        screen.blit(text, (320 - text.get_width()//2, 240 - text.get_height()//2))
        pygame.display.update()
        time.sleep(5)
        pygame.quit()

        os.system('sudo poweroff')
    except Exception as e:
        print(f"Error al intentar apagar: {e}")

def main():
    """
    Función principal que inicia el sistema.
    Coordina la secuencia de inicialización y el bucle principal.
    """
    try:
        # Verificar y crear directorio de ROMs si no existe
        if not os.path.exists(ROM_DIR):
            os.makedirs(ROM_DIR)
        
        # Inicializar sistemas de pygame
        pygame.init()
        pygame.joystick.init()
        
        # Mostrar pantalla de inicio
        show_splash()
        
        # Inicializar estado del juego y monitor USB
        game_state = GameState()
        usb_thread = start_usb_monitor(game_state)
        
        # Bucle principal
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