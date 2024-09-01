FROM python:3.12-slim

LABEL maintainer="dockhardman <f1470891079@gmail.com>"

# Install System Dependencies
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
    git nano vim wget curl htop ca-certificates build-essential && \
    python -m pip install --upgrade pip

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python - && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Install Dependencies
WORKDIR /
COPY ./pyproject.toml ./poetry.lock* /
RUN poetry install --no-root && poetry show

# Application
COPY ./fastapi_chat /fastapi_chat
COPY ./prestart.sh ./start.sh /
RUN chmod +x /prestart.sh /start.sh

ENTRYPOINT ["bash", "-c", "/prestart.sh && /start.sh"]
