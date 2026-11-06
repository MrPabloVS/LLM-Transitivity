# Cómo generar y abrir el informe: guía para macOS y Windows

Esta guía está escrita para personas sin experiencia de programación.
Explica cómo instalar las herramientas, descargar el proyecto, generar el informe
y abrir las tablas interactivas y el explorador de casos.

El ejemplo usa la corrida `2026-11-06_01-23-40-040fd7b7`: 54.000 preguntas,
seis modelos y 324.000 respuestas. Generar el informe vuelve a analizar las
respuestas guardadas. **No vuelve a consultar a los modelos ni genera cargos
por nuevas respuestas.**

## 1. Qué vas a obtener

| Archivo | Para qué sirve |
| --- | --- |
| `report.md` | Informe en Markdown, que se puede leer en GitHub o un editor. |
| `index.html` | Informe para leer en el navegador, con tablas y gráficos estáticos. |
| `explorer.html` | Otra página con tablas interactivas, filtros y explorador de casos. |
| `figures/` | Gráficos SVG. |
| `tables/` | Tablas CSV para abrir en una planilla. |
| `data/` | Casos y respuestas que usa el explorador, separados por dataset. |
| `summary.json` | Resumen de resultados que usa la página interactiva. |
| `analysis.sqlite` | Base de datos derivada del análisis. No hace falta abrirla para leer el informe. |
| `provenance.json` | Referencias y hashes para identificar los archivos analizados. |
| `validation.json` | Constancia de que terminó la validación del informe. |

El informe y el explorador muestran los mismos resultados. El explorador permite
filtrar condiciones y comparar las seis respuestas originales de cada caso.
Un caso es una pregunta completa; puede contener varias oraciones.

## 2. Antes de empezar

Necesitás una computadora con macOS o Windows, un navegador y conexión a Internet
para las instalaciones y descargas. Después de instalar todo y descargar los
archivos, el análisis y la visualización funcionan sin conexión.

Reservá **al menos 45 GB libres** como margen de trabajo para una copia del
proyecto, los objetos LFS locales, la corrida y un informe nuevo. No es una
medición exacta: cada informe adicional necesita más espacio. La corrida ocupa
unos 15,4 GB; Git LFS guarda también una copia local de sus objetos.

Las herramientas cumplen estas funciones:

- **Git:** descarga el proyecto y su historial.
- **Git LFS:** descarga los archivos grandes de evidencia y resultados.
- **uv:** instala Python y las bibliotecas que necesita el proyecto.
- **Python 3.14:** ejecuta el generador y el servidor local del navegador.
- **Homebrew, solo en el recorrido de macOS:** instala Git y Git LFS.

No necesitás instalar Python previamente, usar una clave de OpenRouter,
crear un archivo `.env`, instalar Inspect a mano ni comprar acceso a un modelo.
`uv sync --locked` instala automáticamente las bibliotecas del proyecto.

En una computadora administrada por una organización, puede hacer falta ayuda
del equipo de soporte para instalar programas.

## 3. Cómo copiar los comandos

Una terminal es una ventana donde escribís instrucciones. En macOS se llama
**Terminal**. En Windows usaremos **PowerShell**.

Copiá el texto dentro de cada bloque, pegalo en esa ventana y presioná **Enter**.
No copies los títulos ni las marcas de tres acentos que rodean los bloques.
Esperá a que termine cada paso antes de continuar. Si hay varias líneas en un
bloque, podés ejecutarlas una por una.

Mientras trabaja un comando puede aparecer mucho texto. Cuando vuelve a aparecer
la línea donde podés escribir, terminó. Si aparece un error, revisá la sección de
problemas antes de seguir.

## 4. Instalar las herramientas en macOS

Si usás Windows, saltá a la sección 5.

### 4.1. Abrir Terminal

Presioná **Command + Espacio**, escribí `Terminal` y presioná Enter.

### 4.2. Instalar Homebrew

Probá primero:

```sh
brew --version
```

