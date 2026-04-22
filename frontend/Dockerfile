# ============================================================
# RentalApp Frontend — Multi-stage Dockerfile
# Stage 1: Build  →  Stage 2: Minimal production image
# 
# BACKEND_URL is NOT baked in at build time.
# It is injected at container startup via:
#   - docker run -e BACKEND_URL=http://...
#   - Kubernetes ConfigMap (see k8s/frontend-configmap.yaml)
# ============================================================

# ── Stage 1: Builder ─────────────────────────────────────
FROM node:22-alpine AS builder
WORKDIR /app

# Install deps first (layer cache)
COPY package*.json ./
RUN npm ci --frozen-lockfile

# Copy source and build
COPY . .

# Build with standalone output (no runtime node_modules needed)
# BACKEND_URL must NOT be NEXT_PUBLIC_ — it's never baked in
RUN npm run build

# ── Stage 2: Runner ───────────────────────────────────────
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000

# Non-root user for security
RUN addgroup --system --gid 1001 nodejs \
 && adduser  --system --uid 1001 nextjs

# Copy only the standalone output
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static    ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public          ./public

USER nextjs

EXPOSE 3000

# BACKEND_URL is read at runtime from env — no rebuild needed!
CMD ["node", "server.js"]
