import socket
import json
import sys
import os

HOST = '127.0.0.1'
PORT = 65432

def execute_blender_logic(script_code: str):
    """
    Executes Python code inside the running Blender instance via the bridge.
    
    Args:
        script_code: The Python script string to execute.
    
    Returns:
        A dictionary containing status, stdout, and stderr.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            
            message = {
                "type": "script",
                "payload": script_code
            }
            
            s.sendall(json.dumps(message).encode('utf-8'))
            
            # Receive response
            data = s.recv(1024 * 64)
            if not data:
                return {"status": "error", "message": "No data received from Blender"}
                
            return json.loads(data.decode('utf-8'))
            
    except ConnectionRefusedError:
        return {
            "status": "error", 
            "message": f"Connection refused. Is Blender running with 'blender_bridge_server.py' active on port {PORT}?"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # If run as a script, take input from stdin or args for testing
    if len(sys.argv) > 1:
        # executing file
        with open(sys.argv[1], 'r') as f:
            code = f.read()
            print(json.dumps(execute_blender_logic(code), indent=2))
    else:
        print("Usage: python server.py <script_file>")
