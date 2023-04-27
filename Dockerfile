FROM python:3.10
# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /www
COPY . /www

RUN pip install pipenv
RUN pipenv install --system --deploy --ignore-pipfile
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "80"]