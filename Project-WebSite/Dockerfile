FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates unixodbc-dev g++ \
    && curl -fsSLo /tmp/packages-microsoft-prod.deb https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
    && dpkg -i /tmp/packages-microsoft-prod.deb \
    && apt-get update && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
    && rm -rf /var/lib/apt/lists/* /tmp/packages-microsoft-prod.deb
WORKDIR /app
COPY backend/requirements.txt backend/requirements-lock.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/app backend/app
COPY backend/demo_images backend/demo_images
COPY SQL/ENV09.sql SQL/ENV09.sql
COPY --from=frontend /build/dist frontend/dist
RUN useradd --create-home env09 && mkdir -p backend/storage/uploads && chown -R env09:env09 /app
USER env09
EXPOSE 8000
CMD ["sh", "-c", "python -m backend.app.bootstrap && exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
