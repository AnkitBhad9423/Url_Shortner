# app/auth/password.py
from passlib.context import CryptContext

# bcrypt is the industry standard for password hashing
# never store plain passwords — ever
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Hash a plain password. Store this in DB."""
    print("Type:", type(plain))
    print("Length:", len(plain))
    print("Value preview:", plain[:50])
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Compare plain password against stored hash."""
    return pwd_context.verify(plain, hashed)