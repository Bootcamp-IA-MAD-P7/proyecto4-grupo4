FROM node:20-alpine AS builder

# Receive the API URL from --build-arg and expose it as an env var
# so Vite can read it during `npm run build` and bake it into the bundle.
# Without ARG + ENV here, the --build-arg is silently ignored by Docker
# and import.meta.env.VITE_API_URL compiles as undefined.
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS runner

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
