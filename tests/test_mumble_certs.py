import tempfile
import unittest
from pathlib import Path

from utils.mumble_certs import ensure_cert


class TestMumbleCerts(unittest.TestCase):
    def test_ensure_cert_generates_new_certificate(self):
        with tempfile.TemporaryDirectory() as tmp:
            cert_path = Path(tmp) / 'sub' / 'cert.pem'
            key_path = Path(tmp) / 'sub' / 'key.pem'

            returned_cert, returned_key = ensure_cert(cert_path, key_path, 'LiveTranslation-Test')

            self.assertTrue(cert_path.exists())
            self.assertTrue(key_path.exists())
            self.assertEqual(returned_cert, str(cert_path))
            self.assertEqual(returned_key, str(key_path))

            cert_bytes = cert_path.read_bytes()
            key_bytes = key_path.read_bytes()
            self.assertIn(b'BEGIN CERTIFICATE', cert_bytes)
            self.assertIn(b'BEGIN RSA PRIVATE KEY', key_bytes)

    def test_ensure_cert_reuses_existing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            cert_path = Path(tmp) / 'cert.pem'
            key_path = Path(tmp) / 'key.pem'
            cert_path.write_bytes(b'existing-cert')
            key_path.write_bytes(b'existing-key')

            returned_cert, returned_key = ensure_cert(cert_path, key_path, 'LiveTranslation-Test')

            self.assertEqual(cert_path.read_bytes(), b'existing-cert')
            self.assertEqual(key_path.read_bytes(), b'existing-key')
            self.assertEqual(returned_cert, str(cert_path))
            self.assertEqual(returned_key, str(key_path))

    def test_ensure_cert_creates_parent_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            cert_path = Path(tmp) / 'deep' / 'nested' / 'cert.pem'
            key_path = Path(tmp) / 'deep' / 'nested' / 'key.pem'

            ensure_cert(cert_path, key_path, 'LiveTranslation-Test')

            self.assertTrue(cert_path.parent.is_dir())
