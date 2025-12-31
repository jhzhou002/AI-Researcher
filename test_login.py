"""测试登录API"""
import requests

# 测试登录
login_data = {
    "username": "jason",
    "password": "123456"
}

try:
    response = requests.post(
        "http://127.0.0.1:8000/api/auth/login",
        data=login_data,  # OAuth2PasswordRequestForm使用form data
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
