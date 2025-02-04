import os
import shutil
import logging
from datetime import datetime
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
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

# Página principal
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Renderiza la página principal con el formulario."""
    return templates.TemplateResponse("index.html", {"request": request})

# Endpoint para subir y descargar el archivo generado
@app.post("/process_and_download")
async def process_and_download(video_file: UploadFile = File(...)):
    """Procesa el video, genera los archivos exportados y los descarga automáticamente."""
    # Guardar el archivo subido temporalmente
    filename = video_file.filename
    upload_path = os.path.join(UPLOAD_DIR, filename)
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)

    logger.info(f"Archivo subido y guardado en: {upload_path}")

    # Simulación de generación del VAST
    vast_filename = f"{filename}_vast.xml"
    vast_filepath = os.path.join(EXPORT_DIR, vast_filename)
    with open(vast_filepath, "w", encoding="utf-8") as f:
        f.write("<VAST version='4.0'>VAST Content</VAST>")

    logger.info(f"VAST generado en: {vast_filepath}")

    # Enviar el archivo generado como respuesta de descarga
    return FileResponse(
        path=vast_filepath,
        filename=vast_filename,
        media_type="application/xml"
    )

# Punto de entrada para ejecutar la aplicación
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Puerto dinámico en Render
    uvicorn.run("main:app", host="0.0.0.0", port=port)
