import time
print("Importing app.main...")
start = time.time()
try:
    from app.main import app
    print(f"Import success in {time.time() - start:.4f}s")
except Exception as e:
    print("Import failed:", type(e).__name__, str(e))
