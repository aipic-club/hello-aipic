FROM pipenv:latest
WORKDIR /www
COPY Pipfile Pipfile.lock /www/
RUN pipenv install --system --deploy --ignore-pipfile
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "80"]