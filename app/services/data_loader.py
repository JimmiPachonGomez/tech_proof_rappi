

from google.cloud import bigquery
from app.utils.config import BIGQUERY_TABLE
from app.utils.logger import logger



class DataLoader:

    def __init__(self):

        self.big_query_client = bigquery.Client()
    
    def upload_data(self, payloads):
        table_id = BIGQUERY_TABLE
        batch_size = 200
        total_payloads = len(payloads)
        
        logger.info(f"Iniciando carga de {total_payloads} registros")

        for i in range(0, total_payloads, batch_size):
            chunk = payloads[i : i + batch_size]
            
           
            errors = self.big_query_client.insert_rows_json(table_id, chunk)
                
            if errors == []:
                logger.info(f"Datos de lote {i//batch_size + 1} correctamente cargados en BigQuery ({len(chunk)} filas)")
            else:
                logger.error(f"Errores en el lote que inicia en el índice {i}: {errors}")
