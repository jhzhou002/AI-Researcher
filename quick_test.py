"""
快速测试注册API
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

print("Testing registration...")

data = {
    "email": f"test{int(time.time())}@example.com",  # 使用时间戳避免重复
    "username": f"testuser{int(time.time())}",
    "password": "testpass123"
}

try:
    response = requests.post(
        f"{BASE_URL}/api/auth/register",
        json=data,
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        print("✅ Registration successful!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Failed: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")
