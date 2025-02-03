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

def get_mime_type(container: str) -> str:
    """Devuelve el MIME type según el contenedor."""
    return "video/quicktime" if container.lower() == "mov" else "video/mp4"

def convert_video(input_filepath: str, output_filepath: str, codec: str, resolution: str, bitrate: str, container: str):
    """Ejecuta FFmpeg para convertir el video según los parámetros dados."""
    command = [
        "ffmpeg",
        "-i", input_filepath,
        "-c:v", codec,
        "-b:v", bitrate,
        "-s", resolution,
        "-y",  # Sobrescribir sin preguntar
        output_filepath
    ]
    logger.info(f"Ejecutando comando: {' '.join(command)}")
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info(f"Conversión exitosa: {output_filepath}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error al convertir video: {e.stderr.decode('utf-8')}")
        raise

def generate_vast_xml(platforms: dict, interactive_type: str, interactive_data: dict, media_files: dict) -> str:
    """
    Genera un VAST 4.2 válido con la siguiente estructura:
      - <Impression> obligatorio.
      - <Creatives> con un <Creative> que contiene un bloque <Linear>
        que incluye <TrackingEvents> y <MediaFiles>.
      - <UniversalAdId> se genera colocando el ID como contenido interno.
      - <AdVerifications> y <Extensions> para interactividad.
    """
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
        '            <MediaFiles>'
    ]
    
    # Agregar los MediaFiles para cada plataforma convertida
    for platform, filepath in media_files.items():
        params = platforms[platform]
        mime = get_mime_type(params["container"])
        width, height = params["resolution"].split("x")
        file_url = f"/exports/{os.path.basename(filepath)}"
        vast_parts.append(
            f'              <MediaFile delivery="progressive" type="{mime}" width="{width}" height="{height}"><![CDATA[{file_url}]]></MediaFile>'
        )
    
    vast_parts.extend([
        '            </MediaFiles>',
        '          </Linear>',
        '        </Creative>',
        '      </Creatives>',
        '      <AdVerifications>'
    ])
    
    # Agregar las verificaciones (solo para plataformas con conversión)
    for platform, params in platforms.items():
        if platform in media_files:
            vast_parts.extend([
                f'        <Verification vendor="{params["sdk_vendor"]}">',
                '          <JavaScriptResource apiFramework="omid" browserOptional="true">',
                f'            <![CDATA[{params["sdk_url"]}]]>',
                '          </JavaScriptResource>',
                '        </Verification>'
            ])
    
    vast_parts.extend([
        '      </AdVerifications>',
        '      <Extensions>'
    ])
    
    # Agregar la interactividad según el tipo
    if interactive_type == "in_video":
        vast_parts.extend([
            '        <Extension type="in-video">',
            f'          <Button text="{interactive_data.get("button_text", "")}" color="{interactive_data.get("button_color", "")}" url="{interactive_data.get("button_url", "")}" />',
            '        </Extension>'
        ])
    elif interactive_type == "trivia":
        vast_parts.extend([
            '        <Extension type="trivia">',
            f'          <Question text="{interactive_data.get("question", "")}">',
            f'            <Option text="{interactive_data.get("option1_text", "")}" url="{interactive_data.get("option1_url", "")}" />',
            f'            <Option text="{interactive_data.get("option2_text", "")}" url="{interactive_data.get("option2_url", "")}" />',
            '          </Question>',
            '        </Extension>'
        ])
    elif interactive_type == "qr_scan":
        vast_parts.extend([
            '        <Extension type="qr-scan">',
            f'          <QRCode url="{interactive_data.get("qr_url", "")}" size="{interactive_data.get("qr_size", "")}" position="{interactive_data.get("qr_position", "")}" />',
            '        </Extension>'
        ])
    
    vast_parts.extend([
        '      </Extensions>',
        '    </InLine>',
        '  </Ad>',
        '</VAST>'
    ])
    
    vast_xml = "\n".join(vast_parts)
    return vast_xml

def process_video_and_generate_vast(input_filepath: str, original_filename: str, interactive_type: str, interactive_data: dict) -> dict:
    """
    Convierte el video para cada plataforma y genera el archivo VAST válido.
    Devuelve un diccionario con la ruta del archivo VAST y las rutas de los videos convertidos.
    """
    media_files = {}
    
    # Convertir el video para cada plataforma definida
    for platform, params in PLATFORMS.items():
        output_filename = f"{os.path.splitext(original_filename)[0]}_{platform}.{params['container']}"
        output_filepath = os.path.join(EXPORT_DIR, output_filename)
        try:
            convert_video(
                input_filepath=input_filepath,
                output_filepath=output_filepath,
                codec=params["codec"],
                resolution=params["resolution"],
                bitrate=params["bitrate"],
                container=params["container"]
            )
            media_files[platform] = output_filepath
        except Exception as e:
            logger.error(f"Fallo en la conversión para {platform}: {e}")
    
    # Generar el XML VAST con la nueva estructura
    vast_content = generate_vast_xml(PLATFORMS, interactive_type, interactive_data, media_files)
    vast_filename = f"interactive_vast_{os.path.splitext(original_filename)[0]}.xml"
    vast_filepath = os.path.join(EXPORT_DIR, vast_filename)
    with open(vast_filepath, "w", encoding="utf-8") as f:
        f.write(vast_content)
    logger.info(f"Archivo VAST generado: {vast_filepath}")
    
    return {"vast_file": vast_filepath, "media_files": media_files}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Renderiza la página principal con el formulario."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def upload_video(
    request: Request,
    background_tasks: BackgroundTasks,
    video_file: UploadFile = File(...),
    interactivity: str = Form(...),
    # Campos para in-video
    button_text: str = Form(None),
    button_color: str = Form(None),
    button_url: str = Form(None),
    # Campos para trivia
    question: str = Form(None),
    option1_text: str = Form(None),
    option1_url: str = Form(None),
    option2_text: str = Form(None),
    option2_url: str = Form(None),
    # Campos para qr-scan
    qr_url: str = Form(None),
    qr_size: str = Form(None),
    qr_position: str = Form(None)
):
    # Guardar el archivo subido
    filename = video_file.filename
    upload_path = os.path.join(UPLOAD_DIR, filename)
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)
    logger.info(f"Archivo subido: {upload_path}")
    
    # Recopilar los datos de interactividad según el tipo seleccionado
    interactive_data = {}
    if interactivity == "in_video":
        interactive_data = {
            "button_text": button_text,
            "button_color": button_color,
            "button_url": button_url
        }
    elif interactivity == "trivia":
        interactive_data = {
            "question": question,
            "option1_text": option1_text,
            "option1_url": option1_url,
            "option2_text": option2_text,
            "option2_url": option2_url
        }
    elif interactivity == "qr_scan":
        interactive_data = {
            "qr_url": qr_url,
            "qr_size": qr_size,
            "qr_position": qr_position
        }
    
    # Procesar video y generar el VAST (aquí se ejecuta de forma sincrónica)
    result = process_video_and_generate_vast(upload_path, filename, interactivity, interactive_data)
    vast_file_url = f"/exports/{os.path.basename(result['vast_file'])}"
    
    return templates.TemplateResponse("result.html", {"request": request, "vast_file_url": vast_file_url, "media_files": result["media_files"]})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
