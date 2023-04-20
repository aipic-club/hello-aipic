FROM python:3.10
WORKDIR /www
COPY . /www
RUN pip install --no-cache-dir --upgrade -r requirements.txt
CMD ["uvicorn", "mock-server:app", "--host", "0.0.0.0", "--port", "80"]