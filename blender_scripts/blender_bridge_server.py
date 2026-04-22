import socket
import json
import threading
import sys
import os
import io
import random
import bpy
import traceback
from contextlib import redirect_stdout, redirect_stderr

HOST = '127.0.0.1'
PORT = 65432

class BlenderBridgeServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.thread = None
        # Queue for main-thread execution via bpy.app.timers
        self._pending_scripts = []
        self._pending_lock = threading.Lock()

    def start(self):
        if self.running:
            print(f"Server already running on {self.host}:{self.port}")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
        print(f"Blender Bridge Server started on {self.host}:{self.port}")
        print("  [SAFE MODE] Scripts execute on main thread via bpy.app.timers")

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        # Unregister timer if active
        try:
            if bpy.app.timers.is_registered(self._timer_callback):
                bpy.app.timers.unregister(self._timer_callback)
        except Exception:
            pass
        print("Blender Bridge Server stopped.")

    def _run_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((self.host, self.port))
                s.listen()
                self.server_socket = s

                while self.running:
                    try:
                        conn, addr = s.accept()
                        with conn:
                            self._handle_client(conn)
                    except OSError:
                        pass  # Socket closed
                    except Exception as e:
                        print(f"Accept error: {e}")
            except Exception as e:
                print(f"Server error: {e}")
            finally:
                self.running = False

    def _handle_client(self, conn):
        try:
            # Receive large payloads (up to 2MB)
            chunks = []
            conn.settimeout(2.0)
            while True:
                try:
                    chunk = conn.recv(1024 * 256)
                    if not chunk:
                        break
                    chunks.append(chunk)
                except socket.timeout:
                    break
            data = b''.join(chunks)
            conn.settimeout(None)
            if not data:
                return

            try:
                msg = json.loads(data.decode('utf-8'))
            except json.JSONDecodeError:
                self._send_response(conn, {"status": "error", "message": "Invalid JSON"})
                return

            msg_type = msg.get("type")
            payload = msg.get("payload")

            if msg_type == "ping":
                self._send_response(conn, {"status": "success", "message": "pong"})
            elif msg_type == "script":
                # Queue script for main-thread execution and wait for result
                result_event = threading.Event()
                result_holder = [None]

                with self._pending_lock:
                    self._pending_scripts.append((payload, result_event, result_holder))

                # Register timer if not already running
                try:
                    if not bpy.app.timers.is_registered(self._timer_callback):
                        bpy.app.timers.register(self._timer_callback, first_interval=0.01)
                except Exception:
                    bpy.app.timers.register(self._timer_callback, first_interval=0.01)

                # Wait for main thread to finish executing (up to 5 min)
                result_event.wait(timeout=300)

                if result_holder[0] is not None:
                    self._send_response(conn, result_holder[0])
                else:
                    self._send_response(conn, {"status": "error", "message": "Script execution timed out"})
            else:
                self._send_response(conn, {"status": "error", "message": f"Unknown message type: {msg_type}"})

        except Exception as e:
            print(f"Client handling error: {e}")

    def _send_response(self, conn, response):
        try:
            conn.sendall(json.dumps(response).encode('utf-8'))
        except Exception as e:
            print(f"Send error: {e}")

    def _timer_callback(self):
        """Called on Blender's main thread by bpy.app.timers.
        Executes one pending script per call. Returns None to unregister
        when queue is empty, keeping Blender responsive."""

        script_info = None
        with self._pending_lock:
            if self._pending_scripts:
                script_info = self._pending_scripts.pop(0)

        if script_info is None:
            # No more pending scripts, unregister timer
            return None

        script_code, result_event, result_holder = script_info
        result_holder[0] = self._execute_script(script_code)
        result_event.set()

        # Check if more scripts are queued
        with self._pending_lock:
            if self._pending_scripts:
                return 0.01  # Run again soon
        return None  # Unregister

    def _execute_script(self, script_code):
        """Execute Python code on the MAIN thread. Safe for all bpy operations."""
        f_out = io.StringIO()
        f_err = io.StringIO()

        try:
            with redirect_stdout(f_out), redirect_stderr(f_err):
                exec_context = {
                    'bpy': bpy,
                    'math': __import__('math'),
                    'Vector': __import__('mathutils').Vector,
                    'sys': sys,
                    'os': os,
                    'json': json,
                    'random': random
                }
                exec(script_code, exec_context, exec_context)

            return {
                "status": "success",
                "stdout": f_out.getvalue(),
                "stderr": f_err.getvalue()
            }
        except Exception:
            return {
                "status": "error",
                "stdout": f_out.getvalue(),
                "stderr": f_err.getvalue() + "\n" + traceback.format_exc()
            }

# Singleton instance management
if 'bridge_server' in globals():
    globals()['bridge_server'].stop()

bridge_server = BlenderBridgeServer(HOST, PORT)
bridge_server.start()

# Keep a reference to prevent garbage collection
_server_instance = bridge_server
