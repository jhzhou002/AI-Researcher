"""
测试用户注册功能
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_register():
    """测试注册"""
    url = f"{BASE_URL}/api/auth/register"
    
    data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123"
    }
    
    print(f"Testing registration at {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        try:
            print(f"Response JSON: {json.dumps(response.json(), indent=2)}")
        except:
            pass
        
        if response.status_code == 201:
            print("\n✅ Registration successful!")
            return response.json()
        else:
            print(f"\n❌ Registration failed")
            return None
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_login(username, password):
    """测试登录"""
    url = f"{BASE_URL}/api/auth/login"
    
    data = {
        "username": username,
        "password": password
    }
    
    print(f"\nTesting login at {url}")
    
    try:
        response = requests.post(
            url, 
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("\n✅ Login successful!")
            return response.json()["access_token"]
        else:
            print(f"\n❌ Login failed")
            return None
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


if __name__ == "__main__":
    print("=" * 50)
    print("AI-Researcher API Test")
    print("=" * 50)
    
    # 测试注册
    user = test_register()
    
    if user:
        # 测试登录
        token = test_login("testuser", "testpass123")
        
        if token:
            print(f"\n🎉 All tests passed!")
            print(f"Token: {token[:50]}...")
