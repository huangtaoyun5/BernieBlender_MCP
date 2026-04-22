from server import execute_blender_logic
import json

code = "print('Hello from Antigravity!'); 2 + 2"
result = execute_blender_logic(code)
print(json.dumps(result, indent=2))
