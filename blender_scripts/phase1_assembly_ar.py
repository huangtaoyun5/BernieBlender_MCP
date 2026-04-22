import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix, noise

# =============================================================================
# PHASE 1: ASSEMBLY — AR Scanning UI Mockup (Liminal Lidar Aesthetic)
#
# Clinical, hyper-rational machine vision interface.
# Clean cyan/white wireframes, bounding boxes, telemetry overlays.
# Uses the existing fSpy camera and room geometry in latent2.blend.
# =============================================================================

COLLECTION_NAME = "AR_PHASE1"
CYAN = (0.0, 0.898, 1.0, 1.0)       # #00e5ff
WHITE = (1.0, 1.0, 1.0, 1.0)
DARK_BG = (0.039, 0.039, 0.039, 1.0)  # #0A0A0A
DIM_CYAN = (0.0, 0.4, 0.5, 1.0)

# --- Utility ---
def cleanup_collection(name):
    if name in bpy.data.collections:
        col = bpy.data.collections[name]
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(col)
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col

def make_emission_mat(name, color, strength=2.0):
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

def make_dark_matte_mat(name, color=(0.02, 0.02, 0.025, 1.0), roughness=0.95):
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
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

# =============================================================================
# MAIN
# =============================================================================
print("=" * 60)
print("PHASE 1: ASSEMBLY — AR Scanning UI")
print("=" * 60)

col = cleanup_collection(COLLECTION_NAME)

# --- Materials ---
mat_cyan_glow = make_emission_mat("AR1_Cyan_Glow", CYAN, 3.0)
mat_white_glow = make_emission_mat("AR1_White_Glow", WHITE, 1.5)
mat_dim_cyan = make_emission_mat("AR1_Dim_Cyan", DIM_CYAN, 0.8)
mat_room_dark = make_dark_matte_mat("AR1_Room_Dark", (0.015, 0.018, 0.022, 1.0))
mat_room_wall = make_dark_matte_mat("AR1_Room_Wall", (0.025, 0.028, 0.035, 1.0))
mat_label_glow = make_emission_mat("AR1_Label_Glow", (0.7, 0.95, 1.0, 1.0), 2.0)
mat_telemetry = make_emission_mat("AR1_Telemetry", (0.0, 0.5, 0.6, 1.0), 0.6)

# --- Apply dark materials to room geometry ---
print("[1/7] Setting up room materials...")
cube = bpy.data.objects.get("Cube")
if cube:
    cube.data.materials.clear()
    cube.data.materials.append(mat_room_dark)

for plane_name in ["Plane", "Plane.001", "Plane.002"]:
    obj = bpy.data.objects.get(plane_name)
    if obj:
        obj.data.materials.clear()
        obj.data.materials.append(mat_room_wall)

# --- Dark world ---
world = bpy.context.scene.world
if not world:
    world = bpy.data.worlds.new("AR_World")
    bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get('Background')
if bg:
    bg.inputs['Color'].default_value = DARK_BG
    bg.inputs['Strength'].default_value = 0.1

# --- Adjust existing light to moody/institutional ---
print("[2/7] Adjusting lighting...")
light = bpy.data.objects.get("Light")
if light and light.data:
    light.data.energy = 150
    light.data.color = (0.85, 0.9, 1.0)
    if hasattr(light.data, 'shadow_soft_size'):
        light.data.shadow_soft_size = 2.0

# Add a dim overhead area light for institutional feel
area_data = bpy.data.lights.new("AR1_OverheadArea", type='AREA')
area_data.energy = 80
area_data.size = 6.0
area_data.color = (0.8, 0.85, 0.95)
area_obj = bpy.data.objects.new("AR1_OverheadArea", area_data)
col.objects.link(area_obj)
area_obj.location = (0, 0, 6.5)

# =============================================================================
# LIDAR WIREFRAME OVERLAY — point cloud / wireframe on the Cube
# =============================================================================
print("[3/7] Creating Lidar wireframe overlay...")

