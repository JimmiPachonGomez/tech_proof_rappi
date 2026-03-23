from dotenv import load_dotenv
import os

load_dotenv()

RAPPI_TOKEN = os.getenv("RAPPI_TOKEN")
BIGQUERY_TABLE = os.getenv("BIGQUERY_TABLE")