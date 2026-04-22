import bpy
import bmesh
import math
import random
from mathutils import Vector, noise

# =============================================================================
# PHASE 2: BREACH — AR Narrative Overlay (Adversarial Attack / Latent Space)
# Same room, 10 minutes later. System glitching, hallucinating poetry.
# Terracotta Red (#c23b22) replaces Cyan. Geometry distorted.
# =============================================================================

COLLECTION_NAME = "AR_PHASE2"
RED = (0.761, 0.231, 0.133, 1.0)        # #c23b22
CORRUPT_CYAN = (0.0, 0.3, 0.35, 1.0)    # faded/dying cyan
WHITE_FLICKER = (1.0, 0.9, 0.85, 1.0)
DARK_BG = (0.025, 0.02, 0.02, 1.0)

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

def make_glitch_mat(name):
    """Noisy red emission with flickering."""
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
    noise_tex = nodes.new('ShaderNodeTexNoise')
    noise_tex.location = (-300, 0)
    noise_tex.inputs['Scale'].default_value = 5.0
    noise_tex.inputs['Detail'].default_value = 10.0
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (0, 0)
    ramp.color_ramp.elements[0].color = (0.5, 0.0, 0.0, 1.0)
    ramp.color_ramp.elements[0].position = 0.2
    ramp.color_ramp.elements[1].color = (1.0, 0.15, 0.05, 1.0)
    ramp.color_ramp.elements[1].position = 0.8
    links.new(noise_tex.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], emit.inputs['Color'])
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
print("PHASE 2: BREACH — Adversarial Attack")
print("=" * 60)

# Hide Phase 1 collection
phase1 = bpy.data.collections.get("AR_PHASE1")
if phase1:
    phase1.hide_render = True
    phase1.hide_viewport = True
    print("Hidden AR_PHASE1")

col = cleanup_collection(COLLECTION_NAME)

cam = bpy.data.objects.get("zkm-kubus.fspy")
cam_loc = cam.location.copy() if cam else Vector((-7.54, 7.31, 1.23))

# --- Materials ---
mat_red_glow = make_emission_mat("AR2_Red_Glow", RED, 5.0)
mat_red_hot = make_emission_mat("AR2_Red_Hot", (1.0, 0.12, 0.05, 1.0), 8.0)
mat_glitch = make_glitch_mat("AR2_Glitch_Surface")
mat_corrupt_cyan = make_emission_mat("AR2_Corrupt_Cyan", CORRUPT_CYAN, 1.5)
mat_narrative = make_emission_mat("AR2_Narrative_Text", WHITE_FLICKER, 4.0)
mat_warning = make_emission_mat("AR2_Warning_Text", RED, 6.0)

# --- Darken world further ---
world = bpy.context.scene.world
if world and world.use_nodes:
    bg = world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value = DARK_BG
        bg.inputs['Strength'].default_value = 0.05

# --- Hostile lighting ---
print("[1/6] Setting hostile lighting...")
light = bpy.data.objects.get("Light")
if light:
    light.data.energy = 80
    light.data.color = (0.9, 0.5, 0.4)

# Red panic light
panic_data = bpy.data.lights.new("AR2_PanicLight", type='POINT')
panic_data.energy = 400
panic_data.color = (1.0, 0.1, 0.03)
if hasattr(panic_data, 'shadow_soft_size'):
    panic_data.shadow_soft_size = 3.0
panic_obj = bpy.data.objects.new("AR2_PanicLight", panic_data)
col.objects.link(panic_obj)
panic_obj.location = (0, 0, 3.5)

# Flickering secondary red
flicker_data = bpy.data.lights.new("AR2_FlickerLight", type='POINT')
flicker_data.energy = 200
flicker_data.color = (0.8, 0.05, 0.02)
flicker_obj = bpy.data.objects.new("AR2_FlickerLight", flicker_data)
col.objects.link(flicker_obj)
flicker_obj.location = (-3, -2, 2)

# =============================================================================
# DISTORTED WIREFRAME — violently deformed geometry bleeding from the cube
# =============================================================================
print("[2/6] Creating distorted wireframe geometry...")

