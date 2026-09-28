FROM node:20-bookworm-slim AS frontend-builder
WORKDIR /app/frontend

COPY comic-encryption-app-design/package.json ./
RUN npm install

COPY comic-encryption-app-design ./
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    NEXT_PUBLIC_API_URL=http://localhost:8000 \
    HOSTNAME=0.0.0.0

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg netpbm curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
COPY --from=frontend-builder /app/frontend/.next /app/comic-encryption-app-design/.next
COPY --from=frontend-builder /app/frontend/public /app/comic-encryption-app-design/public
COPY --from=frontend-builder /app/frontend/node_modules /app/comic-encryption-app-design/node_modules
COPY --from=frontend-builder /app/frontend/package.json /app/comic-encryption-app-design/package.json
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 3000 8000

CMD ["/app/docker-entrypoint.sh"]