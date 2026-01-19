PostgreSQL Checklist (Odoo 19)

Run these after installing your custom modules in a staging database.

1) Missing fields in registry vs views
- Find views referencing fields not in the model:
  SELECT v.id, v.name, v.model
  FROM ir_ui_view v
  WHERE v.arch_db LIKE '%<field name=%' AND v.model IS NOT NULL;

2) Check model fields exist
- List fields for a model:
  SELECT name, ttype, relation
  FROM ir_model_fields
  WHERE model = 'your.model'
  ORDER BY name;

3) Invalid external IDs
- Verify a referenced external ID exists:
  SELECT * FROM ir_model_data
  WHERE module = 'your_module' AND name = 'xml_id';

4) Orphan record rules
- Rules referencing missing models:
  SELECT r.id, r.name, m.model
  FROM ir_rule r
  LEFT JOIN ir_model m ON m.id = r.model_id
  WHERE m.id IS NULL;

5) Access control coverage
- Models missing ACLs:
  SELECT m.model
  FROM ir_model m
  LEFT JOIN ir_model_access a ON a.model_id = m.id
  WHERE m.model LIKE 'ptt.%'
  GROUP BY m.model
  HAVING COUNT(a.id) = 0;

6) Duplicate XML IDs
- Detect duplicate XML IDs across modules:
  SELECT module, name, COUNT(*)
  FROM ir_model_data
  GROUP BY module, name
  HAVING COUNT(*) > 1;

7) Views failing to compile
- Identify views with errors in arch_db (if loaded):
  SELECT id, name, model
  FROM ir_ui_view
  WHERE arch_db IS NULL;

8) Model relations that point to missing models
- Check relations for missing comodels:
  SELECT name, model, relation
  FROM ir_model_fields
  WHERE relation IS NOT NULL
    AND relation NOT IN (SELECT model FROM ir_model);

9) Basic sanity for PTT models
- Quick counts:
  SELECT model, COUNT(*) FROM ir_model
  WHERE model LIKE 'ptt.%' GROUP BY model;

Note: Odoo.sh uses managed DB access; run these via `psql` in a local clone or
via Odoo shell with `env.cr` as needed.