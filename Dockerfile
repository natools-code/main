FROM python:3.11-slim

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps (if needed) and clean up
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       gcc libffi-dev build-essential \
       iputils-ping traceroute iproute2 netcat-traditional \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

# Copy app files
COPY main.py /app

# Create non-root user and switch
RUN useradd --create-home --shell /bin/bash appuser || true
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

# Run the NiceGUI app (main.py uses ui.run)
CMD ["python", "main.py"]
