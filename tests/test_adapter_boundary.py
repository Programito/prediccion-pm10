"""Keep vendor imports inside the adapters that own that dependency."""

import ast
from pathlib import Path
import unittest


class TestAdapterBoundary(unittest.TestCase):
    def test_sklearn_imports_are_isolated(self):
        package = Path(__file__).resolve().parents[1] / "pm10_data"
        violations = []
        for source in package.rglob("*.py"):
            if source.is_relative_to(package / "adapters/sklearn"):
                continue
            for node in ast.walk(ast.parse(source.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import):
                    imported = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    imported = [node.module or ""]
                else:
                    continue
                if any(name == "sklearn" or name.startswith("sklearn.") for name in imported):
                    violations.append(str(source.relative_to(package)))
        self.assertEqual(violations, [])
