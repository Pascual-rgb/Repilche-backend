import io
import os
from PIL import Image
from supabase import create_client

# 1. Credenciales del PROYECTO VIEJO
OLD_URL = "https://azpnkrkpvhcfpmvzkjro.supabase.co"
OLD_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF6cG5rcmtwdmhjZnBtdnpranJvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTI0OTcyNjgsImV4cCI6MjEwODA3MzI2OH0.iicQ5-L0Q8_Y28XYxgaco91tBW2b68xUF1T5OfaI3jY"
OLD_BUCKET = "productos"

# 2. Credenciales del PROYECTO NUEVO (sanitizamos la URL base removiendo '/rest/v1/')
NEW_URL = "https://smcfpoyqbhnrxguevujj.supabase.co/rest/v1/".replace("/rest/v1/", "").rstrip("/")
NEW_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNtY2Zwb3lxYmhucnhndWV2dWpqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5NDI1Mjc3NCwiZXhwIjoyMTA5ODI4Nzc0fQ.LXJf-nT1OpVWjZezb-ZXiEOwzsZJtH1dAjcyNn4gt6A"
NEW_BUCKET = "productos"

old_client = create_client(OLD_URL, OLD_KEY)
new_client = create_client(NEW_URL, NEW_KEY)


def optimizar_imagen(buffer_bytes):
    img = Image.open(io.BytesIO(buffer_bytes))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    max_size = 1080
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    salida = io.BytesIO()
    img.save(salida, format="WEBP", quality=80, optimize=True)
    return salida.getvalue()


print("--- OBTENIENDO LISTADO DE IMAGENES DEL VIEJO SUPABASE ---")
# Usamos limit=1000 para obtener todos los archivos (por defecto Supabase limita a 100)
archivos = old_client.storage.from_(OLD_BUCKET).list("prendas", {"limit": 1000})
print(f"Total archivos detectados: {len(archivos)}")

exitosos = 0
omitidos = 0
fallidos = 0

for idx, arch in enumerate(archivos, 1):
    nombre = arch["name"]
    if nombre == ".emptyFolderPlaceholder":
        omitidos += 1
        continue

    ruta = f"prendas/{nombre}"
    print(f"[{idx}/{len(archivos)}] Procesando: {nombre}...")
    try:
        raw_data = old_client.storage.from_(OLD_BUCKET).download(ruta)
        opt_data = optimizar_imagen(raw_data)

        new_client.storage.from_(NEW_BUCKET).upload(
            path=ruta,
            file=opt_data,
            file_options={"content-type": "image/webp", "upsert": "true"},
        )
        print(f"  OK -> Optimizado a {len(opt_data) // 1024} KB y migrado")
        exitosos += 1
    except Exception as e:
        print(f"  Error en {nombre}: {e}")
        fallidos += 1

print("\n--- PROCESO FINALIZADO ---")
print(f"Exitosos: {exitosos} | Omitidos: {omitidos} | Fallidos: {fallidos}")

