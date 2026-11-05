from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

app = FastAPI(title="SmartCrédito - Caja", version="1.0")

# Permitir conexiones desde la interfaz web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tus credenciales de Supabase
SUPABASE_URL = "https://ndcmdsnxitgggacrngau.supabase.co"
SUPABASE_KEY = "sb_secret_fxnf7cftE1OS9cSaoKvHUw_NZqgdZgy"  # Coloca aquí tu Publishable o Secret key de Supabase

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class SolicitudCredito(BaseModel):
    nombre_cliente: str
    dni: str
    ingresos_mensuales: float
    monto_solicitado: float
    motivo_prestamo: str

@app.post("/evaluar")
def evaluar_credito(solicitud: SolicitudCredito):
    # Lógica de evaluación financiera orientada a Cajas
    cuota_estimada = solicitud.monto_solicitado / 12 
    limite_permitido = solicitud.ingresos_mensuales * 0.40
    
    if cuota_estimada <= limite_permitido:
        estado = "Aprobado"
        dictamen = "La cuota estimada se encuentra dentro del 40% de los ingresos declarados. Viabilidad favorable para microcrédito."
    else:
        estado = "Rechazado"
        dictamen = "La cuota estimada supera el ratio de endeudamiento permitido (40%). Riesgo crediticio elevado."

    # Guardar automáticamente en tu tabla de Supabase
    data = {
        "nombre_cliente": solicitud.nombre_cliente,
        "dni": solicitud.dni,
        "ingresos_mensuales": solicitud.ingresos_mensuales,
        "monto_solicitado": solicitud.monto_solicitado,
        "motivo_prestamo": solicitud.motivo_prestamo,
        "estado": estado,
        "dictamen_ia": dictamen
    }
    
    response = supabase.table("solicitudes_credito").insert(data).execute()
    
    return {
        "mensaje": "Evaluación procesada y guardada en Supabase con éxito",
        "estado": estado,
        "dictamen": dictamen,
        "detalles": response.data
    }

@app.get("/solicitudes")
def listar_solicitudes():
    response = supabase.table("solicitudes_credito").select("*").execute()
    return response.data