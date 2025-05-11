
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
La implementacion de este proyecto es para convertir la Raspberry Pi 4 en una consola retro capaz de emular las siguientes consolas:
	- Game Boy Advanced (GBA)
	- Nintendo Entertainment System (NES)
	- Super Nintendo Entertainment System (SNES)

Mediante la ejecucion de un programa desarrollado en python, implementando funcionalidades como:
	- Copia automatica de ROMS al momdento de conectar una memoria USB que contenga roms de estas consolas
	  en la carpeta raiz de la misma.
	- Control total mediante un mando de Xbox Series S/X.
	- Sistema de busqueda de roms mediante un teclado virtual.
	- Interrupcion de emulacion para poder cambiar de juego o consola.

## 🛠️ Hardware Utilizado  
- Microcontrolador: Raspberry Pi 4
- Gamepad: Control de Xbox Series S/X
- Monitor: Cualquier monitor con coneccion HDMI
- Audio: Bocinas externas con conexion jack de 3.5 mm 

## 📂 Estructura del Proyecto 
``plaintext 
/Carpeta raiz  
├── doc/  # Documentos que contienen el tutorial de instalacion pero con enfasis de desarrollo diferentes
├────SistemasEmbebidos-CHJC-ProyectoUSB					# Tutorial de instalacion con enfasis en la parte de deteccion de USB
├────SistemasEmbebidos-MSMA-ProyectoEmulacion			# Tutorial de instalacion con enfasis en la parte de emulacion
├────SistemasEmbebidos-PRJM-ProyectoInterfazGrafica		# Tutorial de instalacion con enfasis en la parte del desarrollo de la interfaz grafica
├
├── src/ # Arcihvos principales de autoinstalacion y funcionamiento principal
├────code.py 					# Codifo principal del programa
├────instalacion.sh 			# Script que se ejecuta para la autoinstalacion
├
├── vid/ # Video evidencia de funcionamiento		
├────VideoEntregaProyecto.txt	# Archivo de texto con link al video de evidencia de funcionamiento
├
├── LICENSE     				# Licencia
└── README.md   				# Este archivo  

## 💻 Instalacion
Para ejecutar la instalacion se debe de tomar en cuenta lo siguiente:
	- Instalacion limpia de Raspios Lite 
	- Tener conexion a internet

Tomando en cuenta que los archivos necesarios para la instalacion estan ubicados en la rama Instalacion del repositorio
se debe de ejecutar desde el usuario local la linea siguiente:

	$ sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/JuanPer03/ccjpmmGaming/Instalacion/instalacion.sh)"

Esto instalara automaticamente las librerias necesarias y extraera las carpetas necesarias para el correcto funcionamiento de la retroconsola.

## 🔗 Links de interes
``plaintext 
Link al video evidencia de funcionamiento: https://youtu.be/znDL1qFbyX8

Link al repositorio en gituhb del proyecto: https://github.com/JuanPer03/ccjpmmGaming
