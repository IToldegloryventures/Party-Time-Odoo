#!/usr/bin/env bash
set -euo pipefail

# Helper to run the PTT cleanup sequence and module upgrade during Odoo.sh builds.
# Usage:
#   DB_NAME=<db> scripts/odoo_sh_build.sh
# Optional env:
#   ODOO_BIN (default: odoo/odoo-bin)
#   ODOO_CONF (default: odoo.conf)

DB_NAME="${DB_NAME:-${1:-}}"
if [[ -z "${DB_NAME}" ]]; then
  echo "DB_NAME is required (export DB_NAME or pass as first argument)" >&2
  exit 1
fi

ODOO_BIN="${ODOO_BIN:-odoo/odoo-bin}"
ODOO_CONF="${ODOO_CONF:-odoo.conf}"

echo "[odoo_sh_build] Running cleanup sequence on DB '${DB_NAME}'"
"${ODOO_BIN}" shell -c "${ODOO_CONF}" -d "${DB_NAME}" --load=script scripts/run_ptt_cleanup.py

echo "[odoo_sh_build] Upgrading ptt_business_core to apply migrations"
"${ODOO_BIN}" -c "${ODOO_CONF}" -d "${DB_NAME}" -u ptt_business_core

echo "[odoo_sh_build] Done"