cube = bpy.data.objects.get("Cube")
if cube:
    # Copy cube mesh and heavily distort it
    bm = bmesh.new()
    bm.from_mesh(cube.data)
    bm.transform(cube.matrix_world)

    # Subdivide for more detail
    edges = list(bm.edges)
    bmesh.ops.subdivide_edges(bm, edges=edges, cuts=3, use_grid_fill=True)

    # Violent noise displacement
    for v in bm.verts:
        p = v.co.copy()
        n = noise.noise_vector(p * 1.5 + Vector((7.7, 3.1, 0)))
        strength = 0.4 + random.uniform(0, 0.6)
        # Stronger displacement upward and outward
        disp = Vector(n) * strength
        disp.z *= 2.5  # stretch upward
        # Random spikes
        if random.random() < 0.08:
            spike_dir = (p - Vector((0,0,0))).normalized()
            disp += spike_dir * random.uniform(0.5, 1.5)
        v.co += disp

    dist_mesh = bpy.data.meshes.new("AR2_DistortedWire_Mesh")
    bm.to_mesh(dist_mesh)
    bm.free()

    dist_obj = bpy.data.objects.new("AR2_DistortedWireframe", dist_mesh)
    col.objects.link(dist_obj)
    dist_obj.data.materials.append(mat_glitch)
    mod = dist_obj.modifiers.new("GlitchWire", 'WIREFRAME')
    mod.thickness = 0.02
    mod.use_replace = False  # show both solid + wire

    # Second ghost copy offset
    bm2 = bmesh.new()
    bm2.from_mesh(cube.data)
    bm2.transform(cube.matrix_world)
    edges2 = list(bm2.edges)
    bmesh.ops.subdivide_edges(bm2, edges=edges2, cuts=2, use_grid_fill=True)
    for v in bm2.verts:
        n = noise.noise_vector(v.co * 2.0 + Vector((13.3, 0, 5.5)))
        v.co += Vector(n) * 0.3
    ghost_mesh = bpy.data.meshes.new("AR2_GhostWire_Mesh")
    bm2.to_mesh(ghost_mesh)
    bm2.free()
    ghost_obj = bpy.data.objects.new("AR2_GhostWireframe", ghost_mesh)
    ghost_obj.location = Vector((0.15, -0.1, 0.2))  # slight offset = ghosting
    col.objects.link(ghost_obj)
    ghost_obj.data.materials.append(mat_red_glow)
    gmod = ghost_obj.modifiers.new("GhostWire", 'WIREFRAME')
    gmod.thickness = 0.015
    gmod.use_replace = True

# =============================================================================
# SHATTERED BOUNDING BOXES — broken, multiplied, dashed
# =============================================================================
print("[3/6] Creating shattered bounding boxes...")

margin = 0.15
bb_min = Vector((-1.0 - margin, -1.0 - margin, -1.0 - margin))
bb_max = Vector((1.0 + margin, 1.0 + margin, 1.0 + margin))

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
    (0,1),(1,2),(2,3),(3,0),
    (4,5),(5,6),(6,7),(7,4),
    (0,4),(1,5),(2,6),(3,7),
]

# Multiple ghost bounding boxes at different offsets
for gi in range(5):
    offset = Vector((
        random.uniform(-0.3, 0.3),
        random.uniform(-0.3, 0.3),
        random.uniform(-0.2, 0.4)
    ))
    scale_f = 1.0 + gi * 0.08 + random.uniform(-0.05, 0.05)

    bm_bb = bmesh.new()
    for ei, (e0, e1) in enumerate(edges_idx):
        # Randomly skip some edges (broken/dashed effect)
        if random.random() < 0.25:
            continue
        c0 = corners[e0] * scale_f + offset
        c1 = corners[e1] * scale_f + offset
        # Add noise to endpoints
        c0 += Vector((random.uniform(-0.05, 0.05), random.uniform(-0.05, 0.05), random.uniform(-0.05, 0.05)))
        c1 += Vector((random.uniform(-0.05, 0.05), random.uniform(-0.05, 0.05), random.uniform(-0.05, 0.05)))
        v0 = bm_bb.verts.new(c0)
        v1 = bm_bb.verts.new(c1)
        bm_bb.verts.ensure_lookup_table()
        bm_bb.edges.new((v0, v1))

    bb_mesh = bpy.data.meshes.new("AR2_BrokenBB_" + str(gi))
    bm_bb.to_mesh(bb_mesh)
    bm_bb.free()

    bb_obj = bpy.data.objects.new("AR2_BrokenBBox_" + str(gi), bb_mesh)
    col.objects.link(bb_obj)
    mat_choice = mat_red_glow if gi < 3 else mat_corrupt_cyan
    bb_obj.data.materials.append(mat_choice)
    bmod = bb_obj.modifiers.new("BBWire", 'WIREFRAME')
    bmod.thickness = 0.02 - gi * 0.003
    bmod.use_replace = True

