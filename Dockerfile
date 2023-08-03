FROM python:3.10-slim-buster
LABEL authors="plux"

WORKDIR /app
VOLUME /app/data
EXPOSE 5000

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]