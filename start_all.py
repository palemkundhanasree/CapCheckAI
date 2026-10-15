#!/usr/bin/env python3
"""
TruthLens AI - All-in-One Single-Click Application Runner
Automatically checks prerequisites, auto-installs missing dependencies,
initializes the database, starts backend and frontend, and opens the browser.
"""

import sys
import os
import subprocess
import time
import webbrowser
import shutil
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
VENV_DIR = ROOT_DIR / "venv"
VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe" if os.name == "nt" else VENV_DIR / "bin" / "python"
VENV_PIP = VENV_DIR / "Scripts" / "pip.exe" if os.name == "nt" else VENV_DIR / "bin" / "pip"


def print_banner():
    print("=" * 70, flush=True)
    print("               TruthLens AI - All-in-One Launcher", flush=True)
    print("=" * 70, flush=True)
    print(flush=True)


def check_prerequisites():
    print("[1/5] Checking System Prerequisites...", flush=True)
    print(f"      - Python: {sys.version.split()[0]} (Verified)", flush=True)

    # Check Node.js in PATH and standard Windows locations
    node_cmd = shutil.which("node")
    if not node_cmd:
        possible_node_paths = [
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "nodejs",
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "nodejs",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "nodejs",
        ]
        for p in possible_node_paths:
            if (p / "node.exe").exists():
                print(f"      - Found Node.js at: {p}", flush=True)
                os.environ["PATH"] = str(p) + os.pathsep + os.environ.get("PATH", "")
                node_cmd = shutil.which("node")
                break

    if not node_cmd:
        print("\n[ERROR] Node.js is not found on your system!", flush=True)
        print("Please download and install Node.js (v18, v20, or v22) from: https://nodejs.org/", flush=True)
        print("After installation, double-click run.bat again.", flush=True)
        input("\nPress Enter to exit...")
        sys.exit(1)

    try:
        node_ver = subprocess.check_output(["node", "-v"], text=True).strip()
        print(f"      - Node.js: {node_ver} (Verified)", flush=True)
    except Exception:
        print("      - Node.js: Found (Verified)", flush=True)


def ensure_backend_venv():
    print("\n[2/5] Checking Python Virtual Environment & Backend Packages...", flush=True)
    if not VENV_PYTHON.exists():
        print("      - Virtual environment not found. Creating 'venv'...", flush=True)
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])
        print("      - Virtual environment created successfully.", flush=True)

    # Check if packages are installed
    req_file = BACKEND_DIR / "requirements.txt"
    try:
        subprocess.check_call(
            [str(VENV_PYTHON), "-c", "import fastapi, uvicorn, sqlalchemy, pydantic, PIL, reportlab"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("      - Backend dependencies are verified.", flush=True)
    except Exception:
        print("      - Installing backend dependencies via pip (this may take 1-2 minutes)...", flush=True)
        subprocess.check_call([str(VENV_PYTHON), "-m", "pip", "install", "-r", str(req_file)])
        print("      - Backend dependencies installed successfully.", flush=True)

    # Check .env
    env_file = ROOT_DIR / ".env"
    env_example = ROOT_DIR / ".env.example"
    if not env_file.exists() and env_example.exists():
        shutil.copy2(env_example, env_file)
        print("      - Generated .env from .env.example.", flush=True)

    # Initialize SQLite DB
    print("      - Initializing SQLite database...", flush=True)
    subprocess.check_call([
        str(VENV_PYTHON), "-c",
        "import sys; sys.path.insert(0, 'backend'); from app.db.session import init_db; init_db()"
    ], cwd=str(ROOT_DIR))
    print("      - Database tables initialized.", flush=True)


def ensure_frontend_deps():
    print("\n[3/5] Checking Frontend Dependencies...", flush=True)
    node_modules = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print("      - node_modules not found. Running 'npm install'...", flush=True)
        shell_cmd = "npm.cmd" if os.name == "nt" else "npm"
        subprocess.check_call([shell_cmd, "install"], cwd=str(FRONTEND_DIR))
        print("      - Frontend packages installed successfully.", flush=True)
    else:
        print("      - Frontend dependencies are verified.", flush=True)


def check_url_live(url, timeout=1.5):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TruthLens-Probe/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.status in (200, 304, 404)
    except Exception:
        return False


def run_services():
    print("\n[4/5] Launching TruthLens AI Services...", flush=True)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR)

    # 1. Start FastAPI Backend if not already running
    backend_proc = None
    if check_url_live("http://127.0.0.1:8000/api/v1/health"):
        print("      - FastAPI Backend is already running on port 8000.", flush=True)
    else:
        print("      - Starting Backend Server on http://127.0.0.1:8000...", flush=True)
        backend_proc = subprocess.Popen(
            [str(VENV_PYTHON), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=str(BACKEND_DIR),
            env=env
        )

    # 2. Start Vite Frontend if not already running
    frontend_proc = None
    if check_url_live("http://localhost:5173"):
        print("      - Vite Frontend is already running on port 5173.", flush=True)
    else:
        print("      - Starting Frontend Server on http://localhost:5173...", flush=True)
        shell_cmd = "npm.cmd" if os.name == "nt" else "npm"
        frontend_proc = subprocess.Popen(
            [shell_cmd, "run", "dev"],
            cwd=str(FRONTEND_DIR)
        )

    # 3. Wait for services to respond
    print("\n[5/5] Awaiting service readiness...", flush=True)
    backend_up = check_url_live("http://127.0.0.1:8000/api/v1/health")
    frontend_up = check_url_live("http://localhost:5173")

    for _ in range(35):
        if not backend_up:
            backend_up = check_url_live("http://127.0.0.1:8000/api/v1/health")
        if not frontend_up:
            frontend_up = check_url_live("http://localhost:5173")

        if backend_up and frontend_up:
            break
        time.sleep(1.0)

    print("\n" + "=" * 70, flush=True)
    print("            TruthLens AI IS RUNNING SUCCESSFULLY!", flush=True)
    print("=" * 70, flush=True)
    print("\n  -> Web Application:        http://localhost:5173", flush=True)
    print("  -> Swagger API Docs:       http://127.0.0.1:8000/docs", flush=True)
    print("  -> Health Check:           http://127.0.0.1:8000/api/v1/health", flush=True)
    print("  -> Default Admin Login:    admin@truthlens.ai / capcheck123", flush=True)
    print("\nPress Ctrl+C in this window at any time to stop both servers.", flush=True)
    print("=" * 70 + "\n", flush=True)

    # Open browser
    try:
        webbrowser.open("http://localhost:5173")
    except Exception:
        pass

    # Keep alive until Ctrl+C
    try:
        while True:
            time.sleep(1)
            # If backend or frontend died, report it
            if backend_proc and backend_proc.poll() is not None:
                print("\n[WARNING] Backend process exited unexpectedly.", flush=True)
                break
            if frontend_proc and frontend_proc.poll() is not None:
                print("\n[WARNING] Frontend process exited unexpectedly.", flush=True)
                break
    except KeyboardInterrupt:
        print("\nStopping TruthLens AI services...", flush=True)
    finally:
        for proc in [backend_proc, frontend_proc]:
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=3)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
        print("All TruthLens AI services stopped cleanly.", flush=True)


def main():
    print_banner()
    try:
        check_prerequisites()
        ensure_backend_venv()
        ensure_frontend_deps()
        run_services()
    except Exception as e:
        print(f"\n[ERROR OCCURRED] {e}", flush=True)
        input("\nPress Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()
