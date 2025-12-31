"""
直接使用bcrypt进行测试，绕过passlib看看是否兼容
"""
import bcrypt

password = b"testpass123"
hashed = bcrypt.hashpw(password, bcrypt.gensalt())
print(f"Direct bcrypt hash: {hashed}")

check = bcrypt.checkpw(password, hashed)
print(f"Direct bcrypt check: {check}")
