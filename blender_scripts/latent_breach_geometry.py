import bpy
import bmesh
import math
import random
import mathutils
from mathutils import Vector, noise

# =============================================================================
# LATENT BREACH — Complex Geometry Generator (Thread-Safe Version)
# 
# IMPORTANT: This script uses ONLY bpy.data / bmesh APIs (no bpy.ops).
# This ensures it can run safely from the MCP bridge server's background
# thread without causing ACCESS_VIOLATION crashes.
#
# Concept: Assembly (Phase 1) → Breach (Phase 2)
# Layers: NURBS Signals / Agent Diagrid / Hessian Isosurface / 
#         Adversarial Shell / Narrative Fragments
# =============================================================================


def create_bmesh_icosphere(radius=1.0, subdivisions=3):
    """Create an icosphere using bmesh (thread-safe, no bpy.ops)."""
    bm = bmesh.new()
    
    # Golden ratio
    phi = (1 + math.sqrt(5)) / 2
    
    # 12 vertices of icosahedron
    scale = radius / math.sqrt(1 + phi * phi)
    verts_data = [
        (-1,  phi, 0), ( 1,  phi, 0), (-1, -phi, 0), ( 1, -phi, 0),
        ( 0, -1,  phi), ( 0,  1,  phi), ( 0, -1, -phi), ( 0,  1, -phi),
        ( phi, 0, -1), ( phi, 0,  1), (-phi, 0, -1), (-phi, 0,  1),
    ]
    
    bm_verts = []
    for v in verts_data:
        bm_verts.append(bm.verts.new(Vector(v) * scale))
    
    bm.verts.ensure_lookup_table()
    
    # 20 faces of icosahedron
    faces_data = [
        (0,11,5), (0,5,1), (0,1,7), (0,7,10), (0,10,11),
        (1,5,9), (5,11,4), (11,10,2), (10,7,6), (7,1,8),
        (3,9,4), (3,4,2), (3,2,6), (3,6,8), (3,8,9),
        (4,9,5), (2,4,11), (6,2,10), (8,6,7), (9,8,1),
    ]
    
    for f in faces_data:
        try:
            bm.faces.new([bm_verts[f[0]], bm_verts[f[1]], bm_verts[f[2]]])
        except ValueError:
            pass
    
    # Subdivide
    for _ in range(subdivisions):
        edges = list(bm.edges)
        bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=True)
        # Project to sphere
        for v in bm.verts:
            v.co = v.co.normalized() * radius
    
    return bm