if cube:
    # Wireframe copy of the cube
    wire_mesh = cube.data.copy()
    wire_obj = bpy.data.objects.new("AR1_Lidar_Wireframe", wire_mesh)
    wire_obj.location = cube.location.copy()
    wire_obj.rotation_euler = cube.rotation_euler.copy()
    wire_obj.scale = cube.scale.copy()
    col.objects.link(wire_obj)
    wire_obj.data.materials.clear()
    wire_obj.data.materials.append(mat_cyan_glow)
    # Add wireframe modifier
    mod = wire_obj.modifiers.new("LidarWire", 'WIREFRAME')
    mod.thickness = 0.012
    mod.use_replace = True
    mod.use_even_offset = True

    # Point cloud simulation — small icospheres at vertices
    bm_src = bmesh.new()
    bm_src.from_mesh(cube.data)
    bm_src.transform(cube.matrix_world)

    # Create a shared tiny sphere mesh for instancing
    bm_dot = bmesh.new()
    # Simple octahedron as point marker
    top = bm_dot.verts.new(Vector((0, 0, 0.015)))
    bot = bm_dot.verts.new(Vector((0, 0, -0.015)))
    pts = []
    for i in range(4):
        angle = i * math.pi / 2
        pts.append(bm_dot.verts.new(Vector((math.cos(angle)*0.015, math.sin(angle)*0.015, 0))))
    bm_dot.verts.ensure_lookup_table()
    for i in range(4):
        try:
            bm_dot.faces.new([top, pts[i], pts[(i+1)%4]])
            bm_dot.faces.new([bot, pts[(i+1)%4], pts[i]])
        except ValueError:
            pass
    dot_mesh = bpy.data.meshes.new("AR1_DotMesh")
    bm_dot.to_mesh(dot_mesh)
    bm_dot.free()

    # Place point markers at cube vertices and along edges
    point_positions = []
    for v in bm_src.verts:
        point_positions.append(v.co.copy())
    # Add points along edges for denser point cloud
    for e in bm_src.edges:
        for t in [0.25, 0.5, 0.75]:
            p = e.verts[0].co.lerp(e.verts[1].co, t)
            point_positions.append(p)
    # Add points on faces
    for f in bm_src.faces:
        center = f.calc_center_median()
        point_positions.append(center)
        for v in f.verts:
            point_positions.append(center.lerp(v.co, 0.5))

    bm_src.free()

    # Merge all points into one mesh object
    bm_cloud = bmesh.new()
    for pos in point_positions:
        bm_temp = bmesh.new()
        bm_temp.from_mesh(dot_mesh)
        for v in bm_temp.verts:
            v.co += pos
        # Transfer to combined
        offset = len(bm_cloud.verts)
        vert_map = {}
        for v in bm_temp.verts:
            nv = bm_cloud.verts.new(v.co)
            vert_map[v.index] = nv
        bm_cloud.verts.ensure_lookup_table()
        for f in bm_temp.faces:
            try:
                bm_cloud.faces.new([vert_map[v.index] for v in f.verts])
            except (ValueError, KeyError):
                pass
        bm_temp.free()

    cloud_mesh = bpy.data.meshes.new("AR1_PointCloud_Mesh")
    bm_cloud.to_mesh(cloud_mesh)
    bm_cloud.free()

    cloud_obj = bpy.data.objects.new("AR1_PointCloud", cloud_mesh)
    col.objects.link(cloud_obj)
    cloud_obj.data.materials.append(mat_cyan_glow)

    # Also add scan lines on floor around the cube (lidar sweep)
    scan_curve = bpy.data.curves.new("AR1_ScanLines", type='CURVE')
    scan_curve.dimensions = '3D'
    scan_curve.bevel_depth = 0.004
    scan_curve.resolution_u = 12

    for ring in range(8):
        spline = scan_curve.splines.new('POLY')
        radius = 1.2 + ring * 0.25
        num_pts = 48
        spline.points.add(num_pts)  # +1 for closing
        for i in range(num_pts + 1):
            angle = (i / num_pts) * 2 * math.pi
            x = math.cos(angle) * radius
            y = math.sin(angle) * radius
            z = 0.01  # just above floor
            # Add slight noise
            n = noise.noise(Vector((x*0.5, y*0.5, ring*0.3)))
            z += n * 0.02
            spline.points[i].co = (x, y, z, 1.0)

    scan_obj = bpy.data.objects.new("AR1_ScanLines", scan_curve)
    col.objects.link(scan_obj)
    scan_obj.data.materials.append(mat_dim_cyan)

