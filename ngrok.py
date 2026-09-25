"""ContentForge AI — Single-URL Ngrok Tunnel with Reverse Proxy.

Runs a local reverse proxy on port 4000 that routes:
  /api/*,  /docs, /redoc, /openapi.json  -->  localhost:8000  (FastAPI backend)
  everything else                         -->  localhost:3000  (Vite React frontend)

Then opens ONE ngrok tunnel on port 4000, giving you a single public URL
with zero CORS issues (both frontend and backend are same-origin).

Prerequisites:
  1. Frontend dev server running on port 3000  (npm run dev)
  2. Backend dev server running on port 8000   (uvicorn app.main:app ...)
  3. pip install pyngrok
  4. ngrok authtoken configured:
       ngrok config add-authtoken YOUR_TOKEN
     or:
       set NGROK_AUTHTOKEN=YOUR_TOKEN

Usage:
  python ngrok.py
"""

import http.server
import urllib.request
import urllib.error
import threading
import signal
import sys
import os
import time
import socketserver

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
FRONTEND_PORT = 3000
BACKEND_PORT = 8000
PROXY_PORT = 4000

FRONTEND_ORIGIN = f"http://127.0.0.1:{FRONTEND_PORT}"
BACKEND_ORIGIN = f"http://127.0.0.1:{BACKEND_PORT}"

# Paths that should be routed to the FastAPI backend
BACKEND_PREFIXES = (
    "/api/",
    "/api",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/ws",          # websockets if any
)


# ---------------------------------------------------------------------------
# Reverse Proxy Handler
# ---------------------------------------------------------------------------
class ReverseProxyHandler(http.server.BaseHTTPRequestHandler):
    """Routes requests to either the frontend or backend based on path."""

    # Suppress default access logging noise; we print our own.
    def log_message(self, format, *args):
        pass

    # --- core routing ---------------------------------------------------
    def _target_url(self, path: str) -> str:
        """Decide which upstream to forward to."""
        if path.startswith(BACKEND_PREFIXES):
            return f"{BACKEND_ORIGIN}{path}"
        return f"{FRONTEND_ORIGIN}{path}"

    def _proxy(self):
        target = self._target_url(self.path)

        # Read request body if present
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        # Build upstream request
        req = urllib.request.Request(target, data=body, method=self.command)

        # Forward all headers except Host (urllib sets it automatically)
        hop_by_hop = {
            "host", "connection", "keep-alive", "proxy-authenticate",
            "proxy-authorization", "te", "trailers",
            "transfer-encoding", "upgrade",
        }
        for key, val in self.headers.items():
            if key.lower() not in hop_by_hop:
                req.add_header(key, val)

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                status = resp.status
                resp_headers = resp.getheaders()
                resp_body = resp.read()
        except urllib.error.HTTPError as e:
            status = e.code
            resp_headers = list(e.headers.items())
            resp_body = e.read()
        except urllib.error.URLError as e:
            # Upstream unreachable
            self.send_error(502, f"Bad Gateway: {e.reason}")
            return
        except Exception as e:
            self.send_error(502, f"Proxy error: {e}")
            return

        # Send response back to client
        self.send_response(status)
        skip_headers = {"transfer-encoding", "connection", "keep-alive"}
        for key, val in resp_headers:
            if key.lower() not in skip_headers:
                self.send_header(key, val)
        self.end_headers()
        self.wfile.write(resp_body)

    # --- HTTP method handlers -------------------------------------------
    def do_GET(self):
        self._proxy()

    def do_POST(self):
        self._proxy()

    def do_PUT(self):
        self._proxy()

    def do_PATCH(self):
        self._proxy()

    def do_DELETE(self):
        self._proxy()

    def do_OPTIONS(self):
        self._proxy()

    def do_HEAD(self):
        self._proxy()


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Handle each request in a new thread so slow upstreams don't block."""
    daemon_threads = True
    allow_reuse_address = True


