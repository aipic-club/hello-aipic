FROM registry.baidubce.com/miss-journey/pipenv:latest
WORKDIR /www
COPY Pipfile Pipfile.lock /www/
RUN pipenv install --deploy --ignore-pipfile
COPY . /www/