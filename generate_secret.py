# generate_secret.py
import secrets
import uuid

# Method 1: Hex string (64 characters)
secret_key_hex = secrets.token_hex(32)
print(f"Hex key: {secret_key_hex}")

# Method 2: Combined UUIDs
secret_key_uuid = str(uuid.uuid4()) + str(uuid.uuid4())
print(f"UUID key: {secret_key_uuid}")

# Method 3: URL-safe base64
import base64
secret_key_b64 = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
print(f"Base64 key: {secret_key_b64}")