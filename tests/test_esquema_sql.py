"""El script database/schema.sql debe estar al día con los modelos y ser ejecutable en PostgreSQL."""
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

import base_api  # noqa: F401  (configura el entorno de pruebas y el sys.path)

RAIZ = Path(__file__).resolve().parents[1]
SCHEMA = RAIZ / "database" / "schema.sql"


class EsquemaSqlTest(unittest.TestCase):
    def test_existe_y_esta_sincronizado_con_los_modelos(self):
        self.assertTrue(SCHEMA.exists(), "Falta database/schema.sql: ejecuta database/generar_schema.py")
        anterior = SCHEMA.read_text(encoding="utf-8")
        try:
            subprocess.run(
                [sys.executable, "-I", str(RAIZ / "database" / "generar_schema.py")],
                check=True, capture_output=True, cwd=RAIZ / "backend",
            )
            self.assertEqual(SCHEMA.read_text(encoding="utf-8"), anterior, "schema.sql estaba desactualizado")
        finally:
            SCHEMA.write_text(anterior, encoding="utf-8")

    def test_crea_todas_las_tablas_y_tipos(self):
        from app.database import Base
        import app.models  # noqa: F401

        sql = SCHEMA.read_text(encoding="utf-8")
        tablas = set(re.findall(r"CREATE TABLE (\w+)", sql))
        self.assertEqual(tablas, set(Base.metadata.tables))
        for tipo in set(re.findall(r"^\s+\w+ (\w+enum) ", sql, re.M)):
            self.assertIn(f"CREATE TYPE {tipo} AS ENUM", sql)
        # Cada tipo se crea antes de la primera tabla.
        self.assertLess(sql.rindex("CREATE TYPE"), sql.index("CREATE TABLE"))

    @unittest.skipUnless(os.environ.get("TEST_PG_URL"), "Define TEST_PG_URL (psql) para ejecutar el script en PostgreSQL")
    def test_se_ejecuta_en_postgresql(self):
        r = subprocess.run(
            ["psql", os.environ["TEST_PG_URL"], "-v", "ON_ERROR_STOP=1", "-q", "-f", str(SCHEMA)],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
