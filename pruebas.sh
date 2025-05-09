#!/bin/bash

# Script de instalacion para RetroConsole en Raspberry Pi OS Lite
# Muestra mensajes de progreso durante la instalación
# Autor: ccjpmmGaming 
echo ""
echo ""
echo "==================================================="
echo "  INSTALACIÓN PARA RETROCONSOLE EN RASPBERRY  "
echo "==================================================="
echo ""
echo ""

# Función para mostrar mensajes de instalación
function instalar {
    echo ""
    echo ""
    echo "==================================================="
    echo "Instalando $1..."
    echo "==================================================="
    echo ""
    echo ""
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

# 0. Actualizar sistema base
instalar "paquetes base" sudo apt update && sudo apt upgrade -y

# 1. Instalar git y clonar la informacion del repositorio de github
instalar "Git y clonando repositorio" sudo apt install git -y
sudo git clone -b Instalacion --single-branch https://github.com/JuanPer03/ccjpmmGaming.git

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
echo ""
echo ""
echo "==================================================="
echo "Creando estructura de directorios..."
mkdir -p /home/ccjpmmGaming
mkdir -p /home/ccjpmmGaming/usb
mkdir -p ~/.mednafen
echo "Directorios creados con éxito!"
echo ""

# 8. Descomprimir la carpeta de la consola
echo ""
echo ""
echo "==================================================="
echo "Copiando archivos de consola..."
unzip ccjpmmGaming/Retroconsole.zip -d /home/ccjpmmGaming
: << come
# 9. Hacer que el programa de la consola se ejecute al encender
echo ""
echo ""
echo "==================================================="
echo "Aplicado la configuracion de arranque automatico...."
# Ruta del script de Python que se va a ejecutar al inicio
PYTHON_SCRIPT="/home/ccjpmmGaming/Retroconsole/code/Code.py"
# Ruta del archivo de log (se creará automáticamente si no existe)
LOG_FILE="/home/ccjpmmGaming/log.txt"
# Verifica si el script de Python existe
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: El archivo $PYTHON_SCRIPT no existe."
    exit 1
fi
# Crea el archivo log.txt si no existe
touch "$LOG_FILE"
# Verifica si ya existe una entrada @reboot en crontab
if crontab -l | grep -q "@reboot.*$PYTHON_SCRIPT"; then
    echo "Cron ya está configurado para ejecutar $PYTHON_SCRIPT al inicio."
else
    # Agrega la línea @reboot a crontab
    (crontab -l 2>/dev/null; echo "@reboot python3 $PYTHON_SCRIPT >> $LOG_FILE 2>&1") | crontab -
    echo "Configuración de cron agregada para ejecutar $PYTHON_SCRIPT al inicio."
fi
echo "¡Listo! configuracion de autoarranque hecha"
come
# 10. Copiar configuracion inicial de mednafen
echo ""
echo ""
echo "==================================================="
echo "Aplicado la configuracion de Mednafen...."
# Obtener el nombre de usuario actual (no root)
USERNAME=$(who am i | awk '{print $1}')
# Ejecuta Mednafen como usuario normal en segundo plano
sudo -u $USERNAME mednafen &
# Guarda el PID (Process ID) del proceso Mednafen
MEDNAFEN_PID=$!
# Espera 10 segundos
sleep 10
# Cierra Mednafen usando su PID
kill $MEDNAFEN_PID
cp ccjpmmGaming/mednafen.cfg ~/.mednafen/mednafen.cfg

# 11. Modificar cmdline.txt para ocultar mensajes de arranque
echo ""
echo ""
echo "==================================================="
echo "Modificando /boot/firmware/cmdline.txt..."
# Verifica si los parámetros ya existen en el archivo
if ! grep -q "quiet loglevel=0 logo.nologo fsck.mode=skip" /boot/firmware/cmdline.txt; then
    # Agrega los parámetros al final del archivo sin salto de línea
    sudo sed -i '$s/$/ quiet loglevel=0 logo.nologo fsck.mode=skip/' /boot/firmware/cmdline.txt
    echo "Parámetros agregados a cmdline.txt"
else
    echo "Los parámetros ya existen en cmdline.txt"
fi

# 12. Mostrar mensaje de salida
echo "================================================="
echo " INSTALACIÓN COMPLETADA SATISFACTORIAMENTE! "
echo "================================================="
echo ""
echo "El sistema se reiniciará en 10 segundos..."
sleep 10
sudo reboot
