FROM python:3.9-slim
WORKDIR /app
COPY src ./src
COPY pyproject.toml .
COPY requirements.txt .
COPY README.md .

RUN pip install .

EXPOSE 8800

CMD ["uvicorn", "src.anki_convo_api.main:app",  "--host", "0.0.0.0", "--port", "8800"]
