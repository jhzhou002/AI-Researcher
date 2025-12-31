"""
检查后端健康状态
"""
import requests

try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to backend. Is it running on port 8000?")
except Exception as e:
    print(f"❌ Error: {e}")