def load_env_files():
    """Load environment variables from .env files in root, Frontend, or Backend directories."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_paths = [
        os.path.join(base_dir, ".env"),
        os.path.join(base_dir, ".env.local"),
        os.path.join(base_dir, "Frontend", ".env"),
        os.path.join(base_dir, "Frontend", ".env.local"),
        os.path.join(base_dir, "Backend", ".env"),
        os.path.join(base_dir, "Backend", ".env.local"),
    ]

    # Try python-dotenv first
    try:
        from dotenv import load_dotenv
        for path in env_paths:
            if os.path.exists(path):
                load_dotenv(path, override=False)
    except ImportError:
        pass

    # Fallback manual parser to ensure env vars are set
    for path in env_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip("'\"")
                            if key and key not in os.environ:
                                os.environ[key] = value
            except Exception:
                pass


def check_upstream_servers():
    """Check if frontend and backend servers are running on localhost."""
    import socket

    servers = [
        ("Frontend", FRONTEND_PORT, FRONTEND_ORIGIN),
        ("Backend", BACKEND_PORT, BACKEND_ORIGIN),
    ]

    all_ok = True
    print("\n[CHECK] Checking upstream servers...", flush=True)
    for name, port, url in servers:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.5)
        try:
            s.connect(("127.0.0.1", port))
            print(f"  [OK] {name} is RUNNING on port {port} ({url})", flush=True)
            s.close()
        except Exception:
            print(f"  [OFFLINE] {name} is NOT RUNNING on port {port} ({url})", flush=True)
            all_ok = False

    if not all_ok:
        print("\n[WARNING] One or more upstream servers are not running!", flush=True)
        print("  Make sure to start them in separate terminal windows:", flush=True)
        print(f"    - Frontend: cd Frontend && npm run dev (port {FRONTEND_PORT})", flush=True)
        print(f"    - Backend:  cd Backend && uvicorn app.main:app --reload --port {BACKEND_PORT}", flush=True)
        print("  (Proxy & Ngrok will still launch, but requests will fail with 502 until servers are started)\n", flush=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # Load .env configuration
    load_env_files()

    # Check if upstream servers (Frontend 3000 / Backend 8000) are running
    check_upstream_servers()

    # 1. Start reverse proxy in background thread
    proxy = ThreadedHTTPServer(("127.0.0.1", PROXY_PORT), ReverseProxyHandler)
    proxy_thread = threading.Thread(target=proxy.serve_forever, daemon=True)
    proxy_thread.start()
    print(f"\n[PROXY] Reverse proxy running on http://127.0.0.1:{PROXY_PORT}", flush=True)
    print(f"        /api/* --> http://127.0.0.1:{BACKEND_PORT}", flush=True)
    print(f"        /*     --> http://127.0.0.1:{FRONTEND_PORT}", flush=True)

    # 2. Open ngrok tunnel
    try:
        from pyngrok import ngrok, conf

        # Use authtoken from env or .env file if set
        auth_token = os.environ.get("NGROK_AUTHTOKEN", "").strip()
        if auth_token:
            masked_token = auth_token[:4] + "..." + auth_token[-4:] if len(auth_token) > 8 else "***"
            print(f"[NGROK] Using authtoken from environment / .env ({masked_token})", flush=True)
            ngrok.set_auth_token(auth_token)
        else:
            print("[NGROK] No NGROK_AUTHTOKEN found in .env; using system ngrok config if present.", flush=True)

        public_url = ngrok.connect(PROXY_PORT, "http", bind_tls=True)
        tunnel_url = str(public_url).replace('"', "").strip()

        print(f"\n{'=' * 60}", flush=True)
        print(f"  NGROK TUNNEL ACTIVE", flush=True)
        print(f"  Public URL:  {tunnel_url}", flush=True)
        print(f"{'=' * 60}", flush=True)
        print(f"\n  Frontend:  {tunnel_url}", flush=True)
        print(f"  Backend:   {tunnel_url}/api/...", flush=True)
        print(f"  API Docs:  {tunnel_url}/docs", flush=True)
        print(f"\n  Press Ctrl+C to stop.\n", flush=True)

    except ImportError:
        print("\n[ERROR] pyngrok is not installed. Run:  pip install pyngrok")
        proxy.shutdown()
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Failed to open ngrok tunnel: {e}")
        print("  Make sure you have configured your ngrok authtoken:")
        print("    ngrok config add-authtoken YOUR_TOKEN")
        print("  or set the environment variable:")
        print("    set NGROK_AUTHTOKEN=YOUR_TOKEN")
        proxy.shutdown()
        sys.exit(1)

    # 3. Keep alive until Ctrl+C
    def shutdown(sig=None, frame=None):
        print("\n[SHUTDOWN] Closing ngrok tunnel and proxy...")
        try:
            ngrok.disconnect(public_url.public_url)
            ngrok.kill()
        except Exception:
            pass
        proxy.shutdown()
        print("[SHUTDOWN] Done.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
