# Multi-stage Dockerfile for ContentForge AI / DocLink Frontend

# ==========================================
# Stage 1: Build React SPA bundle
# ==========================================
FROM node:20-alpine AS build-stage

WORKDIR /app

# Copy package descriptors
COPY package*.json ./

# Clean install dependencies
RUN npm ci

# Build argument for backend API URL (defaults to localhost:8000 for browser access)
ARG VITE_BACKEND_URL=http://localhost:8000
ENV VITE_BACKEND_URL=${VITE_BACKEND_URL}
ENV VITE_API_BASE_URL=${VITE_BACKEND_URL}

# Copy frontend source code
COPY . .

# Build production bundle
RUN npm run build

# ==========================================
# Stage 2: Production Nginx web server
# ==========================================
FROM nginx:alpine AS serve-stage

# NOTE FOR FUTURE ENHANCEMENT:
# If API base URL needs to change at runtime without rebuilding container images,
# an entrypoint.sh can be added to run envsubst on a template config.js placed
# in /usr/share/nginx/html before launching nginx.

# Copy static built assets from build stage
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
