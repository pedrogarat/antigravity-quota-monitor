# 📋 Instrucciones de Instalación y Traslado (Antigravity Quota Monitor)

Este documento explica cómo trasladar este proyecto a tu **segundo PC (u otros ordenadores)** usando **OneDrive**, para que ambos equipos sumen automáticamente sus consumos de cuota en tu panel central de GitHub.

---

## 🌐 Tu Panel en la Nube
El panel visual unificado está publicado en:  
👉 **[https://pedrogarat.github.io/antigravity-quota-monitor/](https://pedrogarat.github.io/antigravity-quota-monitor/)**

---

## 📁 Paso 1: Copiar la carpeta a OneDrive
1. Copia toda la carpeta del proyecto:
   ```text
   C:\Users\Sergio\.gemini\antigravity\scratch\antigravity-quota-monitor
   ```
2. Pégala dentro de tu carpeta de **OneDrive**.
3. Espera a que OneDrive sincronice los archivos en la nube.

---

## 💻 Paso 2: Instalación en el Segundo PC

Cuando estés en el segundo PC con tu OneDrive conectado:

### 💡 Recomendación previa de ubicación:
Para evitar que OneDrive bloquee archivos en ejecución, copia la carpeta `antigravity-quota-monitor` desde tu OneDrive a una ruta fija local de ese PC, por ejemplo:
`C:\Users\<TuUsuario>\.gemini\antigravity\antigravity-quota-monitor`  
*(o `C:\antigravity-quota-monitor`)*.

---

### Opción A: Instalación Automática en 1 Clic (Recomendada)

1. En el segundo PC, abre la subcarpeta:
   ```text
   cliente_cualquier_pc\
   ```
2. Haz doble clic en el archivo:
   👉 **`INSTALAR_SINCRONIZACION.bat`**
3. El asistente se abrirá en una ventana azul:
   * Detectará automáticamente si tienes Python instalado.
   * Te preguntará qué nombre quieres darle a este segundo PC (por ejemplo: `Portatil`, `PC-Oficina`, etc.).
   * Pulsa `Enter`.
4. **¡Listo!** El instalador:
   * Realizará la primera sincronización con GitHub.
   * Registrará la tarea de Windows para que se ejecute en segundo plano sin ventana **automáticamente cada 30 minutos**.

---

### Opción B: Instalación Manual desde la Raíz del Proyecto

Si prefieres usar los archivos de la raíz del proyecto:
1. Abre el archivo `config.json` con el Bloc de notas.
2. Modifica el campo `"device_id"` con el nombre que quieras para ese PC (por ejemplo `"Portatil"`):
   ```json
   {
     "github_token": "TU_TOKEN_DE_GITHUB",
     "repo_owner": "pedrogarat",
     "repo_name": "antigravity-quota-monitor",
     "device_id": "Portatil"
   }
   ```
3. Haz una prueba inicial ejecutando en consola:
   ```bash
   python exporter.py
   ```
4. Registra la tarea programada cada 30 minutos en PowerShell:
   ```powershell
   powershell -ExecutionPolicy Bypass -File register_hourly_task.ps1
   ```

---

## 🔍 Paso 3: ¿Cómo verificar que está funcionando en el segundo PC?

### 1. Comprobar la tarea en Windows
Abre PowerShell y escribe:
```powershell
Get-ScheduledTask -TaskName "AntigravityQuotaCloudSync"
```
Debe devolver `State: Ready`.

### 2. Comprobar el Panel Web
Entra en:
👉 **[https://pedrogarat.github.io/antigravity-quota-monitor/](https://pedrogarat.github.io/antigravity-quota-monitor/)**
* En la barra superior de "Dispositivos conectados", verás aparecer tanto `PC-Sergio` como tu nuevo equipo (`Portatil`).
* El menú desplegable te permitirá ver el **Consumo Combinado de tu cuenta de Antigravity** o filtrar por cada ordenador individualmente.

---

## ❓ Preguntas frecuentes y solución de problemas

### ¿Qué pasa si el segundo PC no tiene Python?
* Descarga Python desde [python.org/downloads](https://www.python.org/downloads/).
* **IMPORTANTE:** Durante la instalación, marca la casilla que dice **"Add python.exe to PATH"**.
* No necesitas instalar ninguna librería (`pip`), el script solo usa librerías estándar nativas.

### ¿Cómo desinstalar la sincronización de un PC?
En la subcarpeta `cliente_cualquier_pc\`, haz doble clic en **`DESINSTALAR.bat`**. Esto eliminará la tarea programada de Windows sin borrar tus archivos.

### ¿Qué datos se envían a GitHub?
Únicamente conteos numéricos agregados de peticiones y tokens por modelo y fecha. **Nunca se envían prompts, código fuente ni rutas de archivos personales**.
