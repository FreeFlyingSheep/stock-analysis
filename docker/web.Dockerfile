FROM node:25.2-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y curl

ENV CI=true

RUN npm i -g pnpm

COPY . .

WORKDIR /app/ui

FROM base AS prod-deps
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --prod --frozen-lockfile

FROM base AS build

RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile
RUN pnpm run build

FROM build AS runtime

ENV NODE_ENV=production

COPY --from=prod-deps /app/ui/node_modules /app/ui/node_modules
COPY --from=build /app/ui/build /app/ui/build

CMD ["node", "build"]
