"""Parse Python models and report fields/methods.

Usage:
  python tools/check_python_models.py [root]
"""
import ast
import os
import sys


def literal_str(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def class_model_info(class_def):
    model_name = None
    inherit_val = None
    has_name = False
    for node in class_def.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == "_name":
                model_name = literal_str(node.value)
                has_name = True
            if isinstance(target, ast.Name) and target.id == "_inherit":
                inherit_val = literal_str(node.value)
    if model_name:
        return [model_name], has_name
    if isinstance(inherit_val, str):
        return [inherit_val], has_name
    if isinstance(inherit_val, (list, tuple)):
        return [v for v in inherit_val if isinstance(v, str)], has_name
    return [], has_name


def class_model_names(class_def):
    names, _ = class_model_info(class_def)
    return names


def parse_models(root):
    model_fields = {}
    model_methods = {}
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if not name.endswith(".py"):
                continue
            path = os.path.join(dirpath, name)
            try:
                tree = ast.parse(open(path, "r", encoding="utf-8").read(), filename=path)
            except Exception:
                continue
            for node in tree.body:
                if not isinstance(node, ast.ClassDef):
                    continue
                model_names = class_model_names(node)
                if not model_names:
                    continue
                for model in model_names:
                    model_fields.setdefault(model, set())
                    model_methods.setdefault(model, set())
                for item in node.body:
                    if isinstance(item, ast.Assign) and isinstance(item.value, ast.Call):
                        if isinstance(item.value.func, ast.Attribute) and isinstance(item.value.func.value, ast.Name):
                            if item.value.func.value.id == "fields":
                                for target in item.targets:
                                    if isinstance(target, ast.Name):
                                        for model in model_names:
                                            model_fields[model].add(target.id)
                    if isinstance(item, ast.FunctionDef):
                        for model in model_names:
                            model_methods[model].add(item.name)
    return model_fields, model_methods


def parse_models_with_inheritance(root):
    model_fields = {}
    model_methods = {}
    model_defined = set()
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if not name.endswith(".py"):
                continue
            path = os.path.join(dirpath, name)
            try:
                tree = ast.parse(open(path, "r", encoding="utf-8").read(), filename=path)
            except Exception:
                continue
            for node in tree.body:
                if not isinstance(node, ast.ClassDef):
                    continue
                model_names, has_name = class_model_info(node)
                if not model_names:
                    continue
                for model in model_names:
                    model_fields.setdefault(model, set())
                    model_methods.setdefault(model, set())
                    if has_name:
                        model_defined.add(model)
                for item in node.body:
                    if isinstance(item, ast.Assign) and isinstance(item.value, ast.Call):
                        if isinstance(item.value.func, ast.Attribute) and isinstance(item.value.func.value, ast.Name):
                            if item.value.func.value.id == "fields":
                                for target in item.targets:
                                    if isinstance(target, ast.Name):
                                        for model in model_names:
                                            model_fields[model].add(target.id)
                    if isinstance(item, ast.FunctionDef):
                        for model in model_names:
                            model_methods[model].add(item.name)
    return model_fields, model_methods, model_defined


def main(root):
    model_fields, model_methods = parse_models(root)
    print(f"Models found: {len(model_fields)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "addons"))