# =============================================================================
# BOUNDING BOX — crisp 3D bounding box around the cube
# =============================================================================
print("[4/7] Creating bounding box...")

if cube:
    bb_min = Vector((-1.0, -1.0, -1.0))
    bb_max = Vector((1.0, 1.0, 1.0))
    # Slightly larger than the cube
    margin = 0.15
    bb_min -= Vector((margin, margin, margin))
    bb_max += Vector((margin, margin, margin))

    corners = [
        Vector((bb_min.x, bb_min.y, bb_min.z)),
        Vector((bb_max.x, bb_min.y, bb_min.z)),
        Vector((bb_max.x, bb_max.y, bb_min.z)),
        Vector((bb_min.x, bb_max.y, bb_min.z)),
        Vector((bb_min.x, bb_min.y, bb_max.z)),
        Vector((bb_max.x, bb_min.y, bb_max.z)),
        Vector((bb_max.x, bb_max.y, bb_max.z)),
        Vector((bb_min.x, bb_max.y, bb_max.z)),
    ]

    edges_idx = [
        (0,1),(1,2),(2,3),(3,0),  # bottom
        (4,5),(5,6),(6,7),(7,4),  # top
        (0,4),(1,5),(2,6),(3,7),  # verticals
    ]

    bm_bb = bmesh.new()
    bm_verts = [bm_bb.verts.new(c) for c in corners]
    bm_bb.verts.ensure_lookup_table()
    for e0, e1 in edges_idx:
        bm_bb.edges.new((bm_verts[e0], bm_verts[e1]))

    bb_mesh = bpy.data.meshes.new("AR1_BBox_Mesh")
    bm_bb.to_mesh(bb_mesh)
    bm_bb.free()

    bb_obj = bpy.data.objects.new("AR1_BoundingBox", bb_mesh)
    col.objects.link(bb_obj)
    bb_obj.data.materials.append(mat_white_glow)
    mod_wire = bb_obj.modifiers.new("BBWire", 'WIREFRAME')
    mod_wire.thickness = 0.018
    mod_wire.use_replace = True

    # Corner bracket marks (L-shaped indicators at each corner)
    bracket_len = 0.3
    bm_brackets = bmesh.new()
    for ci, corner in enumerate(corners):
        # Determine which directions point inward
        cx = 1 if corner.x < 0 else -1
        cy = 1 if corner.y < 0 else -1
        cz = 1 if corner.z < 0 else -1

        # Three short lines from corner
        v0 = bm_brackets.verts.new(corner)
        v1 = bm_brackets.verts.new(corner + Vector((cx * bracket_len, 0, 0)))
        v2 = bm_brackets.verts.new(corner + Vector((0, cy * bracket_len, 0)))
        v3 = bm_brackets.verts.new(corner + Vector((0, 0, cz * bracket_len)))
        bm_brackets.verts.ensure_lookup_table()
        bm_brackets.edges.new((v0, v1))
        bm_brackets.edges.new((v0, v2))
        bm_brackets.edges.new((v0, v3))

    bracket_mesh = bpy.data.meshes.new("AR1_Brackets_Mesh")
    bm_brackets.to_mesh(bracket_mesh)
    bm_brackets.free()

    bracket_obj = bpy.data.objects.new("AR1_CornerBrackets", bracket_mesh)
    col.objects.link(bracket_obj)
    bracket_obj.data.materials.append(mat_cyan_glow)
    mod_bw = bracket_obj.modifiers.new("BracketWire", 'WIREFRAME')
    mod_bw.thickness = 0.025
    mod_bw.use_replace = True

# =============================================================================
# CROSSHAIR — center target reticle
# =============================================================================
print("[5/7] Creating crosshair...")

