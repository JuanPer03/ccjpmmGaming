#!/bin/bash

# ===================================================
# SCRIPT DE INSTALACIÓN PARA RETROCONSOLE
# Autor: ccjpmmGaming
# Versión: 2.0
# ===================================================

# Configuración de colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para mostrar mensajes de estado
function mostrar_estado {
    echo -e "${YELLOW}[*]${NC} $1"
}

# Función para mostrar éxito
function mostrar_exito {
    echo -e "${GREEN}[✓]${NC} $1"
}

# Función para mostrar error
function mostrar_error {
    echo -e "${RED}[✗]${NC} $1"
    exit 1
}

# ===================================================
# CONFIGURACIÓN INICIAL
# ===================================================

clear
echo -e "${GREEN}"
echo "==================================================="
echo "  INSTALACIÓN PARA RETROCONSOLE EN RASPBERRY PI    "
echo "==================================================="
echo -e "${NC}"

# Verificar si se ejecuta como root
if [ "$(id -u)" -ne 0 ]; then
    mostrar_error "Este script debe ejecutarse como root. Usa 'sudo $0'"
fi

# ===================================================
# 1. ACTUALIZAR SISTEMA Y INSTALAR GIT
# ===================================================

mostrar_estado "Actualizando sistema e instalando dependencias básicas..."
sudo apt-get update || mostrar_error "Falló al actualizar repositorios"
sudo apt-get upgrade -y || mostrar_error "Falló al actualizar paquetes"
sudo apt-get install -y git || mostrar_error "Falló al instalar git"

# ===================================================
# 2. CLONAR REPOSITORIO
# ===================================================

mostrar_estado "Clonando repositorio de RetroConsole..."
if [ ! -d "ccjpmmGaming" ]; then
    git clone -b Instalacion --single-branch https://github.com/JuanPer03/ccjpmmGaming.git || mostrar_error "Falló al clonar repositorio"
else
    mostrar_estado "El directorio ccjpmmGaming ya existe, omitiendo clonación"
fi

# ===================================================
# 3. CONFIGURAR ARRANQUE SILENCIOSO
# ===================================================

mostrar_estado "Configurando arranque silencioso..."

# Configurar cmdline.txt
if ! grep -q "quiet loglevel=0" /boot/cmdline.txt; then
    sudo cp /boot/cmdline.txt /boot/cmdline.txt.bak
    sudo sed -i 's/$/ quiet loglevel=0 logo.nologo systemd.show_status=0 plymouth.enable=0 vt.global_cursor_default=0/' /boot/cmdline.txt
    mostrar_exito "Configuración de arranque silencioso aplicada"
else
    mostrar_estado "El arranque silencioso ya estaba configurado"
fi

# Deshabilitar consola
mostrar_estado "Deshabilitando consola de texto..."
sudo systemctl disable getty@tty1.service || mostrar_error "Falló al deshabilitar la consola"

# Ocultar cursor
mostrar_estado "Configurando cursor invisible..."
sudo apt-get install -y unclutter
echo "@unclutter -idle 0.1 -root" | sudo tee -a /etc/xdg/lxsession/LXDE-pi/autostart

# ===================================================
# 4. INSTALAR DEPENDENCIAS
# ===================================================

mostrar_estado "Instalando dependencias principales..."

# Dependencias básicas
sudo apt-get install -y python3 python3-pip python3-dev || mostrar_error "Falló al instalar Python"
sudo apt-get install -y libsdl2-dev libsdl2-mixer-dev libsdl2-image-dev libsdl2-ttf-dev || mostrar_error "Falló al instalar dependencias SDL"
sudo apt-get install -y mednafen || mostrar_error "Falló al instalar Mednafen"
sudo apt-get install -y python3-pygame python3-pyudev || mostrar_error "Falló al instalar paquetes Python"
sudo apt-get install -y libatlas-base-dev || mostrar_error "Falló al instalar optimizaciones"

# ===================================================
# 5. CONFIGURAR ESTRUCTURA DE DIRECTORIOS
# ===================================================

mostrar_estado "Creando estructura de directorios..."
mkdir -p /home/ccjpmmGaming/Retroconsole
mkdir -p /home/ccjpmmGaming/usb
mkdir -p ~/.mednafen

# Copiar archivos
mostrar_estado "Copiando archivos de RetroConsole..."
unzip ccjpmmGaming/Retroconsole.zip -d /home/ccjpmmGaming/ || mostrar_error "Falló al descomprimir RetroConsole"

# ===================================================
# 6. CONFIGURAR AUTOARRANQUE
# ===================================================
<< 'comentario'
mostrar_estado "Configurando autoarranque..."

PYTHON_SCRIPT="/home/ccjpmmGaming/Retroconsole/code/Code.py"
LOG_FILE="/home/ccjpmmGaming/log.txt"

# Crear archivo de log
touch "$LOG_FILE"

# Configurar crontab
if ! crontab -l | grep -q "@reboot.*$PYTHON_SCRIPT"; then
    (crontab -l 2>/dev/null; echo "@reboot python3 $PYTHON_SCRIPT >> $LOG_FILE 2>&1") | crontab -
    mostrar_exito "Autoarranque configurado en crontab"
else
    mostrar_estado "El autoarranque ya estaba configurado"
fi
comentario
# ===================================================
# 7. CONFIGURAR MEDNAFEN
# ===================================================

mostrar_estado "Configurando Mednafen..."

# Ejecutar Mednafen brevemente para generar configuración
sudo -u $(logname) mednafen &
MEDNAFEN_PID=$!
sleep 5
kill $MEDNAFEN_PID

# Copiar configuración personalizada
if [ -f "ccjpmmGaming/mednafen.cfg" ]; then
    cp ccjpmmGaming/mednafen.cfg ~/.mednafen/mednafen.cfg
    mostrar_exito "Configuración de Mednafen aplicada"
else
    mostrar_error "No se encontró el archivo mednafen.cfg"
fi

# ===================================================
# FINALIZACIÓN
# ===================================================

mostrar_exito "¡Instalación completada con éxito!"
echo ""
echo -e "${GREEN}==================================================="
echo "  EL SISTEMA SE REINICIARÁ EN 10 SEGUNDOS       "
echo "==================================================="
echo -e "${NC}"

sleep 10
sudo reboot