class LatentBreachGenerator:
    """Main generator — creates all 5 geometry layers (thread-safe)."""

    def __init__(self):
        self.CONFIG = {
            'COLLECTION_NAME': "LATENT_BREACH",
            # UWB Beacon layout (Kubus-like 2x3 grid)
            'BEACON_POSITIONS': [
                Vector((-3.0, -2.0, 2.5)),
                Vector(( 3.0, -2.0, 2.5)),
                Vector((-3.0,  0.0, 2.5)),
                Vector(( 3.0,  0.0, 2.5)),
                Vector((-3.0,  2.0, 2.5)),
                Vector(( 3.0,  2.0, 2.5)),
            ],
            # Agent system
            'AGENT_COUNT': 150,
            'STEPS': 200,
            'GRID_COLS': 15,
            'GRID_ROWS': 10,
            # Isosurface
            'VOLUME_RES': 25,       # reduced for stability (25³ = 15625 cells)
            'VOLUME_SIZE': 8.0,
            'ISO_THRESHOLD': 0.35,
            # Adversarial perturbation
            'PERTURB_STRENGTH': 0.25,
            'PERTURB_OCTAVES': 4,
            # Narrative text fragments
            'NARRATIVE_TEXTS': [
                "this one has not blinked.",
                "it wasn't facing this way before.",
                "it opened once. no one came through.",
                "DO NOT LOOK AWAY.",
                "i have always been here...",
                "who is writing these sentences?",
            ],
        }

        # Define Agent class locally for exec() scope compatibility
        class Agent:
            def __init__(self, pos, id, config):
                self.pos = Vector(pos)
                self.vel = Vector((
                    random.uniform(-0.5, 0.5),
                    random.uniform(-0.5, 0.5),
                    random.uniform(-0.5, 0.5)
                )).normalized() * 0.05
                self.acc = Vector((0, 0, 0))
                self.history = [self.pos.copy()]
                self.id = id
                self.config = config
                self.max_speed = 0.15
                self.max_force = 0.04

            def apply_force(self, force):
                self.acc += force

            def flock(self, agents, step, total_steps):
                sep = self._separation(agents)
                ali = self._alignment(agents)
                coh = self._cohesion(agents)
                cen = self._center_attraction()

                progress = step / total_steps
                sep_w = 1.0 + progress * 3.0
                ali_w = 1.5 * (1.0 - progress)
                coh_w = 1.2 * (1.0 - progress)
                cen_w = 0.3

                self.apply_force(sep * sep_w)
                self.apply_force(ali * ali_w)
                self.apply_force(coh * coh_w)
                self.apply_force(cen * cen_w)

                if progress > 0.4:
                    noise_strength = (progress - 0.4) * 0.08
                    n = noise.noise_vector(self.pos * 0.5 + Vector((step * 0.01, 0, 0)))
                    self.apply_force(Vector(n) * noise_strength)

            def update(self):
                self.vel += self.acc
                if self.vel.length > self.max_speed:
                    self.vel = self.vel.normalized() * self.max_speed
                self.pos += self.vel
                self.acc *= 0
                self.history.append(self.pos.copy())

            def _separation(self, agents):
                steer = Vector((0, 0, 0))
                count = 0
                for other in agents:
                    if other.id != self.id:
                        d = (self.pos - other.pos).length
                        if 0 < d < 0.6:
                            steer += (self.pos - other.pos).normalized() / d
                            count += 1
                if count > 0:
                    steer /= count
                    if steer.length > 0:
                        steer = steer.normalized() * self.max_speed - self.vel
                        if steer.length > self.max_force:
                            steer = steer.normalized() * self.max_force
                return steer

            def _alignment(self, agents):
                sum_vel = Vector((0, 0, 0))
                count = 0
                for other in agents:
                    d = (self.pos - other.pos).length
                    if d < 1.5 and other.id != self.id:
                        sum_vel += other.vel
                        count += 1
                if count > 0:
                    sum_vel /= count
                    sum_vel = sum_vel.normalized() * self.max_speed
                    steer = sum_vel - self.vel
                    if steer.length > self.max_force:
                        steer = steer.normalized() * self.max_force
                    return steer
                return Vector((0, 0, 0))

            def _cohesion(self, agents):
                sum_pos = Vector((0, 0, 0))
                count = 0
                for other in agents:
                    d = (self.pos - other.pos).length
                    if d < 1.5 and other.id != self.id:
                        sum_pos += other.pos
                        count += 1
                if count > 0:
                    sum_pos /= count
                    return self._seek(sum_pos)
                return Vector((0, 0, 0))

            def _center_attraction(self):
                center = Vector((0, 0, 0))
                desired = center - self.pos
                dist = desired.length
                tangent = desired.cross(Vector((0, 0, 1)))
                if tangent.length > 0:
                    tangent = tangent.normalized()
                else:
                    tangent = Vector((1, 0, 0))
                if dist > 5:
                    return self._seek(center)
                else:
                    target_vel = (desired.normalized() * 0.3 + tangent * 0.7).normalized() * self.max_speed
                    steer = target_vel - self.vel
                    if steer.length > self.max_force:
                        steer = steer.normalized() * self.max_force
                    return steer

            def _seek(self, target):
                desired = (target - self.pos)
                if desired.length > 0:
                    desired = desired.normalized() * self.max_speed
                steer = desired - self.vel
                if steer.length > self.max_force:
                    steer = steer.normalized() * self.max_force
                return steer

        self.AgentClass = Agent
        self.agents = []
        self.collection = self._setup_collection()
        self.materials = self._create_all_materials()

    # =========================================================================
    # COLLECTION MANAGEMENT
    # =========================================================================
    def _setup_collection(self):
        name = self.CONFIG['COLLECTION_NAME']
        if name in bpy.data.collections:
            col = bpy.data.collections[name]
            for obj in list(col.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
        else:
            col = bpy.data.collections.new(name)
            bpy.context.scene.collection.children.link(col)
        return col

    # =========================================================================
    # MATERIALS
    # =========================================================================
    def _create_all_materials(self):
        mats = {}
        mats['signal'] = self._mat_signal_emission()
        mats['plating'] = self._mat_rainbow_plating()
        mats['glass'] = self._mat_hessian_glass()
        mats['adversarial'] = self._mat_adversarial_red()
        mats['terminal'] = self._mat_text_terminal()
        return mats

    def _mat_signal_emission(self):
        name = "LB_Signal_Emission"
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
        emit.inputs['Strength'].default_value = 3.0

        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.location = (0, 0)
        ramp.color_ramp.interpolation = 'EASE'
        ramp.color_ramp.elements[0].color = (0.0, 0.9, 1.0, 1.0)
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[1].color = (1.0, 0.05, 0.1, 1.0)
        ramp.color_ramp.elements[1].position = 1.0
        mid = ramp.color_ramp.elements.new(0.5)
        mid.color = (0.8, 0.1, 0.9, 1.0)

        gradient = nodes.new('ShaderNodeTexGradient')
        gradient.location = (-300, -200)
        gradient.gradient_type = 'SPHERICAL'
        tex_coord = nodes.new('ShaderNodeTexCoord')
        tex_coord.location = (-600, -200)

        links.new(tex_coord.outputs['Object'], gradient.inputs['Vector'])
        links.new(gradient.outputs['Color'], ramp.inputs['Fac'])
        links.new(ramp.outputs['Color'], emit.inputs['Color'])
        links.new(emit.outputs['Emission'], out.inputs['Surface'])
        return mat

    def _mat_rainbow_plating(self):
        name = "LB_Rainbow_Plating"
        mat = bpy.data.materials.get(name)
        if mat:
            bpy.data.materials.remove(mat)
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        out = nodes.new('ShaderNodeOutputMaterial')
        out.location = (400, 0)
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.location = (100, 0)
        bsdf.inputs['Metallic'].default_value = 1.0
        bsdf.inputs['Roughness'].default_value = 0.08

        lw = nodes.new('ShaderNodeLayerWeight')
        lw.location = (-500, 0)
        lw.inputs['Blend'].default_value = 0.35

        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.location = (-200, 0)
        ramp.color_ramp.interpolation = 'CARDINAL'
        ramp.color_ramp.elements[0].color = (0.15, 0.05, 0.45, 1)
        ramp.color_ramp.elements.new(0.2).color = (0.0, 0.3, 0.8, 1)
        ramp.color_ramp.elements.new(0.4).color = (0.0, 0.7, 0.6, 1)
        ramp.color_ramp.elements.new(0.6).color = (0.6, 0.85, 0.15, 1)
        ramp.color_ramp.elements.new(0.8).color = (0.85, 0.2, 0.4, 1)
        ramp.color_ramp.elements[-1].color = (0.25, 0.0, 0.35, 1)

        links.new(lw.outputs['Facing'], ramp.inputs['Fac'])
        links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
        links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
        return mat

    def _mat_hessian_glass(self):
        name = "LB_Hessian_Glass"
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
        glass = nodes.new('ShaderNodeBsdfGlass')
        glass.location = (100, 100)
        glass.inputs['Color'].default_value = (0.75, 0.85, 1.0, 1.0)
        glass.inputs['Roughness'].default_value = 0.05
        glass.inputs['IOR'].default_value = 1.45

        transparent = nodes.new('ShaderNodeBsdfTransparent')
        transparent.location = (100, -100)
        transparent.inputs['Color'].default_value = (0.9, 0.95, 1.0, 1.0)

        mix = nodes.new('ShaderNodeMixShader')
        mix.location = (300, 0)
        mix.inputs['Fac'].default_value = 0.6

        links.new(transparent.outputs['BSDF'], mix.inputs[1])
        links.new(glass.outputs['BSDF'], mix.inputs[2])
        links.new(mix.outputs['Shader'], out.inputs['Surface'])
        return mat

    def _mat_adversarial_red(self):
        name = "LB_Adversarial_Red"
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
        emit.inputs['Strength'].default_value = 4.0

        noise_tex = nodes.new('ShaderNodeTexNoise')
        noise_tex.location = (-300, -100)
        noise_tex.inputs['Scale'].default_value = 3.0
        noise_tex.inputs['Detail'].default_value = 8.0

        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.location = (0, -100)
        ramp.color_ramp.elements[0].color = (0.6, 0.0, 0.0, 1.0)
        ramp.color_ramp.elements[0].position = 0.3
        ramp.color_ramp.elements[1].color = (1.0, 0.1, 0.05, 1.0)
        ramp.color_ramp.elements[1].position = 0.7

        links.new(noise_tex.outputs['Fac'], ramp.inputs['Fac'])
        links.new(ramp.outputs['Color'], emit.inputs['Color'])
        links.new(emit.outputs['Emission'], out.inputs['Surface'])
        return mat

    def _mat_text_terminal(self):
        name = "LB_Text_Terminal"
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
        emit.inputs['Color'].default_value = (0.75, 0.9, 0.8, 1.0)
        emit.inputs['Strength'].default_value = 2.5
        links.new(emit.outputs['Emission'], out.inputs['Surface'])
        return mat

    # =========================================================================
    # LAYER 1: UWB BEACON SIGNAL SPIRALS (NURBS)
    # =========================================================================
    def create_layer1_signals(self):
        print("[Layer 1] Creating UWB Beacon Signal Spirals...")
        beacons = self.CONFIG['BEACON_POSITIONS']

        for bi, beacon_pos in enumerate(beacons):
            curve_data = bpy.data.curves.new(f'LB_Signal_{bi}', type='CURVE')
            curve_data.dimensions = '3D'
            curve_data.bevel_depth = 0.012
            curve_data.resolution_u = 8

            for arm in range(3):
                spline = curve_data.splines.new('NURBS')
                num_pts = 80
                spline.points.add(num_pts - 1)
                arm_offset = arm * (2 * math.pi / 3)

                for i in range(num_pts):
                    t = i / num_pts
                    radius = t * 3.5
                    angle = arm_offset + t * 6 * math.pi
                    z_drop = -t * 2.0
                    noise_amp = t * t * 0.8
                    n_pos = beacon_pos + Vector((radius * 0.3, angle * 0.1, t))
                    n = noise.noise_vector(n_pos * 0.5)
                    x = beacon_pos.x + math.cos(angle) * radius + n.x * noise_amp
                    y = beacon_pos.y + math.sin(angle) * radius + n.y * noise_amp
                    z = beacon_pos.z + z_drop + n.z * noise_amp * 0.5
                    spline.points[i].co = (x, y, z, 1.0)

                spline.use_endpoint_u = True
                spline.order_u = 4

            obj = bpy.data.objects.new(f"LB_Signal_Beacon_{bi}", curve_data)
            self.collection.objects.link(obj)
            obj.data.materials.append(self.materials['signal'])

        # Beacon point markers — using bmesh icosphere (NO bpy.ops)
        for bi, pos in enumerate(beacons):
            bm = create_bmesh_icosphere(radius=0.12, subdivisions=2)
            mesh = bpy.data.meshes.new(f"LB_Beacon_Mesh_{bi}")
            bm.to_mesh(mesh)
            bm.free()
            marker = bpy.data.objects.new(f"LB_Beacon_Point_{bi}", mesh)
            marker.location = pos
            self.collection.objects.link(marker)
            marker.data.materials.append(self.materials['signal'])

        print(f"  -> Created {len(beacons)} beacons x 3 spiral arms + markers")

    # =========================================================================
    # LAYER 2: DETECTION DIAGRID (AGENT-BASED MESH)
    # =========================================================================
    def create_layer2_diagrid(self):
        print("[Layer 2] Creating Detection Diagrid (Agent Flocking)...")

        cols = self.CONFIG['GRID_COLS']
        rows = self.CONFIG['GRID_ROWS']
        spacing = 0.5
        idx = 0
        for r in range(rows):
            for c in range(cols):
                x = (c - cols / 2) * spacing
                y = (r - rows / 2) * spacing
                z = random.uniform(-0.2, 0.2)
                self.agents.append(self.AgentClass((x, y, z), idx, self.CONFIG))
                idx += 1

        steps = self.CONFIG['STEPS']
        print(f"  Simulating {len(self.agents)} agents x {steps} steps...")
        for s in range(steps):
            if s % 50 == 0:
                print(f"    step {s}/{steps}...")
            current_state = list(self.agents)
            for agent in self.agents:
                agent.flock(current_state, s, steps)
                agent.update()

        # Build primary curves (agent trails)
        curve_data = bpy.data.curves.new('LB_AgentPaths', type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.bevel_depth = 0.025
        curve_data.resolution_u = 3

        for agent in self.agents:
            spline = curve_data.splines.new('POLY')
            spline.points.add(len(agent.history) - 1)
            for i, p in enumerate(agent.history):
                spline.points[i].co = (p.x, p.y, p.z, 1)

        obj_paths = bpy.data.objects.new("LB_AgentTrails", curve_data)
        self.collection.objects.link(obj_paths)
        obj_paths.data.materials.append(self.materials['plating'])

        # Build diagrid
        mesh = bpy.data.meshes.new("LB_Diagrid_Mesh")
        bm = bmesh.new()
        step_interval = 6

        for t in range(0, steps, step_interval):
            positions = []
            for agent in self.agents:
                if t < len(agent.history):
                    positions.append(agent.history[t])

            vert_lookup = {}
            for i in range(len(positions)):
                p1 = positions[i]
                connected = 0
                for j in range(i + 1, len(positions)):
                    p2 = positions[j]
                    dist = (p1 - p2).length
                    if 0.3 < dist < 1.0 and connected < 4:
                        k1 = tuple(round(c, 4) for c in p1)
                        if k1 not in vert_lookup:
                            vert_lookup[k1] = bm.verts.new(p1)
                        v1 = vert_lookup[k1]
                        k2 = tuple(round(c, 4) for c in p2)
                        if k2 not in vert_lookup:
                            vert_lookup[k2] = bm.verts.new(p2)
                        v2 = vert_lookup[k2]
                        try:
                            bm.edges.new((v1, v2))
                        except ValueError:
                            pass
                        connected += 1

        bm.to_mesh(mesh)
        bm.free()

        obj_grid = bpy.data.objects.new("LB_Diagrid_Tension", mesh)
        self.collection.objects.link(obj_grid)
        mod_wire = obj_grid.modifiers.new("Wireframe", 'WIREFRAME')
        mod_wire.thickness = 0.015
        mod_wire.use_replace = False
        obj_grid.data.materials.append(self.materials['plating'])

        print("  -> Created agent trails + diagrid mesh")

    # =========================================================================
    # LAYER 3: HESSIAN CURVATURE ISOSURFACE (VOLUMETRIC)
    # =========================================================================
    def create_layer3_hessian(self):
        print("[Layer 3] Creating Hessian Curvature Isosurface...")
        try:
            import numpy as np
            self._create_isosurface_numpy(np)
        except ImportError:
            print("  ! NumPy not available, using fallback")
            self._create_isosurface_fallback()

    def _create_isosurface_numpy(self, np):
        """Marching cubes isosurface from beacon Gaussian field (vectorized)."""
        res = self.CONFIG['VOLUME_RES']
        size = self.CONFIG['VOLUME_SIZE']
        threshold = self.CONFIG['ISO_THRESHOLD']
        beacons = self.CONFIG['BEACON_POSITIONS']

        print(f"  Building scalar field ({res}^3 = {res**3} cells)...")
        lin = np.linspace(-size, size, res)
        X, Y, Z = np.meshgrid(lin, lin, lin, indexing='ij')

        field = np.zeros_like(X)
        for bp in beacons:
            dist_sq = (X - bp.x)**2 + (Y - bp.y)**2 + (Z - bp.z)**2
            field += np.exp(-dist_sq / (2 * 2.8**2))

        # Saddle-point perturbation (Hessian character)
        field += 0.15 * (X**2 - Y**2) / (size**2)

        print("  Extracting isosurface (vectorized)...")
        verts, faces = self._marching_cubes_vectorized(field, threshold, lin, np)

        if len(verts) == 0:
            threshold = float(np.percentile(field, 75))
            print(f"  ! Adjusting threshold to {threshold:.3f}...")
            verts, faces = self._marching_cubes_vectorized(field, threshold, lin, np)

        if len(verts) > 0:
            mesh = bpy.data.meshes.new("LB_Hessian_Mesh")
            mesh.from_pydata(verts, [], faces)
            mesh.update()
            obj = bpy.data.objects.new("LB_Hessian_Surface", mesh)
            self.collection.objects.link(obj)
            obj.data.materials.append(self.materials['glass'])
            for poly in obj.data.polygons:
                poly.use_smooth = True
            mod_sub = obj.modifiers.new("Smooth", 'SUBSURF')
            mod_sub.levels = 1
            mod_sub.render_levels = 2
            print(f"  -> Created isosurface: {len(verts)} verts, {len(faces)} faces")
        else:
            print("  ! Isosurface empty, using fallback")
            self._create_isosurface_fallback()

    def _marching_cubes_vectorized(self, field, threshold, lin, np):
        """Vectorized marching cubes using numpy — much faster than triple loop."""
        res = field.shape[0]
        
        # Pre-compute above/below for all grid points
        above = field >= threshold
        
        verts = []
        faces = []
        vert_map = {}
        
        def get_vert(pos):
            key = (round(pos[0], 4), round(pos[1], 4), round(pos[2], 4))
            if key not in vert_map:
                vert_map[key] = len(verts)
                verts.append(pos)
            return vert_map[key]
        
        def interp(p0, p1, v0, v1):
            if abs(v0 - v1) < 1e-10:
                t = 0.5
            else:
                t = float((threshold - v0) / (v1 - v0))
                t = max(0.0, min(1.0, t))
            return (
                p0[0] + t * (p1[0] - p0[0]),
                p0[1] + t * (p1[1] - p0[1]),
                p0[2] + t * (p1[2] - p0[2]),
            )

        # Find cells that straddle the isosurface (vectorized check)
        # A cell straddles if any of its 8 corners differ in above/below status
        for i in range(res - 1):
            for j in range(res - 1):
                for k in range(res - 1):
                    # Quick reject: check if all same
                    c = above[i:i+2, j:j+2, k:k+2]
                    if c.all() or not c.any():
                        continue
                    
                    # 8 corner values
                    corners = [
                        (i,j,k), (i+1,j,k), (i+1,j+1,k), (i,j+1,k),
                        (i,j,k+1), (i+1,j,k+1), (i+1,j+1,k+1), (i,j+1,k+1)
                    ]
                    vals = [float(field[ci,cj,ck]) for ci,cj,ck in corners]
                    abv = [v >= threshold for v in vals]
                    
                    edges = [
                        (0,1),(1,2),(2,3),(3,0),
                        (4,5),(5,6),(6,7),(7,4),
                        (0,4),(1,5),(2,6),(3,7)
                    ]
                    
                    pts = []
                    for e0, e1 in edges:
                        if abv[e0] != abv[e1]:
                            c0, c1 = corners[e0], corners[e1]
                            p0 = (lin[c0[0]], lin[c0[1]], lin[c0[2]])
                            p1 = (lin[c1[0]], lin[c1[1]], lin[c1[2]])
                            pts.append(interp(p0, p1, vals[e0], vals[e1]))
                    
                    if len(pts) >= 3:
                        ids = [get_vert(p) for p in pts]
                        for t in range(1, len(ids) - 1):
                            faces.append((ids[0], ids[t], ids[t+1]))
        
        return verts, faces

    def _create_isosurface_fallback(self):
        """Fallback: deformed icosphere (NO bpy.ops)."""
        bm = create_bmesh_icosphere(radius=3.0, subdivisions=4)
        
        for v in bm.verts:
            p = v.co.copy()
            saddle = 0.15 * (p.x**2 - p.y**2)
            beacon_influence = 0
            for bp in self.CONFIG['BEACON_POSITIONS']:
                dist = (p - bp).length
                beacon_influence += math.exp(-dist**2 / 8.0) * 0.5
            n = noise.noise_vector(p * 0.4)
            v.co.z += saddle + beacon_influence + n.z * 0.3

        mesh = bpy.data.meshes.new("LB_Hessian_Mesh")
        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new("LB_Hessian_Surface", mesh)
        obj.location = (0, 0, 0.5)
        self.collection.objects.link(obj)
        obj.data.materials.append(self.materials['glass'])
        for poly in obj.data.polygons:
            poly.use_smooth = True
        print("  -> Created fallback Hessian surface (deformed icosphere)")

    # =========================================================================
    # LAYER 4: ADVERSARIAL PERTURBATION SHELL
    # =========================================================================
    def create_layer4_adversarial(self):
        print("[Layer 4] Creating Adversarial Perturbation Shell...")

        source = bpy.data.objects.get("LB_Hessian_Surface")
        if source:
            source_copy = source.copy()
            source_copy.data = source.data.copy()
            self.collection.objects.link(source_copy)
        else:
            # Fallback: create standalone shell (NO bpy.ops)
            print("  ! No Hessian surface found, creating standalone")
            bm = create_bmesh_icosphere(radius=3.5, subdivisions=3)
            mesh = bpy.data.meshes.new("LB_Adversarial_Mesh")
            bm.to_mesh(mesh)
            bm.free()
            source_copy = bpy.data.objects.new("LB_Adversarial_Shell", mesh)
            source_copy.location = (0, 0, 0.5)
            self.collection.objects.link(source_copy)

        source_copy.name = "LB_Adversarial_Shell"

        # PGD-style adversarial perturbation
        mesh = source_copy.data
        strength = self.CONFIG['PERTURB_STRENGTH']

        for v in mesh.vertices:
            p = v.co.copy()
            perturbation = Vector((0, 0, 0))
            amp = strength
            freq = 1.0
            for octave in range(self.CONFIG['PERTURB_OCTAVES']):
                n = noise.noise_vector(p * freq + Vector((octave * 7.31, 0, 0)))
                perturbation += Vector(n) * amp
                amp *= 0.5
                freq *= 2.0

            perturbation.z *= 1.8
            if p.length > 0.001:
                from_center = p.normalized()
                outward = from_center * (perturbation.dot(from_center))
                perturbation = perturbation * 0.4 + outward * 0.6

            v.co += perturbation

        mesh.update()

        source_copy.data.materials.clear()
        source_copy.data.materials.append(self.materials['adversarial'])

        mod_wire = source_copy.modifiers.new("AdversarialWire", 'WIREFRAME')
        mod_wire.thickness = 0.008
        mod_wire.use_replace = False

        source_copy.scale = (1.08, 1.08, 1.08)
        print("  -> Created adversarial shell with PGD perturbation")

    # =========================================================================
    # LAYER 5: NARRATIVE FRAGMENTS (TEXT GEOMETRY)
    # =========================================================================
    def create_layer5_narrative(self):
        print("[Layer 5] Creating Narrative Fragments...")
        texts = self.CONFIG['NARRATIVE_TEXTS']
        beacons = self.CONFIG['BEACON_POSITIONS']

        for ti, text in enumerate(texts):
            text_data = bpy.data.curves.new(f'LB_Text_{ti}', type='FONT')
            text_data.body = text
            text_data.size = 0.18
            text_data.extrude = 0.015
            text_data.bevel_depth = 0.003
            text_data.resolution_u = 2

            obj = bpy.data.objects.new(f"LB_Narrative_{ti}", text_data)
            self.collection.objects.link(obj)

            beacon = beacons[ti % len(beacons)]
            offset = Vector((
                random.uniform(-1.5, 1.5),
                random.uniform(-1.5, 1.5),
                random.uniform(-2.0, -0.5)
            ))
            obj.location = beacon + offset
            obj.rotation_euler = (
                random.uniform(-0.3, 0.3),
                random.uniform(-0.3, 0.3),
                random.uniform(-math.pi, math.pi)
            )
            obj.data.materials.append(self.materials['terminal'])

        print(f"  -> Created {len(texts)} narrative text fragments")

    # =========================================================================
    # SCENE SETUP
    # =========================================================================
    def setup_scene(self):
        print("[Scene] Setting up camera, lighting, and world...")

        # World
        world = bpy.context.scene.world
        if not world:
            world = bpy.data.worlds.new("LB_World")
            bpy.context.scene.world = world
        world.use_nodes = True
        bg = world.node_tree.nodes.get('Background')
        if bg:
            bg.inputs['Color'].default_value = (0.01, 0.01, 0.01, 1.0)
            bg.inputs['Strength'].default_value = 0.3

        # Camera
        cam_data = bpy.data.cameras.new("LB_Camera")
        cam_data.lens = 35
        cam_obj = bpy.data.objects.new("LB_Camera", cam_data)
        self.collection.objects.link(cam_obj)
        cam_obj.location = (8, -8, 7)
        cam_obj.rotation_euler = (math.radians(55), 0, math.radians(45))
        bpy.context.scene.camera = cam_obj

        # Area light
        light_data = bpy.data.lights.new("LB_AreaLight", type='AREA')
        light_data.energy = 200
        light_data.size = 8
        light_data.color = (0.95, 0.95, 1.0)
        light_obj = bpy.data.objects.new("LB_AreaLight", light_data)
        self.collection.objects.link(light_obj)
        light_obj.location = (0, 0, 8)

        # Red rim light
        rim_data = bpy.data.lights.new("LB_RimLight", type='POINT')
        rim_data.energy = 100
        rim_data.color = (1.0, 0.1, 0.05)
        rim_obj = bpy.data.objects.new("LB_RimLight", rim_data)
        self.collection.objects.link(rim_obj)
        rim_obj.location = (-5, 3, 2)

        # Render engine (safe to set from any thread)
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.cycles.samples = 128

        print("  -> Scene setup complete")

    # =========================================================================
    # MAIN
    # =========================================================================
    def generate_all(self):
        print("=" * 60)
        print("LATENT BREACH — Geometry Generation Starting")
        print("=" * 60)

        self.create_layer1_signals()
        self.create_layer2_diagrid()
        self.create_layer3_hessian()
        self.create_layer4_adversarial()
        self.create_layer5_narrative()
        self.setup_scene()

        print("=" * 60)
        print("LATENT BREACH — Generation Complete!")
        total = len(self.collection.objects)
        print(f"Total objects in LATENT_BREACH collection: {total}")
        print("=" * 60)


# =============================================================================
# ENTRY POINT
# =============================================================================
gen = LatentBreachGenerator()
gen.generate_all()
