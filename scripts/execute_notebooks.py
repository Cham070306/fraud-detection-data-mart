"""Execute project notebooks and persist outputs without requiring Jupyter CLI."""
from __future__ import annotations

import argparse
import ast
import contextlib
from datetime import datetime, timezone
import io
import json
from pathlib import Path


def _output(value):
    if value is None:
        return None
    data = {"text/plain": repr(value)}
    if hasattr(value, "to_html"):
        data["text/html"] = value.to_html()
    return {"output_type": "execute_result", "metadata": {}, "data": data}


def execute_notebook(path: Path) -> None:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    namespace = {"__name__": "__main__"}
    execution_count = 0
    previous_cwd = Path.cwd()
    try:
        import os
        os.chdir(path.parent)
        for cell in notebook["cells"]:
            if cell["cell_type"] != "code":
                continue
            execution_count += 1
            source = "".join(cell["source"])
            tree = ast.parse(source, filename=str(path))
            prefix = tree.body
            expression = None
            if prefix and isinstance(prefix[-1], ast.Expr):
                expression = ast.Expression(prefix.pop().value)
            stream = io.StringIO()
            outputs = []
            with contextlib.redirect_stdout(stream):
                if prefix:
                    exec(compile(ast.Module(prefix, type_ignores=[]), str(path), "exec"), namespace)
                value = eval(compile(expression, str(path), "eval"), namespace) if expression else None
            if stream.getvalue():
                outputs.append({"output_type": "stream", "name": "stdout", "text": stream.getvalue()})
            rendered = _output(value)
            if rendered:
                rendered["execution_count"] = execution_count
                outputs.append(rendered)
            cell["execution_count"] = execution_count
            cell["outputs"] = outputs
        notebook["metadata"]["run_all"] = {
            "status": "success",
            "executed_at_utc": datetime.now(timezone.utc).isoformat(),
            "executor": "scripts/execute_notebooks.py",
            "code_cells": execution_count,
        }
        path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
    finally:
        os.chdir(previous_cwd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("notebooks", nargs="+")
    args = parser.parse_args()
    for name in args.notebooks:
        path = Path(name).resolve()
        execute_notebook(path)
        print(f"Executed {path.name}")


if __name__ == "__main__":
    main()
