#!/usr/bin/env python3
"""Model explorer launcher.

Serves the bundled model-explorer Next.js app (model-explorer/ next to the
package or repository), opens it in a browser, and shuts the server down
cleanly on Ctrl-C / Ctrl-D (or SIGTERM/SIGHUP).
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

DEFAULT_PORT = 3312


def find_app_dir() -> Path | None:
    """Locate the model-explorer app directory."""
    env = os.environ.get("RUN_CLAUDE_MODEL_EXPLORER_DIR")
    if env:
        p = Path(env)
        if p.is_dir():
            return p
        print(f"[explorer] RUN_CLAUDE_MODEL_EXPLORER_DIR={env} is not a directory", file=sys.stderr)

    from .profiles import get_builtin_dir

    # Source checkout: app sits at the repo root next to profiles.yaml.
    # Wheel install: force-include places it inside the package dir.
    builtin = get_builtin_dir()
    for cand in (builtin / "model-explorer", builtin.parent / "model-explorer"):
        if (cand / "package.json").exists():
            return cand
    return None


def _port_serving(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://localhost:{port}", timeout=2) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError, ValueError):
        return False


def _wait_ready(port: int, timeout: float = 180.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _port_serving(port):
            return True
        time.sleep(0.5)
    return False


def _shutdown(proc: subprocess.Popen) -> None:
    """Terminate the npm process group (npm -> next-server tree)."""
    if proc.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        try:
            proc.wait(timeout=8)
            return
        except subprocess.TimeoutExpired:
            pass
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        proc.wait(timeout=5)
    except (ProcessLookupError, PermissionError, OSError):
        pass


def cmd_explorer(args: argparse.Namespace) -> int:
    app_dir = find_app_dir()
    if app_dir is None:
        print(
            "[explorer] model-explorer app not found.\n"
            "  Set RUN_CLAUDE_MODEL_EXPLORER_DIR to the model-explorer directory,\n"
            "  or run from a checkout that contains it.",
            file=sys.stderr,
        )
        return 1

    npm = shutil.which("npm")
    if npm is None:
        print("[explorer] Node.js/npm is required (npm not found on PATH).", file=sys.stderr)
        return 1

    port = args.port
    url = f"http://localhost:{port}"

    # Already serving? Just open a tab; do not own that process.
    if _port_serving(port):
        print(f"[explorer] already running at {url}", flush=True)
        if not args.no_open:
            webbrowser.open(url)
        return 0

    def npm_run(*run_args: str) -> int:
        return subprocess.call([npm, *run_args], cwd=app_dir)

    if not (app_dir / "node_modules").exists():
        print("[explorer] first run: installing dependencies (npm install)…", file=sys.stderr)
        if npm_run("install") != 0:
            print("[explorer] npm install failed", file=sys.stderr)
            return 1

    if args.dev:
        run_args = ["run", "dev"]
    else:
        if not (app_dir / ".next" / "BUILD_ID").exists():
            print("[explorer] first run: building app (npm run build)…", file=sys.stderr)
            if npm_run("run", "build") != 0:
                print("[explorer] build failed", file=sys.stderr)
                return 1
        run_args = ["run", "start"]

    # Own process group so Ctrl-C kills the npm -> next-server tree wholesale.
    proc = subprocess.Popen(
        [npm, *run_args],
        cwd=app_dir,
        env={**os.environ, "PORT": str(port)},
        start_new_session=True,
    )

    # Everything that ends the session — Ctrl-C (SIGINT), SIGTERM, SIGHUP,
    # Ctrl-D (stdin EOF), or the server dying — sets one event; the main
    # thread waits on it with a short poll so no signal-routing edge cases
    # can leave us hung (signal.pause() + threads drops SIGINT).
    stop = threading.Event()

    def _watch() -> None:
        proc.wait()
        stop.set()

    threading.Thread(target=_watch, daemon=True).start()

    try:
        if _wait_ready(port):
            print(f"[explorer] serving at {url} — Ctrl-C or Ctrl-D to stop", flush=True)
            if not args.no_open:
                webbrowser.open(url)
        else:
            print(f"[explorer] server did not become ready on port {port}; continuing anyway (Ctrl-C to stop)", file=sys.stderr, flush=True)

        def _sig(_signum: int, _frame: object) -> None:
            stop.set()

        signal.signal(signal.SIGINT, _sig)
        signal.signal(signal.SIGTERM, _sig)
        if hasattr(signal, "SIGHUP"):
            signal.signal(signal.SIGHUP, _sig)

        if sys.stdin.isatty():
            def _stdin_eof() -> None:
                # readline() returns "" on Ctrl-D (EOF).
                try:
                    while not stop.is_set() and sys.stdin.readline() != "":
                        pass
                except Exception:
                    pass
                stop.set()

            threading.Thread(target=_stdin_eof, daemon=True).start()

        while proc.poll() is None and not stop.wait(0.5):
            pass
    except KeyboardInterrupt:
        # Only reachable during _wait_ready, before handlers are installed.
        pass
    finally:
        stop.set()
        print("[explorer] stopping…", file=sys.stderr, flush=True)
        _shutdown(proc)
        print("[explorer] stopped", file=sys.stderr, flush=True)
    return 0
