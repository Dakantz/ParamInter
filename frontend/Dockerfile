FROM node:24-alpine3.21 AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install -D
COPY . .
RUN npm run build

# production stage
FROM nginx:stable-alpine AS production-stage
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx/nginx.conf /etc/nginx/conf.d
COPY --from=build-stage /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]