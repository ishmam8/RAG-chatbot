# security.py
import bcrypt

def hash_password(password: str) -> str:
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    # Verify a password against the hashed version
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))