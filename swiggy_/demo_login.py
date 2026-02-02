import os
import django
import sys
import requests

# Setup Django Environment to access DB directly
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'swiggy_.settings')
django.setup()

from admin.users.models import Users
from admin.access.models import UserAuth

def run_demo():
    print("="*50)
    print("SWIGGY LOGIN DEMO")
    print("="*50)

    # ---------------------------------------------------------
    # 1. SETUP DEMO DATA
    # ---------------------------------------------------------
    print("\n[1] Setting up Demo Data in Database...")
    
    # Create Admin User
    admin_email = "superadmin@swiggy.local"
    admin_pass = "admin@123"
    
    admin_user, created = Users.objects.get_or_create(
        email=admin_email, 
        defaults={'name': 'Super Admin', 'role': 'ADMIN'}
    )
    if not created and admin_user.role != 'ADMIN':
        admin_user.role = 'ADMIN'
        admin_user.save()
        
    # Setup Admin Auth
    admin_auth, _ = UserAuth.objects.get_or_create(user=admin_user, defaults={'auth_type': 'ADMIN'})
    admin_auth.password_hash = admin_pass  # Storing plain text as per current simplistic logic
    admin_auth.save()
    
    print(f"    -> Admin Account Ready: {admin_email} (Pass: {admin_pass})")

    # Create Normal User
    user_email = "demo_user@swiggy.local"
    reg_user, _ = Users.objects.get_or_create(
        email=user_email,
        defaults={'name': 'Demo User', 'role': 'USER'}
    )
    print(f"    -> User Account Ready:  {user_email} (OTP Flow)")


    # ---------------------------------------------------------
    # 2. PERFORM API REQUESTS
    # ---------------------------------------------------------
    BASE_URL = "http://127.0.0.1:8000/api/auth/login/"
    
    print("\n[2] Testing API Endpoints...")

    # TEST A: Admin Login (Success)
    print(f"\n    A. Attempting Admin Login ({admin_email})...")
    try:
        payload = {'contact': admin_email, 'password': admin_pass}
        resp = requests.post(BASE_URL, json=payload)
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"       SUCCESS! Status: {resp.status_code}")
            print(f"       Access Token: {data.get('access')[:20]}...")
            print(f"       Role: {data.get('role')}")
        else:
            print(f"       FAILED. Status: {resp.status_code}")
            print(f"       Response: {resp.text}")
    except requests.exceptions.ConnectionError:
        print("       ERROR: Could not connect to server. Is it running on port 8000?")


    # TEST B: User Login (OTP Gen)
    print(f"\n    B. Attempting User Login ({user_email})...")
    try:
        payload = {'contact': user_email}
        resp = requests.post(BASE_URL, json=payload)
        
        if resp.status_code == 200:
            print(f"       SUCCESS! Status: {resp.status_code}")
            print(f"       Response: {resp.json()}")
        else:
            print(f"       FAILED. Status: {resp.status_code}")
            print(f"       Response: {resp.text}")
    except requests.exceptions.ConnectionError:
        print("       ERROR: Could not connect to server.")

    # TEST C: Verify OTP (Simulation)
    # Since we can't easily get the random OTP sent to console without parsing logs
    # We will fetch it from DB for this demo script specifically
    print(f"\n    C. Simulating OTP Verification for {user_email}...")
    
    user_auth = UserAuth.objects.get(user=reg_user)
    current_otp = user_auth.otp
    
    if current_otp:
        print(f"       [Internal] Fetched OTP from DB: {current_otp}")
        try:
            payload = {'contact': user_email, 'otp': current_otp}
            resp = requests.post(BASE_URL, json=payload)
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"       SUCCESS! Status: {resp.status_code}")
                print(f"       Access Token: {data.get('access')[:20]}...")
            else:
                print(f"       FAILED. Status: {resp.status_code}")
                print(f"       Response: {resp.text}")
        except requests.exceptions.ConnectionError:
            print("       ERROR: Could not connect to server.")
    else:
        print("       [Internal] No OTP found in DB (Test B might have failed to generate one).")

    print("\n" + "="*50)

if __name__ == "__main__":
    run_demo()
