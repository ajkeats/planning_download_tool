FROM python:3.11

RUN pip install -U pip

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

ENV PORT=

COPY . /app
WORKDIR /app

CMD streamlit run app.py --server.port=${PORT} --browser.serverAddress="0.0.0.0"
