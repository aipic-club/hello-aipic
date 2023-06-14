FROM pipenv:latest 
WORKDIR /www
COPY Pipfile Pipfile.lock /www/
RUN pipenv install --system --deploy --ignore-pipfile
COPY . /www/