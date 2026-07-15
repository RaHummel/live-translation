import datetime
import logging
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from config.config_manager import ConfigManager

LOGGER = logging.getLogger(__name__)

# Single shared directory for all persistent Mumble certificates
CERTS_DIR = ConfigManager.get_app_config_dir() / 'murmur' / 'certs'


def ensure_cert(cert_path: Path, key_path: Path, common_name: str) -> tuple[str, str]:
    """Generate a persistent self-signed certificate at *cert_path*/*key_path* if missing.

    Returns (certfile_path, keyfile_path) as strings.
    """
    cert_path.parent.mkdir(parents=True, exist_ok=True)

    if cert_path.exists() and key_path.exists():
        return str(cert_path), str(key_path)

    LOGGER.info('Generating persistent client certificate "%s" in %s', common_name, cert_path.parent)

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650))
        .sign(key, hashes.SHA256())
    )

    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    LOGGER.info('Client certificate written to %s', cert_path.parent)
    return str(cert_path), str(key_path)
