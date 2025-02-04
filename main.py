import os
import shutil
import subprocess
import logging
from datetime import datetime
from fastapi import FastAPI, Request, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CTVConversionApp")

# Directorios para guardar archivos subidos y exportados
UPLOAD_DIR = "uploads"
EXPORT_DIR = "exports"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

# Inicialización de la aplicación FastAPI y configuración de plantillas
app = FastAPI(title="WebApp de Conversión y VAST Interactivo")
templates = Jinja2Templates(directory="templates")

# Montar la carpeta de exports para servir archivos estáticos
app.mount("/exports", StaticFiles(directory=EXPORT_DIR), name="exports")

# Parámetros de conversión por cada plataforma
PLATFORMS = {
    "roku": {
        "codec": "libx264",
        "resolution": "1920x1080",
        "bitrate": "1500k",
        "container": "mp4",
        "sdk_vendor": "roku",
        "sdk_url": "https://sdk.roku.com/raf.js"
    },
    "firetv": {
        "codec": "libx264",
        "resolution": "1280x720",
        "bitrate": "1200k",
        "container": "mp4",
        "sdk_vendor": "amazon",
        "sdk_url": "https://aps.amazon.com/sdk.js"
    },
    "appletv": {
        "codec": "libx264",
        "resolution": "1920x1080",
        "bitrate": "2000k",
        "container": "mov",
        "sdk_vendor": "apple",
        "sdk_url": "https://ads.apple.com/tvos-sdk.js"
    },
    "androidtv": {
        "codec": "libx264",
        "resolution": "1280x720",
        "bitrate": "1200k",
        "container": "mp4",
        "sdk_vendor": "amazon",
        "sdk_url": "https://aps.amazon.com/sdk.js"
    },
    "samsung": {
        "codec": "libx265",
        "resolution": "1920x1080",
        "bitrate": "1800k",
        "container": "mp4",
        "sdk_vendor": "samsung",
        "sdk_url": "https://ads.samsung.com/sdk.js"
    },
    "lg": {
        "codec": "libx264",
        "resolution": "1920x1080",
        "bitrate": "1800k",
        "container": "mp4",
        "sdk_vendor": "lg",
        "sdk_url": "https://ads.lg.com/webos-sdk.js"
    },
    "vizio": {
        "codec": "libx265",
        "resolution": "1920x1080",
        "bitrate": "2000k",
        "container": "mp4",
        "sdk_vendor": "vizio",
        "sdk_url": "https://ads.vizio.com/sdk.js"
    },
}

# Resto de funciones (sin cambios)...

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Renderiza la página principal con el formulario."""
    return templates.TemplateResponse("index.html", {"request": request})



if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)


