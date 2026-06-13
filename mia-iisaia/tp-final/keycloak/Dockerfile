# check=skip=InvalidDefaultArgInFrom
ARG KEYCLOAK_VERSION
FROM quay.io/keycloak/keycloak:${KEYCLOAK_VERSION}

COPY realm-export.json /opt/keycloak/data/import/realm-export.json

CMD ["start-dev", "--import-realm"]
