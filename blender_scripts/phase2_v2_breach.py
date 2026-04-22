import bpy
import bmesh
import math
import random
from mathutils import Vector, noise

# =============================================================================
# PHASE 2 V2: BREACH — YOLO gone haywire
# Positioned using actual screen-to-world mapping for the fSpy 16mm camera.
# Room: Floor Z=0, Back wall Y=-5.4, Right wall X=5.87
# Camera at (-7.54, 7.31, 1.23)
# =============================================================================

COLLECTION_NAME = "AR_PHASE2_V2"

RED = (0.761, 0.231, 0.133, 1.0)
RED_HOT = (1.0, 0.12, 0.05, 1.0)
RED_DIM = (0.4, 0.06, 0.02, 1.0)
WHITE_FLICKER = (1.0, 0.9, 0.85, 1.0)

def make_emission_mat(name, color, strength=5.0):
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

def make_semitransparent_mat(name, color, emit_strength=3.0, alpha=0.3):
    mat = bpy.data.materials.get(name)
    if mat:
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (500, 0)
    mix = nodes.new('ShaderNodeMixShader')
    mix.location = (300, 0)
    mix.inputs['Fac'].default_value = alpha
    transparent = nodes.new('ShaderNodeBsdfTransparent')
    transparent.location = (0, 100)
    emit = nodes.new('ShaderNodeEmission')
    emit.location = (0, -100)
    emit.inputs['Color'].default_value = color
    emit.inputs['Strength'].default_value = emit_strength
    links.new(transparent.outputs['BSDF'], mix.inputs[1])
    links.new(emit.outputs['Emission'], mix.inputs[2])
    links.new(mix.outputs['Shader'], out.inputs['Surface'])
    return mat

def make_glitch_mat(name):
    mat = bpy.data.materials.get(name)
    if mat:
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (600, 0)
    emit = nodes.new('ShaderNodeEmission')
    emit.location = (300, 0)
    emit.inputs['Strength'].default_value = 6.0
    ntex = nodes.new('ShaderNodeTexNoise')
    ntex.location = (-300, 0)
    ntex.inputs['Scale'].default_value = 5.0
    ntex.inputs['Detail'].default_value = 10.0
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (0, 0)
    ramp.color_ramp.elements[0].color = (0.5, 0.0, 0.0, 1.0)
    ramp.color_ramp.elements[0].position = 0.2
    ramp.color_ramp.elements[1].color = (1.0, 0.15, 0.05, 1.0)
    ramp.color_ramp.elements[1].position = 0.8
    links.new(ntex.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], emit.inputs['Color'])
    links.new(emit.outputs['Emission'], out.inputs['Surface'])
    return mat

def face_camera(obj, cam_loc):
    direction = cam_loc - obj.location
    rot_z = math.atan2(direction.y, direction.x) + math.pi / 2
    horiz_dist = math.sqrt(direction.x**2 + direction.y**2)
    rot_x = math.pi/2 - math.atan2(direction.z, horiz_dist)
    obj.rotation_euler = (rot_x, 0, rot_z)

# =============================================================================
print("=" * 60)
print("PHASE 2 V2: BREACH (corrected positions)")
print("=" * 60)

cube = bpy.data.objects.get("Cube")
CUBE_POS = cube.location.copy() if cube else Vector((5.693, -5.274, -0.078))
cam_obj = bpy.data.objects.get("zkm-kubus.fspy")
cam_loc = cam_obj.location.copy() if cam_obj else Vector((-7.54, 7.31, 1.23))

