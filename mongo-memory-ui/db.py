from pymongo import MongoClient
import os

# Prioriza a variável de ambiente MONGO_URI, se definida. Caso contrário, usa o valor padrão.
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://admin:admin123@localhost:27018/dev_memory_db")
DB_NAME = "dev_memory_db"

# A URI já pode conter o nome do banco de dados, então a conexão é feita diretamente.
client = MongoClient(MONGO_URI)
db = client.get_database() # Obtém o banco de dados a partir da URI

# Se o nome do banco de dados não estiver na URI, você pode descomentar a linha abaixo
# db = client[DB_NAME]
