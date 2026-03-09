FROM python:3.11-slim

WORKDIR /app

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the Gensim model during the build phase
# This ensures fast startup time when running the container
COPY src/preload_model.py ./src/
RUN python src/preload_model.py

# Copy the application code
COPY src/ ./src/

# Expose the application port
EXPOSE 5005

# Set working directory to where the app is
WORKDIR /app/src

# Command to run the application using Gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5005", "--workers", "1", "app:app"]