# Position crosshair at center of cube, projected slightly toward camera
crosshair_pos = Vector((0, 0, 0))  # Cube center

bm_cross = bmesh.new()
# Horizontal line
ch_size = 0.2
gap = 0.06
v1 = bm_cross.verts.new(Vector((-ch_size, 0, 0)) + crosshair_pos)
v2 = bm_cross.verts.new(Vector((-gap, 0, 0)) + crosshair_pos)
v3 = bm_cross.verts.new(Vector((gap, 0, 0)) + crosshair_pos)
v4 = bm_cross.verts.new(Vector((ch_size, 0, 0)) + crosshair_pos)
# Vertical line
v5 = bm_cross.verts.new(Vector((0, 0, -ch_size)) + crosshair_pos)
v6 = bm_cross.verts.new(Vector((0, 0, -gap)) + crosshair_pos)
v7 = bm_cross.verts.new(Vector((0, 0, gap)) + crosshair_pos)
v8 = bm_cross.verts.new(Vector((0, 0, ch_size)) + crosshair_pos)
bm_cross.verts.ensure_lookup_table()
bm_cross.edges.new((v1, v2))
bm_cross.edges.new((v3, v4))
bm_cross.edges.new((v5, v6))
bm_cross.edges.new((v7, v8))
# Small diamond
d = 0.04
dv = [
    bm_cross.verts.new(crosshair_pos + Vector((d, 0, 0))),
    bm_cross.verts.new(crosshair_pos + Vector((0, 0, d))),
    bm_cross.verts.new(crosshair_pos + Vector((-d, 0, 0))),
    bm_cross.verts.new(crosshair_pos + Vector((0, 0, -d))),
]
bm_cross.verts.ensure_lookup_table()
for i in range(4):
    bm_cross.edges.new((dv[i], dv[(i+1)%4]))

cross_mesh = bpy.data.meshes.new("AR1_Crosshair_Mesh")
bm_cross.to_mesh(cross_mesh)
bm_cross.free()

cross_obj = bpy.data.objects.new("AR1_Crosshair", cross_mesh)
col.objects.link(cross_obj)
cross_obj.data.materials.append(mat_white_glow)
mod_cw = cross_obj.modifiers.new("CrossWire", 'WIREFRAME')
mod_cw.thickness = 0.012
mod_cw.use_replace = True

# =============================================================================
# TEXT LABELS — Object detection label + telemetry data
# =============================================================================
print("[6/7] Creating UI text labels...")

# Main object label - positioned near top-right of bounding box
label_data = bpy.data.curves.new("AR1_Label_Main", type='FONT')
label_data.body = "Object: Chair | Confidence: 99.8% | Depth: 2.4m"
label_data.size = 0.09
label_data.extrude = 0.005
label_data.resolution_u = 2
label_obj = bpy.data.objects.new("AR1_Label_Main", label_data)
col.objects.link(label_obj)
label_obj.location = (0.5, -1.2, 1.3)
label_obj.rotation_euler = (math.radians(90), 0, math.radians(-35))
label_obj.data.materials.append(mat_label_glow)

# Sub-label: object class
sublabel_data = bpy.data.curves.new("AR1_Label_Sub", type='FONT')
sublabel_data.body = "CLASS: FURNITURE.SEATING.001"
sublabel_data.size = 0.06
sublabel_data.extrude = 0.003
sublabel_data.resolution_u = 2
sublabel_obj = bpy.data.objects.new("AR1_Label_Sub", sublabel_data)
col.objects.link(sublabel_obj)
sublabel_obj.location = (0.5, -1.2, 1.1)
sublabel_obj.rotation_euler = (math.radians(90), 0, math.radians(-35))
sublabel_obj.data.materials.append(mat_dim_cyan)

# Status label
status_data = bpy.data.curves.new("AR1_Label_Status", type='FONT')
status_data.body = "STATUS: NOMINAL | TRACKING: ACTIVE"
status_data.size = 0.06
status_data.extrude = 0.003
status_data.resolution_u = 2
status_obj = bpy.data.objects.new("AR1_Label_Status", status_data)
col.objects.link(status_obj)
status_obj.location = (0.5, -1.2, 0.95)
status_obj.rotation_euler = (math.radians(90), 0, math.radians(-35))
status_obj.data.materials.append(mat_dim_cyan)

