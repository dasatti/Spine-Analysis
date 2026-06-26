#!/bin/sh
set -eu

cp /etc/caddy/Caddyfile.base /etc/caddy/Caddyfile

if [ -n "${CADDY_DOMAIN:-}" ] && [ -n "${ACME_EMAIL:-}" ]; then
  cat >> /etc/caddy/Caddyfile <<EOF

${CADDY_DOMAIN} {
    tls ${ACME_EMAIL}
    import routes
}
EOF
fi

exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
