# 阶段一：构建 React 应用
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# 阶段二：用 Nginx 托管静态文件
FROM nginx:alpine
# 拷贝打包后的文件到 Nginx 目录
COPY --from=build /app/dist /usr/share/nginx/html

# 拷贝我们自定义的 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]