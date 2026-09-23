FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
ARG INSTALL_MODEL_DEPS=false
RUN if [ "$INSTALL_MODEL_DEPS" = "true" ]; then \
      pip install --no-cache-dir '.[models]'; \
    else \
      pip install --no-cache-dir .; \
    fi
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
