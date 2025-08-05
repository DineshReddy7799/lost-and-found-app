# Stage 1: Build stage
FROM python:3.12-slim-bookworm as builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /app

# Install system dependencies needed for PostGIS/GDAL
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libgdal-dev

# Install python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# Stage 2: Final production stage
FROM python:3.12-slim-bookworm

WORKDIR /app

# Install only the necessary runtime system libraries
RUN apt-get update && apt-get install -y --no-install-recommends libgdal-dev && rm -rf /var/lib/apt/lists/*

# Copy python dependencies from the builder stage
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy your project code
COPY . .

# Run collectstatic
RUN python manage.py collectstatic --no-input

# Expose the port your server will run on
EXPOSE 8000

# The command to start the Gunicorn web server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "lostandfound.wsgi"]