#!/bin/bash

# Script para descargar carátulas (requiere sudo para permisos)
# Uso: sudo ./descargar_caratulas_sudo.sh

# --- Verificar root ---
if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: Este script debe ejecutarse con sudo" >&2
  exit 1
fi

# --- Configuración ---
USER_NORMAL="ccjpmmGaming"  # Cambia al usuario normal correcto
RUTA_BASE="/home/$USER_NORMAL/Retroconsole/libretro-thumbnails"
REPO_URL="https://github.com/libretro/libretro-thumbnails.git"
CARPETAS=(
    "Nintendo - Nintendo Entertainment System/Named_Titles"
    "Nintendo - Super Nintendo Entertainment System/Named_Titles"
    "Nintendo - Game Boy Advance/Named_Titles"
)

# --- Verificar git ---
if ! command -v git &> /dev/null; then
  echo "Instalando git..."
  apt-get update && apt-get install -y git || {
    echo "ERROR: No se pudo instalar git" >&2
    exit 1
  }
fi

# --- Crear directorio con permisos correctos ---
echo "Creando directorio en $RUTA_BASE..."
mkdir -p "$RUTA_BASE" && chown "$USER_NORMAL:$USER_NORMAL" "$RUTA_BASE" || {
  echo "ERROR: No se pudo configurar el directorio" >&2
  exit 1
}

# --- Ejecutar como usuario normal el git sparse-checkout ---
echo "Configurando git sparse-checkout..."
sudo -u "$USER_NORMAL" bash << USER_SCRIPT
cd "$RUTA_BASE" || exit 1

if [ ! -d ".git" ]; then
  git init
  git config core.sparseCheckout true

  for carpeta in "${CARPETAS[@]}"; do
    echo "Añadiendo \$carpeta"
    echo "\$carpeta" >> .git/info/sparse-checkout
  done

  git remote add origin "$REPO_URL"
fi
USER_SCRIPT

# --- Descargar ---
echo "Descargando carátulas..."
sudo -u "$USER_NORMAL" git -C "$RUTA_BASE" pull --depth=1 origin main || {
  echo "ERROR: Falló la descarga" >&2
  exit 1
}

# --- Ajustar permisos finales ---
chown -R "$USER_NORMAL:$USER_NORMAL" "$RUTA_BASE"

echo ""
echo "¡Descarga completada!"
echo "Carátulas disponibles en: $RUTA_BASE"
echo "Sistemas descargados:"
sudo -u "$USER_NORMAL" ls -la "$RUTA_BASE"
