import os
import logging
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
import aiofiles
import shutil

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CTVConversionApp")

# Directorios para guardar archivos subidos y exportados
UPLOAD_DIR = "uploads"
EXPORT_DIR = "exports"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

# Inicialización de la aplicación
app = FastAPI(title="WebApp de Conversión y VAST Interactivo")

# Parámetros de conversión por cada plataforma
PLATFORMS = {
    "roku": {"codec": "libx264", "resolution": "1920x1080", "bitrate": "1500k", "container": "mp4", "sdk_vendor": "roku", "sdk_url": "https://sdk.roku.com/raf.js"},
    "firetv": {"codec": "libx264", "resolution": "1280x720", "bitrate": "1200k", "container": "mp4", "sdk_vendor": "amazon", "sdk_url": "https://aps.amazon.com/sdk.js"},
    "appletv": {"codec": "libx264", "resolution": "1920x1080", "bitrate": "2000k", "container": "mov", "sdk_vendor": "apple", "sdk_url": "https://ads.apple.com/tvos-sdk.js"},
    "androidtv": {"codec": "libx264", "resolution": "1280x720", "bitrate": "1200k", "container": "mp4", "sdk_vendor": "amazon", "sdk_url": "https://aps.amazon.com/sdk.js"},
    "samsung": {"codec": "libx265", "resolution": "1920x1080", "bitrate": "1800k", "container": "mp4", "sdk_vendor": "samsung", "sdk_url": "https://ads.samsung.com/sdk.js"},
    "lg": {"codec": "libx264", "resolution": "1920x1080", "bitrate": "1800k", "container": "mp4", "sdk_vendor": "lg", "sdk_url": "https://ads.lg.com/webos-sdk.js"},
    "vizio": {"codec": "libx265", "resolution": "1920x1080", "bitrate": "2000k", "container": "mp4", "sdk_vendor": "vizio", "sdk_url": "https://ads.vizio.com/sdk.js"},
}

# Función para generar el contenido del archivo VAST
def generate_vast_xml(media_files: dict, button_text: str, button_color: str, button_url: str) -> str:
    ad_id = datetime.now().strftime("%Y%m%d%H%M%S")
    vast_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<VAST version="4.2" xmlns="http://www.iab.com/VAST">',
        f'  <Ad id="{ad_id}">',
        '    <InLine>',
        '      <AdSystem>CTVConversionSystem</AdSystem>',
        '      <AdTitle>Interactive Ad</AdTitle>',
        '      <Impression><![CDATA[https://adsmood.com/track/impression]]></Impression>',
        '      <Creatives>',
        '        <Creative id="1" sequence="1">',
        f'          <UniversalAdId idRegistry="Adsmood">{ad_id}</UniversalAdId>',
        '          <Linear>',
        '            <TrackingEvents>',
        '              <Tracking event="start"><![CDATA[https://adsmood.com/track/start]]></Tracking>',
        '            </TrackingEvents>',
        '            <MediaFiles>',
    ]
    for platform, filepath in media_files.items():
        params = PLATFORMS[platform]
        mime = "video/quicktime" if params["container"] == "mov" else "video/mp4"
        width, height = params["resolution"].split("x")
        vast_parts.append(
            f'              <MediaFile delivery="progressive" type="{mime}" width="{width}" height="{height}"><![CDATA[/exports/{os.path.basename(filepath)}]]></MediaFile>'
        )

    vast_parts.extend([
        '            </MediaFiles>',
        '          </Linear>',
        '        </Creative>',
        '      </Creatives>',
        '      <AdVerifications>',
    ])
    for platform, params in PLATFORMS.items():
        vast_parts.extend([
            f'        <Verification vendor="{params["sdk_vendor"]}">',
            '          <JavaScriptResource apiFramework="omid" browserOptional="true">',
            f'            <![CDATA[{params["sdk_url"]}]]>',
            '          </JavaScriptResource>',
            '        </Verification>',
        ])
    vast_parts.extend([
        '      </AdVerifications>',
        '      <Extensions>',
        '        <Extension type="in-video">',
        f'          <Button text="{button_text}" color="{button_color}" url="{button_url}" />',
        '        </Extension>',
        '      </Extensions>',
        '    </InLine>',
        '  </Ad>',
        '</VAST>',
    ])
    return "\n".join(vast_parts)

@app.post("/process_and_download")
async def process_and_download(
    video_file: UploadFile = File(...),
    button_text: str = Form(...),
    button_color: str = Form(...),
    button_url: str = Form(...),
):
    """Procesa el video y genera los formatos exportados junto con el archivo VAST."""
    # Guardar el archivo subido
    filename = video_file.filename
    upload_path = os.path.join(UPLOAD_DIR, filename)
    async with aiofiles.open(upload_path, "wb") as out_file:
        while content := await video_file.read(1024 * 1024):
            await out_file.write(content)

    logger.info(f"Archivo subido y guardado en: {upload_path}")

    # Simulación de generación de archivos exportados por plataforma
    media_files = {}
    for platform, params in PLATFORMS.items():
        output_filename = f"{os.path.splitext(filename)[0]}_{platform}.{params['container']}"
        output_filepath = os.path.join(EXPORT_DIR, output_filename)
        shutil.copy(upload_path, output_filepath)  # Simula una conversión
        media_files[platform] = output_filepath
        logger.info(f"Archivo exportado: {output_filepath}")

    # Generar el archivo VAST
    vast_content = generate_vast_xml(
        media_files=media_files,
        button_text=button_text,
        button_color=button_color,
        button_url=button_url,
    )
    vast_filename = f"{os.path.splitext(filename)[0]}_vast.xml"
    vast_filepath = os.path.join(EXPORT_DIR, vast_filename)
    async with aiofiles.open(vast_filepath, "w", encoding="utf-8") as vast_file:
        await vast_file.write(vast_content)

    logger.info(f"Archivo VAST generado: {vast_filepath}")

    # Descargar el archivo VAST generado
    return JSONResponse({
        "vast_url": f"/exports/{vast_filename}",
        "media_files": [f"/exports/{os.path.basename(path)}" for path in media_files.values()]
    })

# Punto de entrada para ejecutar la aplicación
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
