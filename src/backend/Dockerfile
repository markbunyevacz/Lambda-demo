FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy only the dependency configuration files to leverage Docker cache
COPY pyproject.toml poetry.lock* ./

# Install dependencies using poetry
# --no-root: don't install the project itself, only dependencies
# --no-interaction: don't ask interactive questions
RUN poetry install --no-root --no-interaction

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# The command to run the application will be specified in docker-compose.yml
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 