FROM python:3.11-slim

WORKDIR /app

# Install Tesseract OCR Engine and other dependencies
RUN apt-get update && \
    apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-hun \
    tesseract-ocr-eng \
    libtesseract-dev \
    poppler-utils && \
    apt-get clean

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt
# playwright is not used in the current context, commenting out to speed up builds
# RUN playwright install --with-deps

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 