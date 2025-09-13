# Dockerfile para mongo-memory-ui
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Exponha a porta se o serviço rodar em uma porta específica (exemplo: 8080)
EXPOSE 7860

CMD ["python3", "main.py"]
