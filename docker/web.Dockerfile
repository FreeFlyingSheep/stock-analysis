FROM node:25.2-slim

WORKDIR /app

ENV NODE_ENV=production
ENV CI=true

RUN npm i -g pnpm

COPY . .

WORKDIR /app/ui

RUN pnpm install --frozen-lockfile
RUN pnpm run build

EXPOSE 3000

CMD ["node", "build"]
