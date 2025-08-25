FROM python:3.13-bookworm

WORKDIR /app
ADD requirements.txt /app
RUN pip install -r requirements.txt

WORKDIR /app

ADD . /app

WORKDIR /app/src

CMD [ "python", "-m", "uvicorn", "backend:app", "--port", "8000" ]