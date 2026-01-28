# QA Run Commands (Odoo.sh-aware)

These commands run the full cleanup sequence and upgrade the module. They’re written for Odoo.sh build/post-init hooks and local/staging shells.

## Odoo.sh build/post-init (recommended)

Add this to your Odoo.sh Build (or Post-init) command list for every branch:

```
export DB_NAME=<branch-db-name>  # Odoo.sh usually sets this automatically
export ODOO_BIN=${ODOO_BIN:-odoo/odoo-bin}
export ODOO_CONF=${ODOO_CONF:-odoo.conf}
$ODOO_BIN shell -c $ODOO_CONF -d $DB_NAME --load=script scripts/run_ptt_cleanup.py
$ODOO_BIN -c $ODOO_CONF -d $DB_NAME -u ptt_business_core
```

If you prefer a single call, use the helper script added in `scripts/odoo_sh_build.sh`:

```
DB_NAME=<branch-db-name> scripts/odoo_sh_build.sh
```

## Manual runs (local/staging/live)

```
odoo/odoo-bin shell -c odoo.conf -d <dbname> --load=script scripts/run_ptt_cleanup.py
odoo/odoo-bin -c odoo.conf -d <dbname> -u ptt_business_core
```

## Notes
- `run_ptt_cleanup.py` executes: orphan audit -> legacy Studio cleanup -> orphan service cleanup -> deprecated event field removal.
- The module upgrade (`-u ptt_business_core`) ensures migration 19.0.4.4.4 also runs, keeping schema and metadata aligned.
- Ensure the branch DB has adequate privileges to drop columns.
