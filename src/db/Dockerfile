FROM postgres:15-alpine

COPY --chown=postgres:postgres flag.txt /flag.txt
COPY --chown=postgres:postgres init.sh /docker-entrypoint-initdb.d/init.sh

RUN chmod 400 /flag.txt && \
    chmod 500 /docker-entrypoint-initdb.d/init.sh

USER postgres