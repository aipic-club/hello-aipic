FROM python:3.11.2-slim-buster

ENV HOME /root
WORKDIR /root

COPY . .

RUN pip install -r requirements.txt

EXPOSE 8000

CMD python main.py