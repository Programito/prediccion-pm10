FROM node:24-bookworm-slim AS frontend
WORKDIR /ui
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN corepack pnpm install --frozen-lockfile
COPY index.html vite.config.ts tsconfig.json ./
COPY src ./src
RUN corepack pnpm run build

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py treated_tables.py provenance.py column_dictionary.py descriptive_statistics.py ./explorer/
COPY --from=frontend /ui/dist ./explorer/dist
ENV PM10_HOST=0.0.0.0 PM10_DATA_ROOT=/workspace
EXPOSE 8066
CMD ["python", "-m", "explorer.server"]
