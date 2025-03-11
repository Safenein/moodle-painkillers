# Étape de construction
FROM python:3.12-alpine AS builder

WORKDIR /app
COPY dist/*.whl .

# Installation dans un environnement virtuel
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
RUN pip install --no-cache-dir *.whl

# Étape finale
FROM python:3.12-alpine AS runtime

WORKDIR /app
COPY --from=builder /venv /venv

ENV PATH="/venv/bin:$PATH"
CMD ["python", "-m", "moodle_painkillers"]
