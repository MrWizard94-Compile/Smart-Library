FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY smart_code_lib/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY smart_code_lib/ smart_code_lib/

EXPOSE 8000

CMD ["uvicorn", "smart_code_lib.main:app", "--host", "0.0.0.0", "--port", "8000"]