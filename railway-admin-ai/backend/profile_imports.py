import time
import sys

def test_import(module_name):
    start = time.time()
    try:
        __import__(module_name)
        print(f"Import {module_name} took {time.time() - start:.4f}s")
    except Exception as e:
        print(f"Import {module_name} failed: {type(e).__name__} {str(e)}")

print("Profiling imports:")
test_import("app.api.auth")
test_import("app.api.documents")
test_import("app.api.cases")
test_import("app.api.chat")
test_import("app.api.eligibility")
test_import("app.api.rules")
test_import("app.api.reports")
