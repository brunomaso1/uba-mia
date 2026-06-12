ARG KEYCLOAK_VERSION=26.6.0
FROM quay.io/keycloak/keycloak:${KEYCLOAK_VERSION}

COPY realm-export.json /opt/keycloak/data/import/realm-export.json

ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]
CMD ["start-dev", "--import-realm"]