# Telemetry data blocks - positioned around the edges
telemetry_texts = [
    ("UWB: 6.489GHz | CH9 | PRF64M\nRSSI: -67dBm | FP_IDX: 742\nRANGE: 2.413m | NLOS: 0.02", (-3.5, 3.0, 3.5)),
    ("HESSIAN CURVATURE TENSOR:\n| 0.847  -0.231  0.015 |\n|-0.231   0.563  0.089 |\n| 0.015   0.089  0.412 |", (-3.5, 3.0, 2.2)),
    ("LIDAR POINT DENSITY: 847pts/m2\nSCAN RATE: 240Hz | FOV: 120deg\nMESH CONFIDENCE: 0.994", (2.0, -2.5, 3.5)),
    ("VEC[0]: [0.847, -0.231, 0.563]\nVEC[1]: [-0.123, 0.945, 0.089]\nEIGEN: [1.247, 0.563, 0.012]", (2.0, -2.5, 2.2)),
]

for ti, (text, pos) in enumerate(telemetry_texts):
    td = bpy.data.curves.new("AR1_Telemetry_" + str(ti), type='FONT')
    td.body = text
    td.size = 0.05
    td.extrude = 0.002
    td.resolution_u = 1
    tobj = bpy.data.objects.new("AR1_Telemetry_" + str(ti), td)
    col.objects.link(tobj)
    tobj.location = pos
    tobj.rotation_euler = (math.radians(90), 0, math.radians(-35))
    tobj.data.materials.append(mat_telemetry)

# Connecting lines from label to bounding box (leader lines)
leader_curve = bpy.data.curves.new("AR1_LeaderLines", type='CURVE')
leader_curve.dimensions = '3D'
leader_curve.bevel_depth = 0.005
leader_curve.resolution_u = 4

# Line from bbox corner to main label
spline = leader_curve.splines.new('POLY')
spline.points.add(2)
spline.points[0].co = (1.15, -1.15, 1.15, 1.0)  # bbox corner
spline.points[1].co = (0.8, -1.18, 1.25, 1.0)   # elbow
spline.points[2].co = (0.5, -1.2, 1.35, 1.0)     # label start

leader_obj = bpy.data.objects.new("AR1_LeaderLines", leader_curve)
col.objects.link(leader_obj)
leader_obj.data.materials.append(mat_dim_cyan)

# =============================================================================
# DEPTH/DISTANCE MARKERS — thin vertical measurement lines
# =============================================================================
print("[7/7] Creating depth markers...")

# Distance tick marks along the floor
tick_curve = bpy.data.curves.new("AR1_DepthTicks", type='CURVE')
tick_curve.dimensions = '3D'
tick_curve.bevel_depth = 0.003

for i in range(8):
    dist = 1.0 + i * 0.5
    spline = tick_curve.splines.new('POLY')
    spline.points.add(1)
    # Small vertical tick at distance
    angle = math.radians(-35)  # roughly toward camera
    x = math.cos(angle) * dist
    y = math.sin(angle) * dist
    spline.points[0].co = (x, y, 0.01, 1.0)
    spline.points[1].co = (x, y, 0.12, 1.0)

tick_obj = bpy.data.objects.new("AR1_DepthTicks", tick_curve)
col.objects.link(tick_obj)
tick_obj.data.materials.append(mat_dim_cyan)

# =============================================================================
# RENDER SETTINGS
# =============================================================================
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.film_transparent = False
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100

# Use the fSpy camera
cam = bpy.data.objects.get("zkm-kubus.fspy")
if cam:
    scene.camera = cam

print("=" * 60)
print("PHASE 1: ASSEMBLY — Setup Complete!")
total = len(col.objects)
print("Total AR overlay objects: " + str(total))
print("Ready to render.")
print("=" * 60)
