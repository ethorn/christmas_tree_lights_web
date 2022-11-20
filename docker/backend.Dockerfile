# syntax=docker/dockerfile:1
FROM python:3.8-alpine
WORKDIR /code
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
RUN apk add --no-cache gcc musl-dev linux-headers
COPY ../backend/ .

RUN pip install -r requirements.txt

RUN python3 database/init_db.py

EXPOSE 5000

#CMD ["flask", "run"]