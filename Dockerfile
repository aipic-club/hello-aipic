FROM python:3.10
# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


WORKDIR /www
COPY . /www
# Upgrade pip then change pip registry
RUN pip install -i https://mirrors.cloud.tencent.com/pypi/simple pip -U
RUN pip config set global.index-url https://mirrors.cloud.tencent.com/pypi/simple

RUN pip install --no-cache-dir -r requirements.txt
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "80"]