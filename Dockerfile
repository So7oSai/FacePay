FROM python:3.9-slim

# Install system dependencies required for dlib, OpenCV, and face_recognition
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the port Flask runs on (Railway will use PORT env var)
EXPOSE 5000 

# Command to run the application using Gunicorn (recommended for production)
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
# For Railway, it often uses the PORT environment variable, which app.py now handles.
# The CMD in app.py (app.run) is fine for development or if Railway injects its own start command.
# If using Gunicorn, ensure it's in requirements.txt and app.py's __main__ block might not be used by Docker CMD.
# For Railway, the Procfile or Docker CMD can specify how to run.
# Let's use a simple CMD for now, Railway might override or use Procfile.
CMD ["python", "app.py"]