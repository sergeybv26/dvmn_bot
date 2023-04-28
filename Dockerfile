FROM python:3.9.13-alpine
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt /opt/dvmn_bot/requirements.txt
WORKDIR /opt/dvmn_bot
RUN pip3 install -r requirements.txt
COPY . /opt/dvmn_bot
CMD ["python3", "main.py"]
