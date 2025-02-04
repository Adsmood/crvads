import os
import logging
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import aiofiles

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CTVConversionApp")

# Directorios para guardar archivos subidos y exportados
UPLOAD_DIR = "uploads"
EXPORT_DIR = "exports"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

# Inicialización de la aplicación
app = FastAPI()

@app.post("/process_and_download")
async def process_and_download(video_file: UploadFile = File(...)):
    """Procesa el video, genera los archivos exportados y los descarga automáticamente."""
    # Guardar el archivo subido
    filename = video_file.filename
    upload_path = os.path.join(UPLOAD_DIR, filename)
    async with aiofiles.open(upload_path, "wb") as out_file:
        while content := await video_file.read(1024 * 1024):  # Leer en fragmentos de 1MB
            await out_file.write(content)

    logger.info(f"Archivo subido y guardado en: {upload_path}")

    # Simulación de generación del archivo VAST
    vast_filename = f"{filename}_vast.xml"
    vast_filepath = os.path.join(EXPORT_DIR, vast_filename)
    async with aiofiles.open(vast_filepath, "w", encoding="utf-8") as f:
        await f.write("<VAST version='4.0'>VAST Content</VAST>")
    logger.info(f"VAST generado en: {vast_filepath}")

    # Confirmar que el archivo se generó
    if not os.path.exists(vast_filepath):
        logger.error(f"El archivo VAST no se generó en {vast_filepath}")
        return {"error": "No se pudo generar el archivo VAST"}

    # Enviar el archivo como respuesta para su descarga
    return FileResponse(
        path=vast_filepath,
        filename=vast_filename,
        media_type="application/xml"
    )
