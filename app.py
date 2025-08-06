import os
import requests
from fastapi import FastAPI
from pymongo import MongoClient
import pandas as pd
from dotenv import load_dotenv
import uvicorn
import logging
import http.client

# Configuración detallada de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Para debugging de requests (opcional)
http.client.HTTPConnection.debuglevel = 1
requests_log = logging.getLogger("urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

app = FastAPI()
load_dotenv()

# Configuración
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = "drift_db"
COLLECTION_NAME = "incoming_data"
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Validación de configuración
logger.info(f"MongoDB URI: {MONGODB_URI}")
logger.info(f"Slack Webhook URL: {SLACK_WEBHOOK_URL[:30]}...")  # Log parcial por seguridad

# Conectar a MongoDB
try:
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    logger.info("Conexión a MongoDB establecida")
except Exception as e:
    logger.error(f"Error conectando a MongoDB: {str(e)}")
    client = None

# Carga datos de referencia
try:
    reference_data = pd.read_csv("reference_data.csv")
    logger.info(f"Datos de referencia cargados. Columnas: {', '.join(reference_data.columns)}")
    logger.info(f"Ejemplo de datos:\n{reference_data.head(1)}")
except Exception as e:
    logger.error(f"Error cargando datos de referencia: {str(e)}")
    reference_data = pd.DataFrame()

def check_data_drift(current_data):
    """Detección simplificada de drift para un solo registro"""
    if reference_data.empty:
        logger.error("Datos de referencia no disponibles")
        return False, []
    
    drift_detected = False
    drifted_features = []
    
    for col in reference_data.columns:
        # Verificar si la columna existe en los datos actuales
        if col not in current_data.columns:
            logger.warning(f"Columna {col} no encontrada en datos actuales")
            continue
            
        # Para columnas numéricas
        if reference_data[col].dtype.kind in 'fiu':
            ref_mean = reference_data[col].mean()
            ref_std = reference_data[col].std()
            current_val = current_data[col].iloc[0]
            
            # Manejar caso donde std es cero
            if ref_std == 0:
                if current_val != ref_mean:
                    drift_detected = True
                    drifted_features.append(f"{col} (valor fijo: esperado {ref_mean}, recibido {current_val})")
            else:
                z_score = abs(current_val - ref_mean) / ref_std
                if z_score > 3:  # Más de 3 desviaciones estándar
                    drift_detected = True
                    drifted_features.append(f"{col} (z={z_score:.2f})")
        
        # Para columnas categóricas
        else:
            unique_values = reference_data[col].unique()
            current_val = current_data[col].iloc[0]
            
            if current_val not in unique_values:
                drift_detected = True
                drifted_features.append(f"{col} (nuevo valor: {current_val})")
    
    return drift_detected, drifted_features

def send_slack_alert(message):
    """Envía alerta a Slack usando webhook"""
    if not SLACK_WEBHOOK_URL:
        logger.error("SLACK_WEBHOOK_URL no configurado")
        return False
    
    try:
        payload = {"text": message}
        logger.debug(f"Enviando a Slack: {payload}")
        
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 200:
            logger.info("Alerta enviada a Slack exitosamente")
            return True
        else:
            logger.error(f"Error en Slack (código {response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error al enviar a Slack: {str(e)}")
        return False

@app.post("/data/")
async def receive_data(data: dict):
    logger.info(f"Datos recibidos: {data}")
    
    # Insertar en MongoDB si está disponible
    if client:
        try:
            collection.insert_one(data)
            logger.info("Datos insertados en MongoDB")
        except Exception as e:
            logger.error(f"Error insertando en MongoDB: {str(e)}")
    
    # Verificar si tenemos datos de referencia
    if reference_data.empty:
        return {"status": "error", "message": "Datos de referencia no disponibles"}
    
    # Convertir a DataFrame
    try:
        current_df = pd.DataFrame([data])
        logger.info("Datos convertidos a DataFrame")
        
        # Asegurar mismas columnas que referencia
        for col in reference_data.columns:
            if col not in current_df.columns:
                # Valor por defecto según tipo de dato
                if reference_data[col].dtype.kind in 'fiu':
                    current_df[col] = 0
                else:
                    current_df[col] = ""
                logger.warning(f"Columna faltante: {col} - usando valor por defecto")
        
        current_df = current_df[reference_data.columns]
    except Exception as e:
        logger.error(f"Error procesando datos: {str(e)}")
        return {"status": "error", "message": str(e)}
    
    # Verificar drift
    try:
        drift_detected, drifted_features = check_data_drift(current_df)
        logger.info(f"Drift detectado: {drift_detected} - Features: {drifted_features}")
        
        if drift_detected:
            alert_msg = (
                f"🚨 DATA DRIFT DETECTED!\n"
                f"Features drifted: {', '.join(drifted_features)}\n"
                f"Data sample: {data}"
            )
            alert_sent = send_slack_alert(alert_msg)
            return {
                "status": "drift_detected", 
                "alert_sent": alert_sent,
                "drifted_features": drifted_features
            }
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error verificando drift: {str(e)}")
        return {"status": "error", "message": str(e)}

def test_slack_connection():
    """Prueba la conexión con Slack al iniciar"""
    if not SLACK_WEBHOOK_URL:
        logger.error("No se puede probar Slack: SLACK_WEBHOOK_URL no configurado")
        return False
    
    test_msg = "✅ El servicio de monitoreo se ha iniciado correctamente"
    logger.info(f"Probando conexión con Slack: {test_msg}")
    return send_slack_alert(test_msg)

if __name__ == "__main__":
    # Probar conexión con Slack al inicio
    slack_test_result = test_slack_connection()
    logger.info(f"Prueba de Slack: {'Éxito' if slack_test_result else 'Fallo'}")
    
    # Iniciar servidor
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")