He modificado el archivo `main.py` para implementar la subida de archivos en fragmentos utilizando `aiofiles`. El resto del archivo se ha mantenido igual.

Aquí tienes el código modificado:

```python
import os
import logging
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import aiofiles

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
    # Guardar el archivo subido por fragmentos
    filename = video_file.filename
    upload_path = os.path.join(UPLOAD_DIR, filename)
    async with aiofiles.open(upload_path, "wb") as out_file:
        while content := await video_file.read(1024 * 1024):  # Leer en fragmentos de 1MB
            await out_file.write(content)

    logger.info(f"Archivo subido y guardado en: {upload_path}")

    # Simulación de generación del VAST
    vast_filename = f"{filename}_vast.xml"
    vast_filepath = os.path.join(EXPORT_DIR, vast_filename)
    async with aiofiles.open(vast_filepath, "w", encoding="utf-8") as f:
        await f.write("<VAST version='4.0'>VAST Content</VAST>")

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
```
