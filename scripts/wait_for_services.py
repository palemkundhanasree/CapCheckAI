import urllib.request
import time
import sys

def check_url(url, timeout=2):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'CapCheck-Launcher/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status in (200, 304, 404)  # 200/404 means the server is actively listening
    except Exception:
        return False

def wait_for_services(backend_url="http://127.0.0.1:8000/api/v1/health", frontend_url="http://localhost:5173", max_seconds=45):
    print(f"Waiting for backend ({backend_url}) and frontend ({frontend_url})...")
    start = time.time()
    backend_ready = False
    frontend_ready = False

    while time.time() - start < max_seconds:
        if not backend_ready:
            backend_ready = check_url(backend_url)
            if backend_ready:
                print(" -> Backend service is UP and responding!")
        if not frontend_ready:
            frontend_ready = check_url(frontend_url)
            if frontend_ready:
                print(" -> Frontend web server is UP and responding!")

        if backend_ready and frontend_ready:
            print("\nAll CapCheck AI services are ONLINE!")
            return True

        time.sleep(1.5)

    print("\nTimeout waiting for services. They may still be starting up.")
    return False

if __name__ == "__main__":
    wait_for_services()
