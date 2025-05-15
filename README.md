			
			█▀█ ▄▀█ █▀▄▀█ ▄▀█   █▀ █▀█ █░░ █▀█   █▀▄ █▀▀   █ █▄░█ █▀ ▀█▀ ▄▀█ █░░ ▄▀█ █▀▀ █ █▀█ █▄░█
			█▀▄ █▀█ █░▀░█ █▀█   ▄█ █▄█ █▄▄ █▄█   █▄▀ ██▄   █ █░▀█ ▄█ ░█░ █▀█ █▄▄ █▀█ █▄▄ █ █▄█ █░▀█
			




			█▀▀ █▀▀ ░░▀ █▀▀█ █▀▄▀█ █▀▄▀█ ▒█▀▀█ █▀▀█ █▀▄▀█ ░▀░ █▀▀▄ █▀▀▀ 
			█░░ █░░ ░░█ █░░█ █░▀░█ █░▀░█ ▒█░▄▄ █▄▄█ █░▀░█ ▀█▀ █░░█ █░▀█ 
			▀▀▀ ▀▀▀ █▄█ █▀▀▀ ▀░░░▀ ▀░░░▀ ▒█▄▄█ ▀░░▀ ▀░░░▀ ▀▀▀ ▀░░▀ ▀▀▀▀

# Proyecto Final - Sistemas Embebidos

**Materia:** 	Sistemas Embebidos 
**Semestre:**	2025-2
**Autores:**  
		- Cortés Hernández José César  
		- Montes Suarez Manuel Alejandro  
		- Peralta Rodríguez Juan Manuel  

## 📌 Descripción  
En esta rama del repositorio se encuentran los archivos necesarios para la instalacion de la retroconsola en la Raspberry Pi 4.

## 💻 Instalacion
Para ejecutar la instalacion se debe de tomar en cuenta lo siguiente:
	- Instalacion limpia de Raspios Lite 
	- Tener conexion a internet

Tomando en cuenta que los archivos necesarios para la instalacion estan ubicados en la rama Instalacion del repositorio
se debe de ejecutar desde el usuario local la linea siguiente:

	$ sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/JuanPer03/ccjpmmGaming/Instalacion/instalacion.sh)"

Esto instalara automaticamente las librerias necesarias y extraera las carpetas necesarias para el correcto funcionamiento de la retroconsola.

## 📂 Estructura de la rama
/Intsalacion
└── README.md   				 # Este archivo
└── Retroconsole.zip     # Archivo que contiene la estructura de carpetas para el correcto funcionamiento de la retroconsola
└── RomsGBA1.zip         # Archivo que contiene más roms de GBA
└── RomsGBA2.zip         # Archivo que contiene más roms de GBA
└── RomsNES.zip          # Archivo que contiene más roms de NES
└── RomsSNES.zip         # Archivo que contiene más roms de SNES
└── instalacion.sh       # Script para la autoinstalacion
└── mednafen.cfg         # Archivo de configuracion del emulador con las configuraciones para el control de Xbox Series S/X 
