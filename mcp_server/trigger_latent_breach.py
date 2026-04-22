import sys
import os
import json
import socket
import time

# Add parent dir to path so we can import server module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server import execute_blender_logic

# Path to the latent_breach_geometry.py script
SCRIPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'blender_scripts')
SCRIPT_PATH = os.path.join(SCRIPT_DIR, 'latent_breach_geometry.py')

def trigger_latent_breach():
    """Send the LATENT BREACH geometry script to Blender for execution."""

    # Resolve absolute path
    script_path = os.path.abspath(SCRIPT_PATH)
    print(f"Script path: {script_path}")

    if not os.path.exists(script_path):
        print(f"Error: Script not found at {script_path}")
        return

    with open(script_path, 'r', encoding='utf-8') as f:
        script_content = f.read()

    # Wrapper to ensure proper execution context
    dir_path = os.path.dirname(script_path).replace('\\', '/')

    wrapper_header = f"""
import sys
import os
sys.path.append(r'{dir_path}')
"""

    wrapper_footer = """
# Force execution
try:
    if 'LatentBreachGenerator' in locals():
        print("LATENT BREACH script executed successfully via wrapper.")
    else:
        print("Warning: LatentBreachGenerator not found, attempting manual execution...")
        exec(open(r'""" + script_path.replace('\\', '/') + """', 'r').read())
except Exception as e:
    import traceback
    print(f"Error in LATENT BREACH execution: {e}")
    print(traceback.format_exc())
"""

    payload = wrapper_header + "\n" + script_content + "\n" + wrapper_footer

    print("=" * 50)
    print("LATENT BREACH — Sending to Blender...")
    print(f"  Payload size: {len(payload)} bytes")
    print("  This may take 30-60 seconds (agent simulation + geometry build)")
    print("=" * 50)

    # Send with larger timeout since generation is slow
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 65432))
            s.settimeout(120)  # 2 minute timeout for complex generation

            message = {
                "type": "script",
                "payload": payload
            }

            s.sendall(json.dumps(message).encode('utf-8'))

            # Receive response (may be large)
            chunks = []
            while True:
                try:
                    chunk = s.recv(1024 * 256)
                    if not chunk:
                        break
                    chunks.append(chunk)
                except socket.timeout:
                    break

            data = b''.join(chunks)
            if data:
                response = json.loads(data.decode('utf-8'))
                print("\n" + "=" * 50)
                print(f"Status: {response.get('status', 'unknown')}")
                if response.get('stdout'):
                    print("\n--- Blender Output ---")
                    print(response['stdout'])
                if response.get('stderr'):
                    print("\n--- Errors ---")
                    print(response['stderr'])
                print("=" * 50)
            else:
                print("No response received from Blender")

    except ConnectionRefusedError:
        print("\nError: Cannot connect to Blender!")
        print("Make sure you've run blender_bridge_server.py inside Blender first.")
        print("See setup instructions below.")
        print_setup_instructions()
    except Exception as e:
        print(f"\nError: {e}")


def print_setup_instructions():
    print("""
╔══════════════════════════════════════════════════════════════╗
║              LATENT BREACH — MCP 設定指南                     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  步驟 1: 開啟 Blender                                        ║
║    → 開啟 zkmLatent.blend                                    ║
║                                                              ║
║  步驟 2: 在 Blender 中啟動橋接伺服器                           ║
║    → 切換到 Scripting 分頁                                    ║
║    → 點擊 Open → 選擇                                        ║
║      blender_scripts/blender_bridge_server.py                ║
║    → 按下 ▶ Run Script                                       ║
║    → 確認系統主控台顯示:                                      ║
║      "Blender Bridge Server started on 127.0.0.1:65432"     ║
║                                                              ║
║  步驟 3: 回到這裡執行觸發腳本                                  ║
║    → python trigger_latent_breach.py                         ║
║                                                              ║
║  注意:                                                       ║
║    → Windows: 在 Blender 中開啟系統主控台                      ║
║      Window > Toggle System Console                          ║
║    → 可以看到生成進度                                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print_setup_instructions()
    else:
        trigger_latent_breach()
