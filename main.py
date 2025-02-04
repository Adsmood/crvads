import os
import shutil
import logging
from datetime import datetime
from fastapi import FastAPI, Request, UploadFile, File, BackgroundTasks
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

# Montar las carpetas estáticas
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/exports", StaticFiles(directory=EXPORT_DIR), name="exports")

# Endpoint para la página principal
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Renderiza la página principal con el formulario."""
    return templates.TemplateResponse("index.html", {"request": request})

# Endpoint para subir videos
@app.post("/upload")
async def upload_video(video_file: UploadFile = File(...)):
    """Sube un archivo al servidor."""
    filename = video_file.filename
    upload_path = os.path.join(UPLOAD_DIR, filename)
    
    # Guardar el archivo subido
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)
    
    logger.info(f"Archivo subido: {upload_path}")
    return {"message": "Archivo subido correctamente", "path": f"/uploads/{filename}"}

# Punto de entrada para Uvicorn
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Puerto dinámico en Render
    uvicorn.run("main:app", host="0.0.0.0", port=port)
