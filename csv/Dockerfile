FROM python:3.9-slim-bullseye

COPY csv csv 
COPY utils utils

WORKDIR csv 

RUN pip install -r requirements.txt

CMD ["python", "main.py"]
