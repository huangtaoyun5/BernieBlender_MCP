import bpy
import bmesh
import math
import random
from mathutils import Vector, noise

# =============================================================================
# PHASE 1 V2: DREAM DETECTION
# Only CREATES new collection + objects. Does NOT touch existing collections.
# =============================================================================

COLLECTION_NAME = "AR_PHASE1_V2"

SOFT_WHITE = (0.95, 0.97, 1.0, 1.0)
GHOST_WHITE = (0.85, 0.9, 0.95, 1.0)
FAINT_CYAN = (0.6, 0.85, 0.9, 1.0)
DIM_DATA = (0.5, 0.6, 0.65, 1.0)

def make_emission_mat(name, color, strength=1.0):
    mat = bpy.data.materials.get(name)
    if mat:
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (300, 0)
    emit = nodes.new('ShaderNodeEmission')
    emit.location = (0, 0)
    emit.inputs['Color'].default_value = color
    emit.inputs['Strength'].default_value = strength
    links.new(emit.outputs['Emission'], out.inputs['Surface'])
    return mat

def face_camera_text(obj, cam_loc):
    direction = cam_loc - obj.location
    rot_z = math.atan2(direction.y, direction.x) + math.pi / 2
    horiz_dist = math.sqrt(direction.x**2 + direction.y**2)
    rot_x = math.pi/2 - math.atan2(direction.z, horiz_dist)
    obj.rotation_euler = (rot_x, 0, rot_z)

# =============================================================================
print("=" * 60)
print("PHASE 1 V2: DREAM DETECTION — build only")
print("=" * 60)

# Read positions from existing objects
cube = bpy.data.objects.get("Cube")
CUBE_POS = cube.location.copy() if cube else Vector((5.693, -5.274, -0.078))
cam_obj = bpy.data.objects.get("zkm-kubus.fspy")
cam_loc = cam_obj.location.copy() if cam_obj else Vector((-7.54, 7.31, 1.23))

print("Cube pos: " + str([round(v,2) for v in CUBE_POS]))

