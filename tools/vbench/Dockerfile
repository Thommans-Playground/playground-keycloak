# vbench as a container: the CLI, plus the optional dashboard and MCP server, with git so it can read the branch and commit
# documentation. One image, three ways to use it (the project is mounted at /project):
#
#   docker build -t vbench .
#   docker run --rm -i --user "$(id -u):$(id -g)" -v "$PWD:/project" vbench check          # the CLI
#   docker run -i --rm --user "$(id -u):$(id -g)" -v "$PWD:/project" vbench mcp --write    # for Claude Code, over MCP
#   PROJECT=/path/to/project docker compose up --build                                    # the dashboard (docker-compose.yml)
#
# Only vbench's own gates run in here (links, criteria, rungs, diagrams, docs); the project's test, lint and type
# commands need the project's own toolchain, so they stay on the host. `vbench update` needs the host too.

FROM node:22-alpine AS ui
WORKDIR /ui
COPY src/vbench/ui/package.json src/vbench/ui/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY src/vbench/ui/ ./
RUN npm run build

FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/* \
 # the mounted project belongs to the host user, not whoever git thinks it is
 && git config --system --add safe.directory '*'

WORKDIR /src
COPY pyproject.toml README.md ./
COPY src ./src
# EXTRAS=agent or openai adds the optional SDKs for the dashboard's agents; the CLI and MCP server need none
ARG EXTRAS=""
RUN pip install --no-cache-dir ".${EXTRAS:+[$EXTRAS]}" && rm -rf /src/build

# the built dashboard, which `vbench serve` serves
COPY --from=ui /ui/dist /opt/vbench-ui

# run as any uid (--user): give it a home it can write to, and leave the project as the working directory
ENV HOME=/tmp PYTHONUNBUFFERED=1 VBENCH_UI_DIST=/opt/vbench-ui
WORKDIR /project
EXPOSE 3000
ENTRYPOINT ["vbench"]
CMD ["--help"]
