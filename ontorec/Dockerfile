FROM python:3.10.9-slim-buster as base

# Prevent writing .pyc files on the import of source modules
# and set unbuffered mode to ensure logging outputs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set up system and install openjdk 11
RUN apt update \
    && apt install openjdk-11-jdk -y

# Set up GIT
RUN apt-get -y install git

# Set working directory
WORKDIR /app

    
# Install requirements
COPY ./requirements.txt . 
RUN pip install -q --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org --upgrade pip
RUN pip install -q --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt


################# DEVELOPMENT ####################################
FROM base as development
RUN pip install -q --trusted-host pypi.org --trusted-host files.pythonhosted.org bandit pylint safety mypy pytest pytest-cov
COPY . .

# Run static security check and linters
#RUN bandit -r app \
#  && safety check -r requirements.txt --bare  
  # && pylint app \
  # && mypy app 

# Run pytest with code coverage
# RUN pytest --cov app tests/

# Run with reload option
CMD hypercorn wsgi:app --bind 0.0.0.0:8080 --reload --log-level $ONTOREC_LOG_LEVEL
EXPOSE 8080


################# PRODUCTION ####################################
FROM base as production
COPY . .

# Run app
CMD hypercorn wsgi:app --bind 0.0.0.0:80 --log-level $ONTOREC_LOG_LEVEL
EXPOSE 80