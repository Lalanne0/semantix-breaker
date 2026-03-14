FROM python:3.11-slim

WORKDIR /app

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Generate the French model during build (downloads ~800 MB, extracts top 60k words)
COPY src/extract_fr_model.py ./src/
RUN python src/extract_fr_model.py

# Copy the application code
COPY src/ ./src/

# Expose the application port
EXPOSE 5005

# Set working directory to where the app is
WORKDIR /app/src

# Command to run the application using Gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5005", "--workers", "1", "app:app"]
