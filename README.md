# ☁️ Antigravity Quota Monitor (GitHub Cloud)

Monitor centralizado de cuota y tokens para Google Antigravity en la nube, usando **GitHub Pages** y la **API de GitHub**. Permite monitorizar el consumo unificado de múltiples ordenadores usando la misma cuenta.

---

## 🌟 Características

* **Consumo multi-dispositivo:** Agrupa automáticamente las peticiones y tokens de tus diferentes PCs (PC Sobremesa, Portátil, etc.).
* **Filtros por dispositivo:** Selector interactivo para ver el consumo **Combinado Global** o inspeccionar cada PC por separado.
* **Control de Ventanas Móviles:** Calcula en tiempo real las ventanas de las **Últimas 5 Horas** y **Últimos 7 Días**.
* **Límites personalizables:** Ajusta tu cuota máxima desde el panel web con cálculo automático de % y peticiones restantes.
* **100% Gratuito y sin dependencias:** No requiere librerías `pip`, bases de datos externas ni servidores que mantener.

---

## 🚀 Despliegue Rápido (5 minutos)

### Paso 1: Crear el repositorio en GitHub
1. Entra en tu cuenta de [GitHub](https://github.com) y crea un nuevo repositorio llamado:  
   `antigravity-quota-monitor` (Recomendado: **Público** para usar GitHub Pages gratuito).
2. Sube los archivos de este directorio:
   ```bash
   git init
   git add index.html exporter.py config.example.json .gitignore README.md
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/antigravity-quota-monitor.git
   git push -u origin main
   ```

### Paso 2: Activar GitHub Pages
1. En tu repositorio de GitHub, ve a **Settings** > **Pages**.
2. En **Build and deployment > Source**, selecciona **Deploy from a branch**.
3. Selecciona la rama `main` y la carpeta `/ (root)`. Haz clic en **Save**.
4. ¡Listo! Tu panel estará disponible en:  
   `https://TU_USUARIO.github.io/antigravity-quota-monitor/`

### Paso 3: Generar un Token de GitHub
1. En GitHub, ve a tu avatar (arriba a la derecha) > **Settings** > **Developer Settings** > **Personal access tokens** > **Tokens (classic)** (o Fine-grained).
2. Genera un nuevo token con permiso:
   * Marcando la casilla: `repo` (permiso para leer y escribir contenidos en el repositorio).
3. Copia el token generado.

### Paso 4: Configurar tus PCs
En cada PC donde uses Antigravity:
1. Copia `config.example.json` y renómbralo a `config.json`:
   ```json
   {
     "github_token": "ghp_TU_TOKEN_AQUI",
     "repo_owner": "TU_USUARIO",
     "repo_name": "antigravity-quota-monitor",
     "device_id": "PC-Sobremesa"
   }
   ```
   *(En tu segundo PC, cambia `"device_id"` por `"Portatil"`).*
2. Prueba la primera subida ejecutando:
   ```bash
   python exporter.py
   ```
3. Activa la sincronización automática cada 30 minutos (en segundo plano con `pythonw.exe`) ejecutando en PowerShell:
   ```powershell
   powershell -ExecutionPolicy Bypass -File register_hourly_task.ps1
   ```

---

## 🔒 Privacidad y Seguridad
* El script `exporter.py` **NUNCA** envía prompts, código fuente ni rutas de archivos.
* **Únicamente envía agregaciones numéricas**: modelo utilizado, cantidad de peticiones y conteo de tokens.
* El archivo `config.json` con tu token está en `.gitignore` para evitar que se suba accidentalmente a GitHub.
