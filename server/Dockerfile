FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

COPY server ./server
COPY scripts ./scripts
COPY data ./data
COPY docs ./docs
COPY apps/admin-web/dist ./apps/admin-web/dist

EXPOSE 8000

CMD ["uvicorn", "server.app.admin_main:app", "--host", "0.0.0.0", "--port", "8000"]
