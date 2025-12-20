
import sys
import traceback

print(f"Python path: {sys.path}")

print("Attempting to import delta.dashboard.server...")
try:
    from delta.dashboard.server import run_dashboard_server
    print("SUCCESS: Imported run_dashboard_server")
except ImportError:
    print("FAIL: ImportError caught. Printing traceback:")
    traceback.print_exc()
except Exception:
    print("FAIL: Other exception caught. Printing traceback:")
    traceback.print_exc()