# Create new collection (clean if re-run)
if COLLECTION_NAME in bpy.data.collections:
    c = bpy.data.collections[COLLECTION_NAME]
    for obj in list(c.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(c)
col = bpy.data.collections.new(COLLECTION_NAME)
bpy.context.scene.collection.children.link(col)

# --- Materials ---
mat_particle = make_emission_mat("P1V2_Particle", SOFT_WHITE, 1.2)
mat_grid = make_emission_mat("P1V2_Grid", FAINT_CYAN, 0.4)
mat_text_poem = make_emission_mat("P1V2_Poem", GHOST_WHITE, 1.8)
mat_text_data = make_emission_mat("P1V2_Data", DIM_DATA, 0.6)

# =============================================================================
# 1. PARTICLE CLOUD
# =============================================================================
print("[1/4] Particle cloud...")

bm_cloud = bmesh.new()
for i in range(150):
    r = random.uniform(0.3, 5.0) ** 0.7
    theta = random.uniform(0, 2 * math.pi)
    phi = random.uniform(0, math.pi)
    x = CUBE_POS.x + r * math.sin(phi) * math.cos(theta)
    y = CUBE_POS.y + r * math.sin(phi) * math.sin(theta)
    z = CUBE_POS.z + r * math.cos(phi) * 0.6
    z = max(z, -0.3)

    dot_size = random.uniform(0.008, 0.025)
    center = Vector((x, y, z))
    top = bm_cloud.verts.new(center + Vector((0, 0, dot_size)))
    bot = bm_cloud.verts.new(center + Vector((0, 0, -dot_size)))
    pts = []
    for j in range(4):
        a = j * math.pi / 2
        pts.append(bm_cloud.verts.new(center + Vector((math.cos(a)*dot_size, math.sin(a)*dot_size, 0))))
    bm_cloud.verts.ensure_lookup_table()
    for j in range(4):
        try:
            bm_cloud.faces.new([top, pts[j], pts[(j+1)%4]])
            bm_cloud.faces.new([bot, pts[(j+1)%4], pts[j]])
        except ValueError:
            pass

cloud_mesh = bpy.data.meshes.new("P1V2_Cloud_Mesh")
bm_cloud.to_mesh(cloud_mesh)
bm_cloud.free()
cloud_obj = bpy.data.objects.new("P1V2_ParticleCloud", cloud_mesh)
col.objects.link(cloud_obj)
cloud_obj.data.materials.append(mat_particle)

# =============================================================================
# 2. FLOOR GRID
# =============================================================================
print("[2/4] Floor grid...")

grid_curve = bpy.data.curves.new("P1V2_FloorGrid", type='CURVE')
grid_curve.dimensions = '3D'
grid_curve.bevel_depth = 0.003
grid_curve.resolution_u = 4

floor_z = 0.01
grid_range = 5.0
grid_step = 0.8

for i in range(int(grid_range * 2 / grid_step) + 1):
    y_off = -grid_range + i * grid_step + CUBE_POS.y
    sp = grid_curve.splines.new('POLY')
    sp.points.add(1)
    sp.points[0].co = (CUBE_POS.x - grid_range, y_off, floor_z, 1.0)
    sp.points[1].co = (CUBE_POS.x + grid_range, y_off, floor_z, 1.0)

for i in range(int(grid_range * 2 / grid_step) + 1):
    x_off = -grid_range + i * grid_step + CUBE_POS.x
    sp = grid_curve.splines.new('POLY')
    sp.points.add(1)
    sp.points[0].co = (x_off, CUBE_POS.y - grid_range, floor_z, 1.0)
    sp.points[1].co = (x_off, CUBE_POS.y + grid_range, floor_z, 1.0)

grid_obj = bpy.data.objects.new("P1V2_FloorGrid", grid_curve)
col.objects.link(grid_obj)
grid_obj.data.materials.append(mat_grid)

# =============================================================================
# 3. POETIC TEXT
# =============================================================================
print("[3/4] Poetic text...")

poem_data = bpy.data.curves.new("P1V2_Poem", type='FONT')
poem_data.body = "in a dream, i see one person looking\nup towards the ground"
poem_data.size = 0.15
poem_data.extrude = 0.004
poem_data.space_line = 1.3
poem_data.resolution_u = 2
poem_data.align_x = 'CENTER'
poem_obj = bpy.data.objects.new("P1V2_Poem", poem_data)
col.objects.link(poem_obj)
poem_obj.location = CUBE_POS + Vector((-1.5, 1.0, 2.5))
face_camera_text(poem_obj, cam_loc)
poem_obj.data.materials.append(mat_text_poem)

# =============================================================================
# 4. DATA LABELS
# =============================================================================
print("[4/4] Data labels...")

data_texts = [
    ("AMBIENT SCAN | MODE: PASSIVE\nSENSOR: UWB 6.489GHz | DEPTH: 17.4m", CUBE_POS + Vector((-2.0, 2.0, -0.3))),
    ("POINT DENSITY: 247pts/m2\nSTATUS: LISTENING...", CUBE_POS + Vector((1.0, 1.5, -0.3))),
]

for di, (text, pos) in enumerate(data_texts):
    td = bpy.data.curves.new("P1V2_DataLabel_" + str(di), type='FONT')
    td.body = text
    td.size = 0.06
    td.extrude = 0.002
    td.resolution_u = 1
    tobj = bpy.data.objects.new("P1V2_DataLabel_" + str(di), td)
    col.objects.link(tobj)
    tobj.location = pos
    face_camera_text(tobj, cam_loc)
    tobj.data.materials.append(mat_text_data)

print("=" * 60)
print("PHASE 1 V2: Built " + str(len(col.objects)) + " objects in " + COLLECTION_NAME)
print("Old collections untouched.")
print("=" * 60)
