FROM python:3.13-slim
RUN pip install --no-cache-dir uv
WORKDIR /app
# Commit uv.lock (`uv sync` writes it); --locked fails the build if it is missing or out of date.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
RUN uv sync --locked --no-dev
RUN useradd --system --uid 10001 --no-create-home app
USER app
# Run the virtualenv's uvicorn directly: the runtime needs no uv, and no cache directory.
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "{{PACKAGE}}.main:app", "--host", "0.0.0.0", "--port", "8000"]
