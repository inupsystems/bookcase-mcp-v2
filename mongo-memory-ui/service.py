from db import db
import unicodedata
from datetime import datetime

def list_project_ids():
    return db.project_context.distinct("project_id")

def get_last_tags(project_id):
    doc = db.project_context.find({"project_id": project_id}).sort("_id", -1).limit(1)
    for d in doc:
        return d.get("tags", [])
    return []

def normalize_text(text):
    # Remove acentos e deixa minúsculo
    nfkd = unicodedata.normalize('NFKD', text)
    only_ascii = nfkd.encode('ASCII', 'ignore').decode('ASCII')
    return only_ascii.lower()

def insert_project_context(project_id, tags, context_type, context_content):
    normalized_content = normalize_text(context_content)
    current_time = datetime.utcnow()
    doc = {
        "project_id": project_id,
        "tags": tags,
        "context_type": context_type,
        "context_content": normalized_content,
        "created_at": current_time,
        "updated_at": current_time
    }
    return db.project_context.insert_one(doc)
