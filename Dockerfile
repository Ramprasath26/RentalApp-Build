# ── Build stage ───────────────────────────────────────────────────────────────
# Separate builder so gcc/musl-dev don't end up in the final image.
# Alpine has no manylinux wheels for Pillow, so we compile from source here.
FROM python:3.12-alpine AS builder

WORKDIR /build

RUN apk add --no-cache \
        gcc \
        musl-dev \
        jpeg-dev \
        zlib-dev \
        libffi-dev

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-alpine

LABEL org.opencontainers.image.title="RentalApp-Build" \
      org.opencontainers.image.description="Production Django microservice for rental property management"

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    PORT=8000

# Runtime-only native libs
RUN apk add --no-cache libjpeg-turbo \
    && addgroup -S appgroup \
    && adduser -S appuser -G appgroup

# Copy compiled packages from builder
COPY --from=builder /install /usr/local

# Copy application sources
COPY backend/ .
COPY logo.png ./logo.png
COPY entrypoint.sh ./entrypoint.sh

RUN mkdir -p media staticfiles \
    && chmod +x ./entrypoint.sh \
    && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
