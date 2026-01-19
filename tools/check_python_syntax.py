"""Compile Python files to catch syntax errors.

Usage:
  python tools/check_python_syntax.py [root]
"""
import os
import py_compile
import sys


def main(root):
    errors = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if not name.endswith(".py"):
                continue
            path = os.path.join(dirpath, name)
            try:
                py_compile.compile(path, doraise=True)
            except Exception as exc:
                errors.append(f"{path}: {exc}")

    if errors:
        print("Python syntax errors:")
        for err in errors:
            print(f"- {err}")
        return 1
    print("Python syntax OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "addons"))