# Clean rebuild
if COLLECTION_NAME in bpy.data.collections:
    c = bpy.data.collections[COLLECTION_NAME]
    for obj in list(c.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(c)
col = bpy.data.collections.new(COLLECTION_NAME)
bpy.context.scene.collection.children.link(col)

# Materials
mat_red_line = make_emission_mat("P2V2_RedLine", RED, 10.0)
mat_red_hot = make_emission_mat("P2V2_RedHot", RED_HOT, 15.0)
mat_red_fill = make_semitransparent_mat("P2V2_RedFill", RED_HOT, 4.0, 0.35)
mat_red_dim = make_emission_mat("P2V2_RedDim", RED_DIM, 4.0)
mat_glitch = make_glitch_mat("P2V2_Glitch")
mat_text_white = make_emission_mat("P2V2_TextWhite", WHITE_FLICKER, 12.0)
mat_text_red = make_emission_mat("P2V2_TextRed", RED, 12.0)

# =============================================================================
# HELPERS
# =============================================================================
def make_bbox_2d(name, center, width, height, mat_outline, mat_fill, line_thick=0.04):
    hw = width / 2
    hh = height / 2
    # Filled face
    bm = bmesh.new()
    v0 = bm.verts.new(Vector((-hw, 0, -hh)))
    v1 = bm.verts.new(Vector(( hw, 0, -hh)))
    v2 = bm.verts.new(Vector(( hw, 0,  hh)))
    v3 = bm.verts.new(Vector((-hw, 0,  hh)))
    bm.verts.ensure_lookup_table()
    bm.faces.new([v0, v1, v2, v3])
    fm = bpy.data.meshes.new(name + "_Fill")
    bm.to_mesh(fm)
    bm.free()
    fo = bpy.data.objects.new(name + "_Fill", fm)
    fo.location = center
    col.objects.link(fo)
    face_camera(fo, cam_loc)
    fo.data.materials.append(mat_fill)

    # Outline
    bm2 = bmesh.new()
    v0 = bm2.verts.new(Vector((-hw, 0, -hh)))
    v1 = bm2.verts.new(Vector(( hw, 0, -hh)))
    v2 = bm2.verts.new(Vector(( hw, 0,  hh)))
    v3 = bm2.verts.new(Vector((-hw, 0,  hh)))
    bm2.verts.ensure_lookup_table()
    bm2.edges.new((v0, v1))
    bm2.edges.new((v1, v2))
    bm2.edges.new((v2, v3))
    bm2.edges.new((v3, v0))
    om = bpy.data.meshes.new(name + "_Outline")
    bm2.to_mesh(om)
    bm2.free()
    oo = bpy.data.objects.new(name + "_Outline", om)
    oo.location = center
    col.objects.link(oo)
    face_camera(oo, cam_loc)
    oo.data.materials.append(mat_outline)
    mod = oo.modifiers.new("Wire", 'WIREFRAME')
    mod.thickness = line_thick
    mod.use_replace = True

def make_arrow_2d(name, position, direction_vec, length, head_size=0.25):
    d = direction_vec.normalized()
    up = Vector((0, 0, 1))
    if abs(d.dot(up)) > 0.9:
        up = Vector((1, 0, 0))
    perp = d.cross(up).normalized()
    tip = Vector((0, 0, 0))
    tail = -d * length
    head_base = -d * head_size
    bm = bmesh.new()
    v_tail = bm.verts.new(tail)
    v_base = bm.verts.new(head_base)
    bm.verts.ensure_lookup_table()
    bm.edges.new((v_tail, v_base))
    v_tip = bm.verts.new(tip)
    v_l = bm.verts.new(head_base + perp * head_size * 0.6)
    v_r = bm.verts.new(head_base - perp * head_size * 0.6)
    bm.verts.ensure_lookup_table()
    bm.faces.new([v_tip, v_l, v_r])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = position
    col.objects.link(obj)
    face_camera(obj, cam_loc)
    obj.data.materials.append(mat_red_hot)
    mod = obj.modifiers.new("Wire", 'WIREFRAME')
    mod.thickness = 0.04
    mod.use_replace = False

def make_triangle_2d(name, position, size=0.25):
    bm = bmesh.new()
    v0 = bm.verts.new(Vector((0, 0, size)))
    v1 = bm.verts.new(Vector((-size * 0.866, 0, -size * 0.5)))
    v2 = bm.verts.new(Vector(( size * 0.866, 0, -size * 0.5)))
    bm.verts.ensure_lookup_table()
    bm.faces.new([v0, v1, v2])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = position
    col.objects.link(obj)
    face_camera(obj, cam_loc)
    obj.data.materials.append(mat_red_hot)

def make_circle_2d(name, position, radius=0.2):
    bm = bmesh.new()
    cv = bm.verts.new(Vector((0, 0, 0)))
    ring = []
    for i in range(20):
        a = i / 20 * 2 * math.pi
        ring.append(bm.verts.new(Vector((math.cos(a)*radius, 0, math.sin(a)*radius))))
    bm.verts.ensure_lookup_table()
    for i in range(20):
        try:
            bm.faces.new([cv, ring[i], ring[(i+1)%20]])
        except ValueError:
            pass
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = position
    col.objects.link(obj)
    face_camera(obj, cam_loc)
    obj.data.materials.append(mat_red_fill)

def make_line(name, start, end):
    curve = bpy.data.curves.new(name, type='CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = 0.012
    curve.resolution_u = 2
    sp = curve.splines.new('POLY')
    sp.points.add(1)
    sp.points[0].co = (start.x, start.y, start.z, 1.0)
    sp.points[1].co = (end.x, end.y, end.z, 1.0)
    obj = bpy.data.objects.new(name, curve)
    col.objects.link(obj)
    obj.data.materials.append(mat_red_line)

# =============================================================================
# 1. YOLO BOUNDING BOXES — placed at real Kubus objects
#    World positions derived from screen-to-world mapping
# =============================================================================
print("[1/6] YOLO bounding boxes...")

# Positions mapped from photo landmarks:
# Piano: back wall, center-right → screen ~(0.44, 0.40)
# Left wall speakers: left side → screen ~(0.65, 0.50)
# Ceiling lights: upper area → screen ~(0.50, 0.65)
# Floor foreground: lower-center → screen ~(0.50, 0.35)
# Right wall: right edge → screen ~(0.25, 0.45)
# Person (hypothetical): center-left → screen ~(0.55, 0.44)

detections = [
    # (name, world_pos, box_w, box_h, label, scale_factor_for_distance)
    ("piano",    Vector((3, -5.2, 1.0)),   1.8, 1.2,  "it still remembers the weight\nof the last occupant."),
    ("speaker",  Vector((-5, -4, 3.0)),    1.0, 1.0,  "SIGNAL: [REDACTED]"),
    ("ceiling",  Vector((-2, -2, 5.5)),    3.0, 2.0,  "DO NOT LOOK AWAY."),
    ("person",   Vector((-4, 1, 1.2)),     1.2, 2.2,  "their biological signature\nis decaying."),
    ("floor",    Vector((-2, 1, 0.05)),    4.0, 2.5,  "this one has not blinked."),
    ("door",     Vector((5.5, -3, 2.0)),   1.0, 2.0,  "it opened once.\nno one came through."),
    ("stage",    Vector((0, -5.2, 1.5)),   2.5, 2.0,  "OBJECT: [REDACTED]"),
]

for di, (det_name, pos, bw, bh, label) in enumerate(detections):
    # Scale box size by distance to camera (closer = bigger in view)
    dist = (cam_loc - pos).length
    # Boxes need to be bigger for far objects to appear similar screen size
    make_bbox_2d("P2V2_Det_" + det_name, pos, bw, bh, mat_red_line, mat_red_fill, 0.04)

    # Label
    td = bpy.data.curves.new("P2V2_Lbl_" + det_name, type='FONT')
    td.body = label
    td.size = 0.12 + (dist / 30.0) * 0.06  # slightly bigger for farther
    td.extrude = 0.005
    td.space_line = 1.1
    td.resolution_u = 1
    tobj = bpy.data.objects.new("P2V2_Lbl_" + det_name, td)
    col.objects.link(tobj)
    label_pos = pos + Vector((0, 0, bh / 2 + 0.2))
    tobj.location = label_pos
    face_camera(tobj, cam_loc)
    tobj.data.materials.append(mat_text_red if di % 2 == 0 else mat_text_white)

    # Connection line
    make_line("P2V2_Conn_" + det_name, pos + Vector((0, 0, bh/2)), label_pos)

# =============================================================================
# 2. ARROWS
# =============================================================================
print("[2/6] Arrows...")

arrows = [
    (Vector((3, -5.2, 3.5)),   Vector((0, 0, -1)), 1.5),   # down to piano
    (Vector((-4, 1, 4.0)),     Vector((0, 0, -1)), 1.2),   # down to person
    (Vector((-2, 1, -0.5)),    Vector((0, 0, 1)),  1.5),   # up from floor
    (Vector((5.5, -3, -0.3)),  Vector((0, 0, 1)),  2.0),   # up to door
    (Vector((-6, -2, 1.5)),    Vector((1, -0.5, 0)), 1.5), # sideways toward stage
]

for ai, (pos, d, length) in enumerate(arrows):
    make_arrow_2d("P2V2_Arrow_" + str(ai), pos, d, length, 0.3)

# =============================================================================
# 3. WARNING TRIANGLES + CIRCLES — spread across the room
# =============================================================================
print("[3/6] Warning symbols...")

triangles = [
    Vector((-5, -3, 5.0)),    # left upper (near ceiling)
    Vector((2, -5, 4.0)),     # back wall upper
    Vector((5.5, -1, 4.5)),   # right wall upper
    Vector((-3, 3, 2.0)),     # foreground left
    Vector((0, -4, 0.5)),     # floor near stage
]

for ti, pos in enumerate(triangles):
    make_triangle_2d("P2V2_Tri_" + str(ti), pos, random.uniform(0.2, 0.4))

circles = [
    Vector((-6, -5, 2.5)),    # far left corner
    Vector((4, -5, 5.0)),     # back ceiling
    Vector((5.5, 1, 1.0)),    # right wall low
    Vector((-1, 0, 3.5)),     # center mid-height
]

for ci, pos in enumerate(circles):
    make_circle_2d("P2V2_Circle_" + str(ci), pos, random.uniform(0.2, 0.35))

# =============================================================================
# 4. FLOATING EMOTIONAL TEXT — spread across full frame
# =============================================================================
print("[4/6] Emotional text...")

texts = [
    # text, position, size, material
    ("[WARNING] BIOMETRIC ANOMALY\nCONFIDENCE: 1.2%",    Vector((-3, 3, 0.3)),    0.10, mat_text_red),
    ("why is it so cold...",                               Vector((-5, -1, 2.5)),   0.16, mat_text_white),
    ("nothing feels real!!!",                              Vector((4, -3, 4.5)),    0.15, mat_text_red),
    ("who is writing\nthese sentences?",                   Vector((1, -5, 3.5)),    0.12, mat_text_white),
    ("CONFIDENCE: NaN%",                                   Vector((-4, -4, 5.5)),   0.12, mat_text_red),
    ("your gaze is the instrument\nof its own alienation.",Vector((5.5, 0, 3.0)),   0.09, mat_text_white),
    ("a game you do not know\nyou are playing",            Vector((-6, 1, 4.0)),    0.10, mat_text_red),
]

for fi, (text, pos, size, mat) in enumerate(texts):
    td = bpy.data.curves.new("P2V2_Float_" + str(fi), type='FONT')
    td.body = text
    td.size = size
    td.extrude = 0.005
    td.space_line = 1.15
    td.resolution_u = 1
    tobj = bpy.data.objects.new("P2V2_Float_" + str(fi), td)
    col.objects.link(tobj)
    tobj.location = pos
    face_camera(tobj, cam_loc)
    rx, ry, rz = tobj.rotation_euler
    tobj.rotation_euler = (rx + random.uniform(-0.05, 0.05), random.uniform(-0.03, 0.03), rz)
    tobj.data.materials.append(mat)

# =============================================================================
# 5. 3D SHATTERED GEOMETRY — at the Cube (wall intersection)
# =============================================================================
print("[5/6] Shattered geometry...")

bm = bmesh.new()
bm.from_mesh(bpy.data.objects["Cube"].data)
edges = list(bm.edges)
bmesh.ops.subdivide_edges(bm, edges=edges, cuts=3, use_grid_fill=True)

for v in bm.verts:
    p = v.co.copy()
    n = noise.noise_vector(p * 1.5 + Vector((7.7, 3.1, 0)))
    strength = 0.3 + random.uniform(0, 0.5)
    disp = Vector(n) * strength
    disp.z *= 2.0
    if random.random() < 0.06:
        spike_dir = p.normalized() if p.length > 0.001 else Vector((0,0,1))
        disp += spike_dir * random.uniform(0.3, 1.0)
    v.co += disp

dm = bpy.data.meshes.new("P2V2_Shattered_Mesh")
bm.to_mesh(dm)
bm.free()
do = bpy.data.objects.new("P2V2_ShatteredGeo", dm)
do.location = CUBE_POS
col.objects.link(do)
do.data.materials.append(mat_glitch)
mod = do.modifiers.new("Wire", 'WIREFRAME')
mod.thickness = 0.015
mod.use_replace = False

# Tendrils
tc = bpy.data.curves.new("P2V2_Tendrils", type='CURVE')
tc.dimensions = '3D'
tc.bevel_depth = 0.010
tc.resolution_u = 6
for ti in range(6):
    sp = tc.splines.new('NURBS')
    np = 25
    sp.points.add(np - 1)
    sa = random.uniform(0, 2 * math.pi)
    pos = CUBE_POS + Vector((math.cos(sa)*0.6, math.sin(sa)*0.6, random.uniform(-0.3, 0.3)))
    for i in range(np):
        t = i / np
        n = noise.noise_vector(pos * 0.8 + Vector((ti * 3.3, 0, t * 2)))
        vel = Vector(n) * (0.10 + t * 0.20)
        vel.z += 0.05
        pos = pos + vel
        sp.points[i].co = (pos.x, pos.y, pos.z, 1.0)
    sp.use_endpoint_u = True
    sp.order_u = 4
to = bpy.data.objects.new("P2V2_Tendrils", tc)
col.objects.link(to)
to.data.materials.append(mat_glitch)

# =============================================================================
# 6. SCAN GRID on floor — across the whole visible floor
# =============================================================================
print("[6/6] Scan grid...")

sc = bpy.data.curves.new("P2V2_ScanGrid", type='CURVE')
sc.dimensions = '3D'
sc.bevel_depth = 0.006
sc.resolution_u = 4

# Floor grid covering full room: X from -8 to 6, Y from -5 to 5
for i in range(18):
    y = -5.0 + i * 0.6
    sp = sc.splines.new('POLY')
    pts = 16
    sp.points.add(pts - 1)
    for j in range(pts):
        t = j / (pts - 1)
        x = -8 + t * 14
        n = noise.noise_vector(Vector((x*0.3, y*0.3, i*0.5)))
        x += n.x * 0.08
        y_n = y + n.y * 0.08
        z = 0.02 + n.z * 0.04
        w = 0.0 if random.random() < 0.03 else 1.0
        sp.points[j].co = (x, y_n, z, w)

# Also Y-direction lines
for i in range(20):
    x = -8.0 + i * 0.7
    sp = sc.splines.new('POLY')
    pts = 14
    sp.points.add(pts - 1)
    for j in range(pts):
        t = j / (pts - 1)
        y = -5 + t * 10
        n = noise.noise_vector(Vector((x*0.3, y*0.3, i*0.3)))
        x_n = x + n.x * 0.08
        z = 0.02 + n.z * 0.04
        w = 0.0 if random.random() < 0.03 else 1.0
        sp.points[j].co = (x_n, y, z, w)

so = bpy.data.objects.new("P2V2_ScanGrid", sc)
col.objects.link(so)
so.data.materials.append(mat_red_dim)

print("=" * 60)
print("PHASE 2 V2: Built " + str(len(col.objects)) + " objects")
print("=" * 60)