# =============================================================================
# PROCEDURAL NOISE TENDRILS — bleeding from the chair
# =============================================================================
print("[4/6] Creating noise tendrils...")

tendril_curve = bpy.data.curves.new("AR2_Tendrils", type='CURVE')
tendril_curve.dimensions = '3D'
tendril_curve.bevel_depth = 0.015
tendril_curve.resolution_u = 6

for ti in range(12):
    spline = tendril_curve.splines.new('NURBS')
    num_pts = 40
    spline.points.add(num_pts - 1)

    # Start from cube surface
    start_angle = random.uniform(0, 2 * math.pi)
    start_z = random.uniform(-0.8, 0.8)
    start = Vector((
        math.cos(start_angle) * 1.0,
        math.sin(start_angle) * 1.0,
        start_z
    ))

    pos = start.copy()
    for i in range(num_pts):
        t = i / num_pts
        n = noise.noise_vector(pos * 0.8 + Vector((ti * 3.3, 0, t * 2)))
        vel = Vector(n) * (0.15 + t * 0.3)
        vel.z += 0.08  # tendency upward
        # Outward from center
        outward = pos.copy()
        outward.z = 0
        if outward.length > 0.01:
            vel += outward.normalized() * t * 0.1
        pos += vel
        spline.points[i].co = (pos.x, pos.y, pos.z, 1.0)

    spline.use_endpoint_u = True
    spline.order_u = 4

tendril_obj = bpy.data.objects.new("AR2_Tendrils", tendril_curve)
col.objects.link(tendril_obj)
tendril_obj.data.materials.append(mat_glitch)

# =============================================================================
# NARRATIVE TEXT — the machine writes poetry
# =============================================================================
print("[5/6] Creating narrative text overlays...")

# Main narrative - massive, terrifying
main_text_data = bpy.data.curves.new("AR2_Narrative_Main", type='FONT')
main_text_data.body = "IT STILL REMEMBERS\nTHE WEIGHT OF THE\nLAST PERSON."
main_text_data.size = 0.22
main_text_data.extrude = 0.012
main_text_data.bevel_depth = 0.004
main_text_data.space_line = 1.2
main_text_data.resolution_u = 2
main_obj = bpy.data.objects.new("AR2_Narrative_Main", main_text_data)
col.objects.link(main_obj)
main_obj.location = (-0.5, -0.5, 2.0)
face_camera_text(main_obj, cam_loc)
main_obj.data.materials.append(mat_narrative)

# Warning box
warn_data = bpy.data.curves.new("AR2_Warning", type='FONT')
warn_data.body = "[WARNING] BIOMETRIC ANOMALY. CONFIDENCE: 1.2%"
warn_data.size = 0.10
warn_data.extrude = 0.006
warn_data.resolution_u = 2
warn_obj = bpy.data.objects.new("AR2_Warning", warn_data)
col.objects.link(warn_obj)
warn_obj.location = (-0.8, 0.5, -0.5)
face_camera_text(warn_obj, cam_loc)
warn_obj.data.materials.append(mat_warning)

