FROM node:25.2-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl

ENV NODE_ENV=production
ENV CI=true

RUN npm i -g pnpm

COPY . .

WORKDIR /app/ui

RUN pnpm install --frozen-lockfile
RUN pnpm run build

CMD ["node", "build"]
