import sys
import os
from server import execute_blender_logic
import json

# Path to the organic_ore.py script
SCRIPT_PATH = r"e:/BernieBlenderMCP/blender_scripts/organic_ore.py"

def trigger_organic_generation():
    if not os.path.exists(SCRIPT_PATH):
        print(f"Error: Script not found at {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, 'r') as f:
        script_content = f.read()
    
    # Use raw string for the wrapper and format manually or just concat
    # We need to set the sys.path so it can find local modules if needed (though everything is in one file now)
    
    dir_path = os.path.dirname(SCRIPT_PATH).replace('\\', '/')
    
    wrapper_header = f"import sys\nimport os\nsys.path.append(r'{dir_path}')\n"
    
    wrapper_footer = """
# Force execution
try:
    if 'BioStructure' in locals():
        print("Instantiating BioStructure...")
        sim = BioStructure()
        sim.init_agents()
        sim.run_simulation()
        print("Simulation Triggered Successfully.")
    else:
        print("Error: BioStructure class not found in locals.")
except Exception as e:
    import traceback
    print(f"Error executing BioStructure: {e}")
    print(traceback.format_exc())
"""

    payload = wrapper_header + "\n" + script_content + "\n" + wrapper_footer
    
    print("Sending generation script to Blender...")
    response = execute_blender_logic(payload)
    print(json.dumps(response, indent=2))

if __name__ == "__main__":
    trigger_organic_generation()
