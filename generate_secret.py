import secrets
import base64
import uuid
from datetime import datetime

print("=" * 60)
print("🔑 SECRET KEY GENERATOR")
print("=" * 60)
print()

# 1. For JWT Authentication (What you need)
jwt_key = secrets.token_hex(32)
print("📌 JWT SECRET KEY (Use this for your Flask app):")
print(f"SECRET_KEY={jwt_key}")
print()

# 2. Alternative format
jwt_key_b64 = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
print("📌 JWT SECRET KEY (Base64 format):")
print(f"SECRET_KEY={jwt_key_b64}")
print()

# 3. For Stripe (Only if using Stripe)
print("📌 STRIPE KEYS (Only if using Stripe payments):")
print("⚠️  Stripe keys must be obtained from Stripe Dashboard")
print("🔗 https://dashboard.stripe.com/apikeys")
print()

print("=" * 60)
print("✅ Generated on:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 60)