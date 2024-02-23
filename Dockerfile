FROM python:3.9-slim
WORKDIR /app
RUN pip install --upgrade pip

COPY src ./
COPY requirements.lock .

RUN sed '/-e/d' requirements.lock > requirements.txt
RUN pip install -r requirements.txt

EXPOSE 8800

CMD ["uvicorn", "phrasify_api.main:app",  "--host", "0.0.0.0", "--port", "8800"]
