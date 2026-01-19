"""Check XML files for well-formedness and view field/method references.

Usage:
  python tools/check_xml_views.py [root]
"""
import os
import sys
import xml.etree.ElementTree as ET

from check_python_models import parse_models_with_inheritance

VIEW_ROOT_TAGS = {
    "form",
    "tree",
    "list",
    "kanban",
    "calendar",
    "graph",
    "pivot",
    "gantt",
    "timeline",
    "activity",
    "search",
}

AUTO_FIELDS = {
    "id",
    "display_name",
    "create_date",
    "create_uid",
    "write_date",
    "write_uid",
    "__last_update",
}

KNOWN_METHODS = {
    "toggle_active",
    "action_archive",
    "action_unarchive",
}


def walk_arch(node, model, model_fields, model_methods, model_defined, errors, path, in_subview=False):
    if node.tag == "field":
        fname = node.get("name")
        if fname and not in_subview and model in model_defined:
            if fname not in AUTO_FIELDS and model in model_fields and fname not in model_fields[model]:
                errors.append(f"{path}: view field '{fname}' missing on model '{model}'")
        has_subview = any(child.tag in VIEW_ROOT_TAGS for child in node)
        for child in node:
            walk_arch(
                child,
                model,
                model_fields,
                model_methods,
                model_defined,
                errors,
                path,
                in_subview or has_subview,
            )
        return
    if node.tag == "button" and node.get("type") == "object" and not in_subview and model in model_defined:
        mname = node.get("name")
        if mname and mname not in KNOWN_METHODS and model in model_methods and mname not in model_methods[model]:
            errors.append(f"{path}: method '{mname}' missing on model '{model}'")
    for child in node:
        walk_arch(child, model, model_fields, model_methods, model_defined, errors, path, in_subview)


def main(root):
    model_fields, model_methods, model_defined = parse_models_with_inheritance(root)
    errors = []

    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if not name.endswith(".xml"):
                continue
            path = os.path.join(dirpath, name)
            try:
                tree = ET.parse(path)
            except Exception as exc:
                errors.append(f"{path}: XML parse error: {exc}")
                continue

            root_el = tree.getroot()
            for rec in root_el.findall(".//record"):
                if rec.get("model") != "ir.ui.view":
                    continue
                model_field = rec.find("./field[@name='model']")
                if model_field is None or not (model_field.text or "").strip():
                    continue
                model = (model_field.text or "").strip()
                arch = rec.find("./field[@name='arch']")
                if arch is None:
                    continue
                for child in arch:
                    walk_arch(
                        child,
                        model,
                        model_fields,
                        model_methods,
                        model_defined,
                        errors,
                        path,
                        in_subview=False,
                    )

    if errors:
        print("XML/view issues:")
        for err in errors:
            print(f"- {err}")
        return 1
    print("XML/view checks OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "addons"))