# Secondary glitch text fragments
fragments = [
    ("DO NOT LOOK AWAY.", (-2.5, 1.0, 3.0), 0.14),
    ("i have always been here...", (1.5, -1.5, 2.8), 0.10),
    ("who is writing these sentences?", (-1.0, 2.0, 0.5), 0.08),
    ("OBJECT: [REDACTED]", (2.0, -0.5, 1.5), 0.09),
    ("CONFIDENCE: NaN%", (1.0, 1.0, 3.2), 0.07),
    ("it opened once.\nno one came through.", (-2.0, -1.0, 1.8), 0.08),
]

for fi, (text, pos, size) in enumerate(fragments):
    fd = bpy.data.curves.new("AR2_Fragment_" + str(fi), type='FONT')
    fd.body = text
    fd.size = size
    fd.extrude = 0.004
    fd.resolution_u = 1
    fobj = bpy.data.objects.new("AR2_Fragment_" + str(fi), fd)
    col.objects.link(fobj)
    fobj.location = pos
    # Random slight tilt for unsettling feel
    face_camera_text(fobj, cam_loc)
    rx, ry, rz = fobj.rotation_euler
    fobj.rotation_euler = (rx + random.uniform(-0.1, 0.1), random.uniform(-0.08, 0.08), rz + random.uniform(-0.05, 0.05))
    mat_choice = mat_warning if random.random() < 0.4 else mat_narrative
    fobj.data.materials.append(mat_choice)

# =============================================================================
# CORRUPTED SCAN LINES — broken, red-shifted
# =============================================================================
print("[6/6] Creating corrupted scan lines...")

scan_curve = bpy.data.curves.new("AR2_CorruptScan", type='CURVE')
scan_curve.dimensions = '3D'
scan_curve.bevel_depth = 0.006
scan_curve.resolution_u = 8

for ring in range(10):
    spline = scan_curve.splines.new('POLY')
    radius = 1.0 + ring * 0.3
    num_pts = 48
    spline.points.add(num_pts)
    for i in range(num_pts + 1):
        angle = (i / num_pts) * 2 * math.pi
        x = math.cos(angle) * radius
        y = math.sin(angle) * radius
        # Heavy noise distortion
        n = noise.noise_vector(Vector((x*0.3, y*0.3, ring*0.5)))
        z = 0.01 + n.z * 0.15 * (ring / 10.0)
        x += n.x * 0.2 * (ring / 10.0)
        y += n.y * 0.2 * (ring / 10.0)
        # Random breaks
        w = 0.0 if random.random() < 0.05 else 1.0
        spline.points[i].co = (x, y, z, w)

scan_obj = bpy.data.objects.new("AR2_CorruptScan", scan_curve)
col.objects.link(scan_obj)
scan_obj.data.materials.append(mat_red_glow)

# =============================================================================
# RENDER SETTINGS
# =============================================================================
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 96
scene.cycles.use_denoising = True
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

cam_obj = bpy.data.objects.get("zkm-kubus.fspy")
if cam_obj:
    scene.camera = cam_obj

# =============================================================================
# COMPOSITOR — Chromatic Aberration
# =============================================================================
scene.use_nodes = True
tree = scene.node_tree
for node in tree.nodes:
    tree.nodes.remove(node)

rl = tree.nodes.new('CompositorNodeRLayers')
rl.location = (-400, 0)

# Lens distortion for chromatic aberration
lens = tree.nodes.new('CompositorNodeLensdist')
lens.location = (0, 0)
lens.inputs['Distort'].default_value = 0.0
lens.inputs['Dispersion'].default_value = 0.06  # chromatic aberration

# Glare for bloom on emissions
glare = tree.nodes.new('CompositorNodeGlare')
glare.location = (200, 0)
glare.glare_type = 'FOG_GLOW'
glare.quality = 'HIGH'
glare.threshold = 0.8
glare.size = 6

comp = tree.nodes.new('CompositorNodeComposite')
comp.location = (500, 0)

tree.links.new(rl.outputs['Image'], lens.inputs['Image'])
tree.links.new(lens.outputs['Image'], glare.inputs['Image'])
tree.links.new(glare.outputs['Image'], comp.inputs['Image'])

print("=" * 60)
print("PHASE 2: BREACH — Setup Complete!")
print("Total objects: " + str(len(col.objects)))
print("Compositor: Chromatic Aberration + Bloom active")
print("=" * 60)
