# ---------------------------------------------------
# Stage 1: Build environment (Node.js)
# ---------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Cache package dependencies
COPY package*.json ./
RUN npm ci

COPY . .

# Build Vite application (automatically reads .env.production)
RUN npm run build

# ---------------------------------------------------
# Stage 2: Production environment (Nginx)
# ---------------------------------------------------
FROM nginx:alpine

# Remove default Nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom Nginx template
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Copy built artifacts to Nginx html folder
COPY --from=builder /app/dist /usr/share/nginx/html

# Default port for Cloud Run (overridden by Cloud Run at runtime)
ENV PORT=8080

EXPOSE 8080

# The default entrypoint in nginx:alpine automatically runs envsubst
# on /etc/nginx/templates/*.template and outputs to /etc/nginx/conf.d/
CMD ["nginx", "-g", "daemon off;"]


