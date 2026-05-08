FROM python:3.12-slim

WORKDIR /

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir google-api-python-client google-auth

COPY upload.py .

ENTRYPOINT [ "python", "upload.py" ]