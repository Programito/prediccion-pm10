import hashlib
from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.restore_sources import restore, verify


class TestRestoreSources(unittest.TestCase):
    def entry(self, path, content):
        return {"path": path, "url": "https://example.org/source.csv",
                "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}

    def test_publica_solo_descarga_con_huella_correcta(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.csv"
            entry = self.entry(path, b"recorded")
            with patch("scripts.restore_sources.urlopen", return_value=BytesIO(b"recorded")):
                restore(entry)
            self.assertEqual(path.read_bytes(), b"recorded")
            verify(entry)
            self.assertFalse(list(path.parent.glob("*.part")))

    def test_descarta_respuesta_distinta_y_permite_reintento(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.csv"
            entry = self.entry(path, b"recorded")
            with patch("scripts.restore_sources.urlopen", return_value=BytesIO(b"changed!")):
                with self.assertRaises(ValueError):
                    restore(entry)
            self.assertFalse(path.exists())
            self.assertFalse(list(path.parent.glob("*.part")))
            with patch("scripts.restore_sources.urlopen", return_value=BytesIO(b"recorded")):
                restore(entry)
            self.assertEqual(path.read_bytes(), b"recorded")

    def test_conserva_original_existente_y_senala_conflicto(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.csv"
            path.write_bytes(b"user-copy")
            entry = self.entry(path, b"recorded")
            with patch("scripts.restore_sources.urlopen") as download:
                with self.assertRaises(ValueError):
                    restore(entry)
                download.assert_not_called()
            self.assertEqual(path.read_bytes(), b"user-copy")

    def test_reintento_verifica_sin_volver_a_descargar(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.csv"
            path.write_bytes(b"recorded")
            with patch("scripts.restore_sources.urlopen") as download:
                restore(self.entry(path, b"recorded"))
                download.assert_not_called()


if __name__ == "__main__":
    unittest.main()
