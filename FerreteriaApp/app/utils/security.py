import hashlib
import secrets

def crear_hash(password: str) -> str:
    """Hash SHA-256 con sal aleatoria. Nunca guardar la contraseña en texto plano."""
    salt = secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${digest}"

def verificar_password(password: str, password_hash: str) -> bool:
    try:
        salt, digest = password_hash.split("$", 1)
        comprobacion = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return secrets.compare_digest(comprobacion, digest)
    except (ValueError, AttributeError):
        return False
