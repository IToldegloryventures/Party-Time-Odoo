"""Check __manifest__.py files for common issues.

Usage:
  python tools/check_manifests.py [root]
"""
import ast
import os
import sys


def parse_manifest(path):
    text = open(path, "r", encoding="utf-8").read()
    tree = ast.parse(text, filename=path)
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Dict):
            return ast.literal_eval(node.value)
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
            return ast.literal_eval(node.value)
    raise ValueError("No manifest dict found")


def main(root):
    errors = []
    for dirpath, _, filenames in os.walk(root):
        if "__manifest__.py" not in filenames:
            continue
        manifest_path = os.path.join(dirpath, "__manifest__.py")
        module_dir = os.path.dirname(manifest_path)
        module_name = os.path.basename(module_dir)
        try:
            manifest = parse_manifest(manifest_path)
        except Exception as exc:
            errors.append(f"{manifest_path}: failed to parse manifest: {exc}")
            continue

        version = manifest.get("version")
        if not (isinstance(version, str) and version.startswith("19.0.")):
            errors.append(f"{manifest_path}: version should start with 19.0.")

        data_files = manifest.get("data", []) or []
        for rel in data_files:
            if not isinstance(rel, str):
                continue
            abs_path = os.path.join(module_dir, rel)
            if not os.path.exists(abs_path):
                errors.append(f"{manifest_path}: missing data file {rel}")

        assets = manifest.get("assets", {}) or {}
        if isinstance(assets, dict):
            for _, entries in assets.items():
                if not isinstance(entries, (list, tuple)):
                    continue
                for item in entries:
                    if isinstance(item, str):
                        abs_path = os.path.join(module_dir, item) if not item.startswith("/") else None
                        if abs_path and not os.path.exists(abs_path):
                            errors.append(f"{manifest_path}: missing asset {item}")

        depends = manifest.get("depends", []) or []
        if not isinstance(depends, list):
            errors.append(f"{manifest_path}: depends should be a list")
        else:
            for dep in depends:
                if not isinstance(dep, str):
                    errors.append(f"{manifest_path}: non-string dependency {dep}")

    if errors:
        print("Manifest issues:")
        for err in errors:
            print(f"- {err}")
        return 1
    print("Manifest check OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "addons"))