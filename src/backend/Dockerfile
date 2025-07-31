FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy Poetry configuration files
COPY pyproject.toml ./

# Configure Poetry to not create virtual environment in Docker
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev

# Copy the entire application
COPY . .

# Expose port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]