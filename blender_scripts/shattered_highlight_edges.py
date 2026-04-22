"""
shattered_highlight_edges.py
Give P2V2_ShatteredGeo a "selected" orange glow edge look.

How it works:
- ShatteredGeo already has a Wireframe modifier (thickness 0.015)
- We add a second material slot: bright orange emission
- Set modifier material_offset = 1 so wireframe tubes use the orange mat
- Original mesh faces keep the existing glitch material (slot 0)
"""

import bpy

OBJ_NAME = "P2V2_ShatteredGeo"
EDGE_MAT_NAME = "P2V2_SelectedEdge"

# Blender selection highlight colour — orange
EDGE_COLOR = (1.0, 0.55, 0.05, 1.0)
EDGE_STRENGTH = 12.0   # punchy glow

obj = bpy.data.objects.get(OBJ_NAME)
if not obj:
    raise RuntimeError(f"Object '{OBJ_NAME}' not found")

# --- Build / refresh the orange edge material ---
mat = bpy.data.materials.get(EDGE_MAT_NAME)
if mat:
    bpy.data.materials.remove(mat)

mat = bpy.data.materials.new(name=EDGE_MAT_NAME)
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
nodes.clear()

out  = nodes.new('ShaderNodeOutputMaterial'); out.location = (300, 0)
emit = nodes.new('ShaderNodeEmission');        emit.location = (0, 0)
emit.inputs['Color'].default_value    = EDGE_COLOR
emit.inputs['Strength'].default_value = EDGE_STRENGTH
links.new(emit.outputs['Emission'], out.inputs['Surface'])

# --- Assign to slot 0 (use_replace=True means only wireframe tubes exist, use slot 0) ---
if len(obj.data.materials) == 0:
    obj.data.materials.append(mat)
else:
    obj.data.materials[0] = mat

# --- Point the Wireframe modifier at slot 1 ---
wire_mod = None
for m in obj.modifiers:
    if m.type == 'WIREFRAME':
        wire_mod = m
        break

if not wire_mod:
    wire_mod = obj.modifiers.new("Wire", 'WIREFRAME')
    wire_mod.thickness    = 0.015
    wire_mod.use_replace  = False

wire_mod.material_offset = 0   # wireframe tubes → slot 0 (orange)
wire_mod.use_replace     = True    # remove solid faces, show ONLY wireframe tubes

print(f"[shattered_highlight_edges] Done — {OBJ_NAME} now has orange selected-edge look")
print(f"  Edge colour: {EDGE_COLOR}, Strength: {EDGE_STRENGTH}")
print(f"  Wireframe thickness: {wire_mod.thickness}, material_offset: {wire_mod.material_offset}")
