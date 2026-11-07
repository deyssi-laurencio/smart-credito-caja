import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
import cohere

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
SUPABASE_KEY = "sb_publishable_dEigapyyWGQy16LThl_yiA_qhm3TNZ3" 

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Inicializar cliente de la API de IA (COHERE CORRECTO)
cohere_client = cohere.Client(api_key="cohere_2mVpFTauX86YpLuWs5mS0vp1BqylZo25EfCbUfmp2GNBMV")

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
        evaluacion_preliminar = "Favorable (Cuota dentro del 40% de los ingresos declarados)"
    else:
        estado = "Rechazado"
        evaluacion_preliminar = "Desfavorable (Supera el ratio de endeudamiento permitido del 40%)"

    # Generación de dictamen con la API de Cohere (command-r-08-2024)
    try:
        prompt_sistema = (
            "Eres un analista de riesgos senior para una Caja de Ahorro y Crédito. "
            "Redacta un dictamen crediticio formal y un análisis de riesgo breve justificando la decisión."
        )
        prompt_usuario = (
            f"Cliente: {solicitud.nombre_cliente}, DNI: {solicitud.dni}\n"
            f"Ingresos mensuales: {solicitud.ingresos_mensuales}\n"
            f"Monto solicitado: {solicitud.monto_solicitado} (Cuota estimada: {cuota_estimada:.2f})\n"
            f"Motivo: {solicitud.motivo_prestamo}\n"
            f"Evaluación del sistema: {estado}. {evaluacion_preliminar}"
        )

        response = cohere_client.chat(
            model="command-r-08-2024",
            message=prompt_usuario,
            preamble=prompt_sistema,
            temperature=0.3
        )
        dictamen = response.text
    except Exception as e:
        dictamen = f"Dictamen automático por reglas: {evaluacion_preliminar}. (Nota Cohere: {str(e)})"

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
    
    response_db = supabase.table("solicitudes_credito").insert(data).execute()
    
    return {
        "mensaje": "Evaluación con Cohere procesada y guardada en Supabase con éxito",
        "estado": estado,
        "dictamen": dictamen,
        "detalles": response_db.data
    }

@app.get("/solicitudes")
def listar_solicitudes():
    response = supabase.table("solicitudes_credito").select("*").execute()
    return response.data
