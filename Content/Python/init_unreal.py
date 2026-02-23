"""
CatBakery Python Skill Set - HTTP Server for Claude Code Integration

UE5 Editor starts this automatically via PythonScriptPlugin.
Provides POST /execute for arbitrary Python script execution on the game thread,
and GET /health for status checks.

Architecture:
  Claude Code --HTTP--> Background Thread (HTTPServer)
                          |
                          v
                    ThreadSafeQueue (Lock-protected)
                          |
                          v
                    Slate Post-Tick Callback (Game Thread)
                          |
                          v
                    exec(script, context) -> result via Event
"""

import unreal
import threading
import traceback
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

_VERSION = "1.0.0"
_HOST = "127.0.0.1"
_PORT = 8080
_LOG_PREFIX = "[PythonSkillSet]"


# ---------------------------------------------------------------------------
# Thread-safe queue
# ---------------------------------------------------------------------------
class ThreadSafeQueue:
    """Lock-protected FIFO queue for cross-thread communication."""

    def __init__(self):
        self._lock = threading.Lock()
        self._items = []

    def push(self, item):
        with self._lock:
            self._items.append(item)

    def drain(self):
        """Remove and return all items atomically."""
        with self._lock:
            items = self._items[:]
            self._items.clear()
            return items

    def __len__(self):
        with self._lock:
            return len(self._items)


# ---------------------------------------------------------------------------
# Execution context
# ---------------------------------------------------------------------------
class ExecutionContext:
    """Per-request context carrying script, params, result, and sync event."""

    def __init__(self, script, params, timeout=30.0):
        self.script = script
        self.params = params
        self.timeout = timeout
        self.result = {}
        self.error = None
        self.done = threading.Event()

    def wait(self):
        """Block until execution completes or timeout."""
        if not self.done.wait(timeout=self.timeout):
            self.error = f"Execution timed out after {self.timeout}s"
        return self

    def to_response(self):
        """Build JSON-serializable response dict."""
        if self.error:
            return {"success": False, "error": self.error}
        return {"success": True, "result": self.result}


# ---------------------------------------------------------------------------
# Queues
# ---------------------------------------------------------------------------
_editor_queue = ThreadSafeQueue()
_game_queue = ThreadSafeQueue()


# ---------------------------------------------------------------------------
# Script executor (runs on game thread via tick callback)
# ---------------------------------------------------------------------------
def _execute_context(ctx):
    """Execute a script within its context. Must run on game thread."""
    namespace = {
        "unreal": unreal,
        "params": ctx.params,
        "result": ctx.result,
    }
    try:
        exec(ctx.script, namespace)
        # exec may have mutated ctx.result in-place; also capture any
        # top-level 'result' reassignment
        if "result" in namespace and namespace["result"] is not ctx.result:
            ctx.result = namespace["result"]
    except Exception:
        ctx.error = traceback.format_exc()
    finally:
        ctx.done.set()


def _drain_queue(queue):
    """Process all pending contexts from a queue."""
    for ctx in queue.drain():
        _execute_context(ctx)


# ---------------------------------------------------------------------------
# Slate post-tick callback
# ---------------------------------------------------------------------------
_tick_handle = None


def _on_slate_post_tick(delta_time):
    """Called every Slate tick on the game thread. Drains both queues."""
    _drain_queue(_editor_queue)
    _drain_queue(_game_queue)


# ---------------------------------------------------------------------------
# HTTP request handler
# ---------------------------------------------------------------------------
class _RequestHandler(BaseHTTPRequestHandler):
    """Thin HTTP handler: /health and /execute."""

    def do_GET(self):
        if self.path == "/health":
            body = json.dumps({
                "status": "running",
                "version": _VERSION,
                "editor_queue_size": len(_editor_queue),
                "game_queue_size": len(_game_queue),
            })
            self._respond(200, body)
        else:
            self._respond(404, json.dumps({"error": "Not found"}))

    def do_POST(self):
        if self.path != "/execute":
            self._respond(404, json.dumps({"error": "Not found"}))
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            body = json.loads(raw)
        except Exception as e:
            self._respond(400, json.dumps({"success": False, "error": f"Bad request: {e}"}))
            return

        mode = body.get("mode", "editor")
        script = body.get("script", "")
        params = body.get("params", {})
        timeout = float(body.get("timeout", 30))

        if mode not in ("editor", "game"):
            self._respond(400, json.dumps({
                "success": False,
                "error": f"Unknown mode: {mode}. Use 'editor' or 'game'.",
            }))
            return

        ctx = ExecutionContext(script, params, timeout=timeout)

        if mode == "editor":
            _editor_queue.push(ctx)
        else:
            _game_queue.push(ctx)

        ctx.wait()

        response = ctx.to_response()
        self._respond(200, json.dumps(response, ensure_ascii=False, default=str))

    def _respond(self, status, body_str):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body_str.encode("utf-8"))

    def log_message(self, format, *args):
        # Suppress default stderr logging; route to UE log
        unreal.log(f"{_LOG_PREFIX} {format % args}")


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------
_server_instance = None


def _start_server():
    """Start HTTPServer on a daemon background thread."""
    global _server_instance

    try:
        _server_instance = HTTPServer((_HOST, _PORT), _RequestHandler)
        unreal.log(f"{_LOG_PREFIX} HTTP server listening on {_HOST}:{_PORT}")
        _server_instance.serve_forever()
    except OSError as e:
        if e.errno == 10048:  # WSAEADDRINUSE on Windows
            unreal.log_warning(
                f"{_LOG_PREFIX} Port {_PORT} already in use. "
                "Server may already be running from a previous session."
            )
        else:
            unreal.log_error(f"{_LOG_PREFIX} Failed to start HTTP server: {e}")
    except Exception as e:
        unreal.log_error(f"{_LOG_PREFIX} Failed to start HTTP server: {e}")


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------
def _initialize():
    """Entry point: register tick callback and start HTTP server."""
    global _tick_handle

    # Register Slate post-tick callback for game-thread execution
    _tick_handle = unreal.register_slate_post_tick_callback(_on_slate_post_tick)

    # Start HTTP server on background daemon thread
    server_thread = threading.Thread(target=_start_server, daemon=True)
    server_thread.start()

    unreal.log(f"{_LOG_PREFIX} Initialized successfully (v{_VERSION})")


_initialize()
