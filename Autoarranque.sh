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


# 11. Mostrar mensaje de salida
echo "================================================="
echo " INSTALACIÓN COMPLETADA SATISFACTORIAMENTE! "
echo "================================================="
echo ""
echo "El sistema se reiniciará en 10 segundos..."
sleep 10
sudo reboot
