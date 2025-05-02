#!/bin/bash

# Script de preconfiguracion para RetroConsole en Raspberry Pi OS Lite
# Muestra mensajes de progreso durante la instalación
# Autor: ccjpmmGaming 
echo ""
echo ""
echo "==================================================="
echo "  PRECONFIGURACIÓN PARA RETROCONSOLE EN RASPBERRY  "
echo "==================================================="
echo ""
echo ""

# Función para mostrar mensajes de instalación
function instalar {
    echo "Instalando $1..."
    shift
    $@
    if [ $? -eq 0 ]; then
        echo "$1 se instaló con éxito!"
        echo ""
    else
        echo "Error al instalar $1"
        exit 1
    fi
}

# 1. Actualizar sistema base
instalar "paquetes base" sudo apt update && sudo apt upgrade -y

# 2. Instalar dependencias esenciales
instalar "Python y dependencias básicas" sudo apt install -y python3 python3-pip python3-dev

# 3. Instalar dependencias para Pygame
instalar "dependencias de SDL para Pygame" sudo apt install -y libsdl2-dev libsdl2-mixer-dev libsdl2-image-dev libsdl2-ttf-dev

# 4. Instalar el emulador Mednafen
instalar "emulador Mednafen" sudo apt install -y mednafen

# 5. Instalar paquetes Python
instalar "Pygame" sudo apt install -y python3 python3-pygame
instalar "PyUDEV" sudo apt install -y python3 python3-pyudev

# 6. Instalar dependencias adicionales para Raspberry Pi
instalar "optimizaciones para Raspberry Pi" sudo apt install -y libatlas-base-dev

# 7. Crear estructura de directorio
echo "Creando estructura de directorios..."
mkdir -p /home/ccjpmmGaming
mkdir -p /home/ccjpmmGaming/usb
echo "Directorios creados con éxito!"
echo ""

# Mensaje final
echo "================================================="
echo " PRECONFIGURACIÓN COMPLETADA SATISFACTORIAMENTE! "
echo "================================================="
echo ""
