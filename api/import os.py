import os
import io
from PIL import Image
from supabase import create_client

# Credenciales del PROYECTO VIEJO
OLD_URL = "https://azpnkrkpvhcfpmvzkjro.supabase.co"
OLD_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF6cG5rcmtwdmhjZnBtdnpranJvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTI0OTcyNjgsImV4cCI6MjEwODA3MzI2OH0.iicQ5-L0Q8_Y28XYxgaco91tBW2b68xUF1T5OfaI3jY"  # Token eyJ... del proyecto viejo
OLD_BUCKET = "productos"

# Credenciales del PROYECTO NUEVO
NEW_URL = "https://smcfpoyqbhnrxguevujj.supabase.co/rest/v1/"
NEW_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNtY2Zwb3lxYmhucnhndWV2dWpqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5NDI1Mjc3NCwiZXhwIjoyMTA5ODI4Nzc0fQ.LXJf-nT1OpVWjZezb-ZXiEOwzsZJtH1dAjcyNn4gt6A"                 # Anon o Service Role del proyecto nuevo
NEW_BUCKET = "productos"

old_client = create_client(OLD_URL, OLD_KEY)
new_client = create_client(NEW_URL, NEW_KEY)

def optimizar_imagen(buffer_bytes):
    """Redimensiona y convierte a WebP liviano."""
    img = Image.open(io.BytesIO(buffer_bytes))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    # Redimensionar si supera 1080px de ancho/alto
    max_size = 1080
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    
    salida = io.BytesIO()
    img.save(salida, format="WEBP", quality=80, optimize=True)
    return salida.getvalue()

print("--- OBTENIENDO LISTA DE IMÁGENES DEL STORAGE ANTERIOR ---")
archivos = old_client.storage.from_(OLD_BUCKET).list("prendas")

print(f"Total archivos detectados: {len(archivos)}")

for idx, arch in enumerate(archivos, 1):
    nombre_archivo = arch["name"]
    if nombre_archivo == ".emptyFolderPlaceholder":
        continue

    ruta_origen = f"prendas/{nombre_archivo}"
    print(f"[{idx}/{len(archivos)}] Descargando: {nombre_archivo}...")
    
    try:
        # 1. Descarga del viejo
        datos_crudos = old_client.storage.from_(OLD_BUCKET).download(ruta_origen)
        
        # 2. Compresión
        datos_optimizados = optimizar_imagen(datos_crudos)
        
        # 3. Subida al nuevo Supabase
        new_client.storage.from_(NEW_BUCKET).upload(
            path=ruta_origen,
            file=datos_optimizados,
            file_options={"content-type": "image/webp", "upsert": "true"}
        )
        print(f"  -> Migrado y optimizado con éxito ({len(datos_optimizados) // 1024} KB)")
    except Exception as e:
        print(f"  ❌ Error en {nombre_archivo}: {e}")

print("\n--- TODAS LAS IMÁGENES HAN SIDO OPTIMIZADAS Y MIGRADAS ---")