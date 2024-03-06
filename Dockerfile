FROM python:3.9-slim
WORKDIR /app
COPY requirements/app.txt ./requirements/app.txt
RUN pip install -r requirements/app.txt
COPY src .

EXPOSE 8800

CMD ["uvicorn", "phrasify_api.main:app",  "--host", "0.0.0.0", "--port", "8800"]
