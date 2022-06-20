FROM python:3.9

COPY postgre postgre
COPY utils utils

WORKDIR postgre

RUN pip install -r requirements.txt

CMD ["python", "main.py"]
