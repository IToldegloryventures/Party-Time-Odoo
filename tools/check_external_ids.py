"""Check XML refs against known external IDs.

Usage:
  python tools/check_external_ids.py [root]
"""
import os
import re
import sys
import xml.etree.ElementTree as ET


def collect_ids(base_dirs):
    ids = set()
    for base in base_dirs:
        for dirpath, _, filenames in os.walk(base):
            for name in filenames:
                if not name.endswith(".xml"):
                    continue
                path = os.path.join(dirpath, name)
                try:
                    tree = ET.parse(path)
                except Exception:
                    continue
                root = tree.getroot()
                for el in root.iter():
                    xml_id = el.get("id")
                    if xml_id:
                        # module is inferred by file path unless id is already qualified
                        if "." in xml_id:
                            ids.add(xml_id)
                        else:
                            module = module_from_path(path)
                            if module:
                                ids.add(f"{module}.{xml_id}")
                            else:
                                ids.add(xml_id)
                    if el.tag == "record" and el.get("model") == "ir.model.data":
                        module_val = None
                        name_val = None
                        for child in el:
                            if child.tag != "field":
                                continue
                            field_name = child.get("name")
                            if field_name == "module":
                                module_val = (child.text or "").strip()
                            if field_name == "name":
                                name_val = (child.text or "").strip()
                        if module_val and name_val:
                            ids.add(f"{module_val}.{name_val}")
    return ids


def module_from_path(path):
    parts = path.replace("\\", "/").split("/")
    if "addons" in parts:
        idx = parts.index("addons")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return None


def find_repo_root(start_path):
    cur = os.path.abspath(start_path)
    while True:
        if os.path.isdir(os.path.join(cur, "odoo")) and os.path.isdir(os.path.join(cur, "addons")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return os.path.abspath(start_path)
        cur = parent


def is_ref_candidate(ref):
    if not ref:
        return False
    if ref.startswith("model_"):
        return False
    if ".model_" in ref:
        return False
    if "{" in ref or "}" in ref:
        return False
    if "://" in ref or ref.startswith("/") or ref.startswith("mailto:"):
        return False
    if any(ch in ref for ch in ("/", "?", "#")):
        return False
    return True


def main(root):
    repo_root = find_repo_root(root)
    candidates = [
        root,
        os.path.join(repo_root, "addons"),
        os.path.join(repo_root, "odoo", "addons"),
        os.path.join(repo_root, "odoo", "odoo", "addons"),
    ]
    base_dirs = []
    for path in candidates:
        if os.path.exists(path) and path not in base_dirs:
            base_dirs.append(path)
    ids = collect_ids(base_dirs)

    errors = []
    ref_re = re.compile(r"ref=\"([^\"]+)\"")
    eval_ref_re = re.compile(r"ref\('([^']+)'\)")

    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if not name.endswith(".xml"):
                continue
            path = os.path.join(dirpath, name)
            text = open(path, "r", encoding="utf-8").read()
            module = module_from_path(path)
            for match in ref_re.findall(text):
                ref = match
                if not is_ref_candidate(ref):
                    continue
                if "." in ref:
                    if ref not in ids:
                        errors.append(f"{path}: missing ref {ref}")
                else:
                    if module and f"{module}.{ref}" not in ids:
                        errors.append(f"{path}: missing ref {module}.{ref}")
            for match in eval_ref_re.findall(text):
                ref = match
                if not is_ref_candidate(ref):
                    continue
                if "." in ref:
                    if ref not in ids:
                        errors.append(f"{path}: missing ref {ref}")
                else:
                    if module and f"{module}.{ref}" not in ids:
                        errors.append(f"{path}: missing ref {module}.{ref}")

    if errors:
        print("External ID issues:")
        for err in errors:
            print(f"- {err}")
        return 1
    print("External ID checks OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "addons"))
