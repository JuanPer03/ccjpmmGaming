def draw_menu(screen, items, selected, current_path, game_state):
    """Dibuja el menú principal con carátulas superpuestas sobre la lista de ROMs"""
    # Configuración de fuentes
    font = pygame.font.Font(None, 28)  # Fuente para las ROMs (tamaño reducido)
    title_font = pygame.font.Font(None, 30)  # Fuente para el título
    controls_font = pygame.font.Font(None, 26)  # Fuente para los controles
    console_font = pygame.font.Font(None, 28)  # Fuente para los encabezados de consola
    
    # 1. Dibujar fondo
    screen.fill(COLOR_BG)
    
    # 2. Dibujar barra de título
    title_area = pygame.Rect(0, 0, 640, 60)
    pygame.draw.rect(screen, COLOR_SEARCH_BG, title_area)
    pygame.draw.line(screen, COLOR_HIGHLIGHT, (0, title_area.height), (640, title_area.height), 2)
    
    # Título con ruta actual
    rel_path = os.path.relpath(current_path, ROM_DIR)
    title_text = "Todas las ROMs" if rel_path == "." else f"Ubicación: {rel_path}"
    title = title_font.render(title_text, True, COLOR_HIGHLIGHT)
    screen.blit(title, (320 - title.get_width()//2, 20))

    # 3. Dibujar lista de ROMs (fondo)
    if not items:
        # Mensaje si no hay items
        no_results = font.render("No hay ROMs en esta carpeta", True, COLOR_TEXT)
        screen.blit(no_results, (320 - no_results.get_width()//2, 150))
    else:
        # Mostrar items agrupados por consola
        y_pos = 80  # Posición vertical inicial
        start_idx = max(0, selected - 5)  # Índice de inicio para el scroll
        end_idx = min(len(items), start_idx + 10)  # Índice final para el scroll
        
        for idx in range(start_idx, end_idx):
            item_type, name, _ = items[idx]
            color = COLOR_SELECTED if idx == selected else COLOR_TEXT
            prefix = "> " if idx == selected else "  "
            
            if item_type == 'console':
                # Encabezado de consola
                text = console_font.render(f"--- {name} ---", True, COLOR_HIGHLIGHT)
                screen.blit(text, (50, y_pos))
                y_pos += 30
            else:
                # Item de ROM
                text = font.render(f"{prefix}{name}", True, color)
                screen.blit(text, (50, y_pos))
                y_pos += 28  # Espaciado reducido para la fuente más pequeña

    # 4. Dibujar carátula (primer plano)
    if items and selected < len(items) and items[selected][0] == 'rom':
        cover_area = pygame.Rect(400, 70, 200, 150)  # Área de la carátula
        
        # Crear superficie semitransparente para el fondo
        cover_bg = pygame.Surface((cover_area.width, cover_area.height), pygame.SRCALPHA)
        cover_bg.fill((30, 30, 30, 200))  # Fondo oscuro semitransparente
        screen.blit(cover_bg, cover_area.topleft)
        
        # Cargar y mostrar carátula
        cover_image = load_game_cover(items[selected][1])
        if cover_image:
            # Escalar manteniendo relación de aspecto
            img_ratio = min(cover_area.width/cover_image.get_width(), 
                           cover_area.height/cover_image.get_height())
            new_width = int(cover_image.get_width() * img_ratio)
            new_height = int(cover_image.get_height() * img_ratio)
            scaled_cover = pygame.transform.scale(cover_image, (new_width, new_height))
            
            # Centrar en el área
            pos_x = cover_area.x + (cover_area.width - new_width) // 2
            pos_y = cover_area.y + (cover_area.height - new_height) // 2
            screen.blit(scaled_cover, (pos_x, pos_y))
        else:
            # Placeholder si no hay carátula
            no_cover = font.render("Sin carátula", True, COLOR_TEXT)
            screen.blit(no_cover, (cover_area.centerx - no_cover.get_width()//2, 
                                 cover_area.centery - no_cover.get_height()//2))
        
        # Borde decorativo
        pygame.draw.rect(screen, COLOR_HIGHLIGHT, cover_area, 2, border_radius=5)

    # 5. Dibujar controles (siempre visibles)
    controls_area = pygame.Rect(0, 400, 640, 80)
    pygame.draw.rect(screen, COLOR_SEARCH_BG, controls_area)
    pygame.draw.line(screen, COLOR_HIGHLIGHT, (0, controls_area.y), (640, controls_area.y), 2)
    
    # Texto de controles
    controls_title = controls_font.render("Controles del Menú", True, COLOR_HIGHLIGHT)
    screen.blit(controls_title, (320 - controls_title.get_width()//2, controls_area.y + 10))
    
    # Controles individuales
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
    
    # Botón de apagado (centrado)
    screen.blit(shutdown_text, (320 - shutdown_text.get_width()//2, controls_area.y + 60))

    return screen