Si muestra una versión, ya está instalado. Si dice `command not found`, seguí
las instrucciones de [la página oficial de Homebrew](https://brew.sh/).
El comando oficial es:

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

El instalador explica lo que hará y puede pedir la contraseña de tu usuario de
Mac. Al escribir una contraseña en Terminal, no aparecen letras ni puntos: es
normal. Seguí los pasos que muestre. Si pide instalar las herramientas de línea
de comandos de Apple, completá esa instalación.

Al terminar, leé **Next steps**. Copiá y ejecutá las instrucciones que allí indique
para agregar Homebrew al entorno. Las rutas pueden variar entre un Mac con Apple
Silicon y uno con Intel; usá las que muestra tu instalador.

Cerrá Terminal, abrila otra vez y comprobá:

```sh
brew --version
```

Homebrew publica sus requisitos de macOS en su sitio. Si tu sistema no es
compatible, pedí ayuda antes de continuar con esta ruta de instalación.

### 4.3. Instalar Git y Git LFS

```sh
brew install git git-lfs
```

Cuando termine:

```sh
git --version
git lfs version
git lfs install
```

Los dos primeros deben mostrar versiones. El último suele mostrar
`Git LFS initialized.`. No hace falta ejecutar `git lfs track`: las reglas ya
están en el proyecto.

### 4.4. Instalar uv

Usá el instalador de [la documentación oficial de uv](https://docs.astral.sh/uv/getting-started/installation/):

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Cerrá y volvé a abrir Terminal. Comprobá:

```sh
uv --version
```

### 4.5. Instalar Python 3.14

```sh
uv python install 3.14
```

uv descarga Python. No reemplaces la versión de Python que usa macOS.
La [guía oficial de Python en uv](https://docs.astral.sh/uv/guides/install-python/)
explica esta instalación.

### 4.6. Crear una carpeta de trabajo

```sh
mkdir -p "$HOME/llm-work"
cd "$HOME/llm-work"
```

Ahora seguí en la sección 6.

## 5. Instalar las herramientas en Windows

Si completaste la instalación de macOS, saltá a la sección 6.

### 5.1. Abrir PowerShell

Abrí Inicio, escribí **PowerShell** y abrilo. Usá PowerShell para los comandos de
Windows de esta guía; no el Símbolo del sistema ni Git Bash.

### 5.2. Instalar Git

Abrí [la descarga oficial de Git para Windows](https://git-scm.com/install/windows).
Elegí el instalador para tu equipo. La mayoría usa x64; un equipo con procesador
ARM necesita ARM64. Podés consultar el tipo de sistema en Configuración →
Sistema → Acerca de.

Abrí el instalador y seguí sus pantallas. Para el uso de Git desde otros programas,
elegí la opción **Git from the command line and also from 3rd-party software**
si aparece. Conservá las demás opciones predeterminadas si no tenés una necesidad
particular. Completá la instalación, cerrá PowerShell y abrilo de nuevo.

```powershell
git --version
```

Debe mostrar una versión.

### 5.3. Instalar o comprobar Git LFS

```powershell
git lfs version
```

Si muestra una versión, continuá con `git lfs install`. Si dice que `lfs` no es un
comando de Git, descargá el instalador de Windows de [Git LFS](https://git-lfs.com/).
Abrí el archivo `.exe` descargado y completá el asistente. Cerrá PowerShell y
abrilo otra vez para que reconozca el programa.

```powershell
git lfs version
git lfs install
```

La [guía oficial de instalación de LFS](https://docs.github.com/en/repositories/working-with-files/managing-large-files/installing-git-large-file-storage)
detalla este procedimiento.

### 5.4. Instalar uv

Copiá este comando oficial en PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Esperá a que termine. Cerrá PowerShell, abrilo de nuevo y comprobá:

```powershell
uv --version
```

Este comando usa el instalador oficial de uv. No requiere instalar Python antes.

### 5.5. Instalar Python 3.14

```powershell
uv python install 3.14
```

No hace falta usar Microsoft Store ni instalar otro Python por separado.

### 5.6. Crear una carpeta de trabajo

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\llm-work"
Set-Location "$env:USERPROFILE\llm-work"
```

## 6. Descargar el proyecto completo

Estos comandos sirven tanto en Terminal de macOS como en PowerShell de Windows:

```sh
git -c core.longpaths=true -c core.autocrlf=false clone --branch tobe/runs-2026-11-05 https://github.com/MrPabloVS/LLM-Transitivity.git
cd LLM-Transitivity
git config core.longpaths true
git config core.autocrlf false
git lfs pull
```

La descarga puede tardar bastante porque incluye evidencia grande. No cierres
la ventana mientras trabaja. `git lfs pull` completa los archivos grandes si no
se descargaron durante el primer comando.

La opción `core.autocrlf=false` conserva los saltos de línea de los archivos.
Es necesaria para que las comprobaciones de hashes funcionen también en Windows.

Usamos una rama concreta del proyecto: `tobe/runs-2026-11-05`. No uses la descarga
**Download ZIP** de GitHub ni una copia sin historial: el generador consulta Git
para comprobar los originales. No agregues `--depth` al comando de descarga.

Si GitHub solicita acceso, usá una cuenta con permiso para el repositorio.
No pegues contraseñas ni claves en los archivos del proyecto.

Si ya tenés una copia del proyecto, no ejecutes `clone` sobre la misma carpeta.
Para evitar mezclar cambios propios, podés crear otra carpeta de trabajo con un
nombre diferente y hacer allí la descarga de esta sección.

Comprobá la rama:

```sh
git branch --show-current
```

Debe mostrar `tobe/runs-2026-11-05`.

## 7. Preparar el proyecto

Todos los comandos siguientes se ejecutan dentro de `LLM-Transitivity`.
No hace falta activar manualmente un entorno virtual.

### 7.1. Configurar texto UTF-8

Esto permite leer correctamente acentos y otros caracteres de las respuestas.
Ejecutalo también cada vez que abras una terminal nueva para trabajar con el informe.

En macOS:

```sh
export PYTHONUTF8=1
```

En Windows:

```powershell
$env:PYTHONUTF8 = "1"
```

### 7.2. Instalar las bibliotecas del proyecto

En ambos sistemas:

```sh
uv sync --locked
uv run --locked python --version
uv run --locked transitivity report --help
```

Esperá a que termine la instalación. La versión de Python debe ser 3.14.x.
El último comando debe mostrar las opciones `--run` y `--output`.
`--locked` hace que se respeten las versiones de bibliotecas guardadas en
`uv.lock`. Conservá ese archivo.

## 8. Elegir: leer el informe existente o generar otro

Si solo querés leer los resultados, **no hace falta regenerarlos ni descomprimir
la base SQLite**. Andá directamente a la sección 10 y usá `analysis-v3`.

Si querés generar un informe desde las respuestas originales, continuá con la
sección 9. Descargar el CSV o la base de datos del informe no reemplaza los logs
nativos que necesita el generador.

## 9. Generar un informe nuevo

### 9.1. Comprobar que está la corrida completa

La carpeta necesaria es:

```text
results/full/2026-11-06_01-23-40-040fd7b7/
```

Contiene `full_manifest.json`, `worker.json`, `events.jsonl` y las carpetas
`preflight/` y `corpus/`. Estas contienen los logs, cierres y copias congeladas
de los archivos del experimento. La carpeta completa se versiona con Git LFS;
no alcanza con copiar únicamente los archivos `.eval`.

Comprobá los objetos descargados:

```sh
git lfs fsck
```

Esperá a que termine. Si informa archivos faltantes o corruptos, no generes el
informe todavía: volvé a ejecutar `git lfs pull` y revisá los mensajes.

En macOS podés comprobar la carpeta con:

```sh
ls results/full/2026-11-06_01-23-40-040fd7b7
```

En Windows:

```powershell
Get-ChildItem results/full/2026-11-06_01-23-40-040fd7b7
```

Si la corrida no está, necesitás una versión de la rama que ya la incluya y acceso
a sus objetos LFS. Como alternativa, pedile a quien mantiene el experimento una
copia íntegra de esa carpeta y colocala en esa misma ruta. No inventes ni edites
los archivos faltantes.

### 9.2. Ejecutar el generador

El mismo comando funciona en ambos sistemas. Copialo como una sola línea:

```sh
uv run --locked transitivity report --run results/full/2026-11-06_01-23-40-040fd7b7 --correction results/corrections/2026-11-06_15-37-32-64caf3fd-eate-to-ate-v1 --output reports/full/2026-11-06_01-23-40-040fd7b7/mi-informe-01
```

`--run` señala la corrida original. `--correction` señala la ejecución con las
respuestas nuevas para los 612 casos corregidos. Necesitás ambas carpetas
completas para reconstruir el informe actual. La carpeta de corrección es
`results/corrections/2026-11-06_15-37-32-64caf3fd-eate-to-ate-v1`. `--output` indica dónde crear el
informe nuevo. **La carpeta de salida no debe existir.** No la crees antes.
Si ya existe `mi-informe-01`, usá `mi-informe-02`, y así sucesivamente.

El programa revisa los originales, lee las respuestas y calcula las tablas.
Después genera Markdown, las dos páginas HTML, los gráficos y los datos del
explorador. No ejecutes `pilot`, `full`, `followup` ni `correction` para esta tarea: esos son
comandos de ejecución del experimento.

### 9.3. Esperar a que termine

Durante el proceso aparecen mensajes como `corpus: verified 20/108 tasks`.
Es normal que una tarea tarde y que no aparezcan mensajes durante algunos pasos.
La duración depende del equipo y del disco; esta guía no fija un tiempo máximo.
Mantené el equipo encendido y la ventana abierta.

Al terminar correctamente, aparece:

```text
Report complete: ...
```

Debe existir `validation.json` dentro de `mi-informe-01`, con `"complete": true`.
No consideres terminado un informe que no tenga esa constancia.

Si se interrumpe, no lo reinicies sobre esa misma carpeta. Conservá la salida
incompleta para revisar el error y elegí otro nombre de salida para reintentar.
El generador no modifica las respuestas originales.

## 10. Abrir el informe y el explorador

### 10.1. Iniciar el servidor local

Desde `LLM-Transitivity`, ejecutá en cualquiera de los dos sistemas:

```sh
uv run --locked python -m http.server 7590 --bind 127.0.0.1
```

La ventana muestra un mensaje parecido a `Serving HTTP on 127.0.0.1 port 7590`.
**Dejá esa ventana abierta.** Ahora está atendiendo al navegador y no vuelve
inmediatamente a la línea para escribir comandos. Eso es normal.

No hace falta instalar un servidor adicional. El servidor se conecta solo a tu
computadora; no publica una web en Internet.

### 10.2. Abrir las páginas en el navegador

Para el informe que acabás de generar, copiá estas direcciones en Chrome, Edge,
Safari o Firefox:

- Informe: <http://127.0.0.1:7590/reports/full/2026-11-06_01-23-40-040fd7b7/mi-informe-01/index.html>
- Tablas y explorador: <http://127.0.0.1:7590/reports/full/2026-11-06_01-23-40-040fd7b7/mi-informe-01/explorer.html>

Si elegiste otro nombre de salida, reemplazá `mi-informe-01` en las direcciones.
Para abrir el informe ya guardado en el proyecto, usá `analysis-v3` en su lugar:

- Informe existente: <http://127.0.0.1:7590/reports/full/2026-11-06_01-23-40-040fd7b7/analysis-v3/index.html>
- Explorador existente: <http://127.0.0.1:7590/reports/full/2026-11-06_01-23-40-040fd7b7/analysis-v3/explorer.html>

No abras el HTML con doble clic: puede abrirse como `file://` y el navegador
puede bloquear la lectura de los datos interactivos. Usá las direcciones HTTP.

El informe incluye enlaces a las tablas y al explorador. El explorador incluye
un enlace para volver al informe. El Markdown se llama `report.md`: podés leerlo
en GitHub, en un editor compatible o como texto.

### 10.3. Usar las tablas interactivas

En **Compare conditions**, elegí un modelo o una condición. Podés combinar filtros
como `family = HS` y `frequency = LF`. Los resultados se actualizan debajo.
Para quitar un filtro, elegí **All**. Una combinación sin casos muestra un
denominador cero; no significa un resultado de 0% de acuerdo.

### 10.4. Usar el explorador

En **Explore all 54,000 cases**:

1. Elegí un dataset, que es un grupo de preguntas.
2. Esperá a que cargue. Se descarga un dataset por vez desde tu disco.
3. Si querés, filtrá por resultado, etiqueta fuente u orden de las premisas.
4. Abrí un caso pulsando su identificador.
5. Leé la pregunta original y la comparación de las seis respuestas.
6. Abrí la respuesta de cada modelo para ver su texto original.
7. Usá **Next 50** y **Previous 50** para cambiar de página.

Podés pegar un UID completo en **Find UID**. El UID identifica un caso; si es de
otro dataset, el explorador cambia a ese dataset. Si no aparece, quitá los demás
filtros y comprobá que copiaste el identificador completo.

Las etiquetas fuente son las etiquetas del dataset. El acuerdo con ellas no
constituye por sí solo una auditoría de validez lógica.

### 10.5. Cerrar y volver a abrir otro día

Para detener el servidor, volvé a su ventana y presioná **Control + C** en ambos
sistemas. En Mac, es Control, no Command. Después podés cerrar la terminal.
Los archivos del informe quedan guardados.

Otro día, abrí Terminal o PowerShell, entrá a la carpeta del proyecto, configurá
UTF-8 como en la sección 7.1 y repetí el comando del servidor de la sección 10.1.
No hace falta volver a generar el informe.

En macOS, para volver a la carpeta:

```sh
cd "$HOME/llm-work/LLM-Transitivity"
```

En Windows:

```powershell
Set-Location "$env:USERPROFILE\llm-work\LLM-Transitivity"
```

## 11. Si algo no funciona

| Mensaje o síntoma | Qué hacer |
| --- | --- |
| `uv` o `git` no se reconoce | Cerrá y abrí la terminal. Comprobá las versiones. Si sigue igual, revisá los pasos finales del instalador. |
| `lfs is not a git command` | Instalá Git LFS y abrí otra terminal; repetí `git lfs install`. |
| GitHub pide permiso o devuelve 403 | Comprobá que tu cuenta tenga acceso al repositorio y a sus objetos LFS. |
| La descarga LFS falla por cuota | Pedile al responsable del repositorio que revise el almacenamiento o transferencia de LFS. No reemplaces los objetos por archivos vacíos. |
| `pyproject.toml` no aparece o el comando no encuentra el proyecto | Entrá a `LLM-Transitivity` con el comando `cd` o `Set-Location` correspondiente. |
| Un archivo grande contiene solo tres líneas con `git-lfs.github.com/spec/v1` | Es un puntero sin descargar. Ejecutá `git lfs pull`. |
| Falta `worker.json`, un cierre o un log | No está la corrida completa. Revisá la sección 9.1. |
| `Report output already exists` | Elegí un nombre de salida nuevo. No borres evidencia para resolverlo. |
| Aparece un error de hash, de scorer o de corrida incompleta | Detenete y compartí el mensaje completo con quien mantiene el experimento. No cambies originales ni scores para que pase. |
| Windows informa una ruta demasiado larga | Revisá `git config core.longpaths true`; si persiste, pedí ayuda para usar una ruta de trabajo más corta y habilitar rutas largas en Windows. |
| El navegador dice conexión rechazada | El servidor está detenido. Volvé a ejecutar la sección 10.1 y dejá abierta la terminal. |
| El navegador muestra 404 | Revisá el nombre del informe en la dirección y que el servidor se haya iniciado desde `LLM-Transitivity`. |
| Las tablas quedan en “Loading…” | Usá HTTP y no `file://`. Comprobá que existan `summary.json`, `report.js` y la carpeta `data/`. |
| El puerto 7590 está ocupado | Si el servidor anterior funciona, usalo. Si no, iniciá el nuevo con el puerto 7591 y cambiá también el puerto en todas las direcciones del navegador. |

Para usar otro puerto:

```sh
uv run --locked python -m http.server 7591 --bind 127.0.0.1
```

Si una instalación requiere una conexión que no tenés o permisos de administrador,
resolvé ese requisito antes de continuar. Guardá el mensaje de error; no hace
falta compartir claves ni contraseñas.

## 12. Qué está verificado y qué falta comprobar en otra computadora

Los comandos del generador y los requisitos de Python se contrastaron con el
código de este proyecto. El informe y el explorador se comprobaron localmente en
macOS. Las instrucciones de instalación se contrastaron con las fuentes oficiales
indicadas abajo. No se ejecutó una instalación desde cero en Windows durante la
preparación de esta guía.

La descarga de la corrida por otra persona requiere que el commit y los objetos
LFS estén publicados en la rama. Un commit local sin push todavía no alcanza.

## Fuentes oficiales

- [Instalar uv en macOS y Windows](https://docs.astral.sh/uv/getting-started/installation/).
- [Instalar Python con uv](https://docs.astral.sh/uv/guides/install-python/).
- [Homebrew y requisitos de macOS](https://brew.sh/).
- [Instalar Git en Windows](https://git-scm.com/install/windows).
- [Git LFS](https://git-lfs.com/).
- [Instalar Git LFS: guía de GitHub](https://docs.github.com/en/repositories/working-with-files/managing-large-files/installing-git-large-file-storage).
- [Arquitectura del generador](architecture.md#offline-full-corpus-report).
