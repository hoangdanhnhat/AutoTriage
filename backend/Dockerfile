FROM python:3.12-slim

# Install system deps needed by ansible + asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    sshpass \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create artifacts directory
RUN mkdir -p /app/artifacts

# SSH dir for key mount
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
