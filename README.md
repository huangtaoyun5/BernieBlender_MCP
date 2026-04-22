Computational Tectonic Production Line - Migration Guide
To User: This file contains all necessary information to set up and resume the "BernieBlenderMCP" project on a new machine.

1. Project Overview
Goal: Generate "Organic Ore" structures using a Self-Organizing Agent logic (RMIT Tectonic style) in Blender, triggered via an external MCP bridge. Core Tech: Blender Python (bpy), Socket Communication (JSON-RPC), MCP (Model Context Protocol).

2. Directory Structure
e:\BernieBlenderMCP\
├── blender_scripts/          # Scripts meant to run INSIDE Blender
│   ├── blender_bridge_server.py  # MAIN SERVER: Runs the socket listener
│   └── organic_ore.py            # GENERATIVE LOGIC: The core algorithm (sent to Blender)
├── mcp_server/               # Scripts meant to run OUTSIDE Blender (Terminal/MCP)
│   ├── server.py                 # Client tool to send commands
│   ├── trigger_generation.py     # Script to read organic_ore.py and execute it in Blender
│   └── test_bridge.py            # Simple connection test
└── README_MIGRATION.md       # This file
3. Setup Instructions (New Machine)
Prerequisites
Blender 4.0+ installed.
Python 3.x installed (for the external client).
Step 1: Start the Bridge (Inside Blender)
Open Blender.
Go to the Scripting tab.
Open/Import blender_scripts/blender_bridge_server.py.
Run the script.
Check: Open functionality Window > Toggle System Console on Windows to see "Blender Bridge Server started on 127.0.0.1:65432".
Step 2: Trigger Generation (External)
Open a terminal (PowerShell/CMD).
Navigate to mcp_server/.
Run:
python trigger_generation.py
Result: Blender should freeze momentarily and then display the generated "Primary_Structure", "Diagrid_Tension", and "Secondary_Fins" in the 3D Viewport.
4. Technical Context for AI Agent
Communication: The system uses a raw TCP socket on port 65432.
Logic Injection: trigger_generation.py reads the content of organic_ore.py and sends it as a string payload to Blender.
Execution Scope:
blender_bridge_server.py uses exec() to run the code.
CRITICAL: organic_ore.py is written delicately to handle exec scope. The Agent class and imports are defined locally inside BioStructure.__init__ to avoid NameError or AttributeError when running in the bridge's closure. Do not move them to global scope without testing.
Implement interactive parameters via MCP (e.g. attractor_points).
Bernie / - 2025-12-25
