import hmac
import hashlib
import os
import sys

# Key secret from the user's settings.py edit
api_secret = "c20SKd1gEcU4Aw4AxPny3p69"

razorpay_order_id = "order_SFDdIIohBf9cQ8"
# Mock payment ID for testing
razorpay_payment_id = "pay_TestPaymentId12345"

msg = f"{razorpay_order_id}|{razorpay_payment_id}"

signature = hmac.new(
    key=api_secret.encode(),
    msg=msg.encode(),
    digestmod=hashlib.sha256
).hexdigest()

print("---JSON PAYLOAD---")
print(f'{{"razorpay_order_id": "{razorpay_order_id}", "razorpay_payment_id": "{razorpay_payment_id}", "razorpay_signature": "{signature}"}}')
