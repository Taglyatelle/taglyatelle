FROM python:3.14.1 AS build_package

COPY . .
RUN make install-prod
RUN make build


FROM python:3.14.1-slim AS production_stage

LABEL org.opencontainers.image.source="https://github.com/alexym1/taglyatelle"

WORKDIR /app

COPY --from=build_package dist/taglyatelle-*-py3-none-any.whl /tmp/pkg/
RUN pip install /tmp/pkg/taglyatelle-*-py3-none-any.whl
RUN rm -rf /tmp/pkg/*

ENV LANG=en_US.UTF-8
ENV LC_CTYPE=en_US.UTF-8

CMD ["uvicorn", "taglyatelle.exposition.taglyatelle_api:app", "--host", "0.0.0.0", "--port", "8000"]
