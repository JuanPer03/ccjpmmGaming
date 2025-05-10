#!/bin/bash

# Script para descargar solo carátulas de NES, SNES y GBA desde libretro-thumbnails
# Autor: TuNombre
# Uso: ./descargar_caratulas.sh

# --- Configuración ---
RUTA_BASE="/home/ccjpmmGaming/Retroconsole/libretro-thumbnails"
REPO_URL="https://github.com/libretro/libretro-thumbnails.git"
CARPETAS=(
    "Nintendo - Nintendo Entertainment System/Named_Titles"
    "Nintendo - Super Nintendo Entertainment System/Named_Titles"
    "Nintendo - Game Boy Advance/Named_Titles"
)

# --- Verificar dependencias ---
if ! command -v git &> /dev/null; then
    echo "ERROR: Git no está instalado. Instálalo con:"
    echo "sudo apt install git"
    exit 1
fi

# --- Crear directorio base ---
mkdir -p "$RUTA_BASE" || {
    echo "ERROR: No se pudo crear el directorio $RUTA_BASE"
    exit 1
}

cd "$RUTA_BASE" || exit

# --- Configurar sparse checkout ---
if [ ! -d ".git" ]; then
    echo "Inicializando repositorio Git..."
    git init
    git config core.sparseCheckout true
    
    # Añadir carpetas al sparse-checkout
    for carpeta in "${CARPETAS[@]}"; do
        echo "Añadiendo $carpeta"
        echo "$carpeta" >> .git/info/sparse-checkout
    done
    
    git remote add origin "$REPO_URL"
else
    echo "El repositorio ya existe. Actualizando..."
fi

# --- Descargar ---
echo "Descargando carátulas (esto puede tomar unos minutos)..."
git pull --depth=1 origin main || {
    echo "ERROR: Falló la descarga"
    exit 1
}

# --- Resultados ---
echo ""
echo "¡Descarga completada!"
echo "Carátulas disponibles en: $RUTA_BASE"
echo "Sistemas descargados:"
ls -d */
