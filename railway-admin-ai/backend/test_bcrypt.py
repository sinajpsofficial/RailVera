import bcrypt
import time

print("Testing bcrypt hashing speed...")
start = time.time()
try:
    salt = bcrypt.gensalt()
    print(f"gensalt took {time.time() - start:.4f}s")
    start_hash = time.time()
    hashed = bcrypt.hashpw("Password123".encode('utf-8'), salt)
    print(f"hashpw took {time.time() - start_hash:.4f}s")
    print("Hash result:", hashed.decode('utf-8'))
except Exception as e:
    print("Error:", type(e).__name__, str(e))
