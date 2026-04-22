import bpy
import bmesh
import math
import random
import mathutils
from mathutils import Vector, noise

# =============================================================================
# MAIN SIMULATION
# =============================================================================
class BioStructure:
    def __init__(self):
        # CONFIGURATION
        self.CONFIG = {
            'COLLECTION_NAME': "MCP_Collection",
            'AGENT_COUNT': 150,
            'STEPS': 250,
            'STEP_SIZE': 0.15,
            'INFLUENCE_RADIUS': 1.5,
            'SEPARATION_RADIUS': 0.6,
            'THIN_FILM_MAT_NAME': "Rainbow_Plating"
        }
        
        # Define Agent Class Locally to capture scope
        class Agent:
            def __init__(self, pos, id, config):
                import random
                import mathutils
                Vector = mathutils.Vector
                self.pos = Vector(pos)
                self.vel = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))).normalized()
                self.acc = Vector((0, 0, 0))
                self.history = [self.pos.copy()]
                self.id = id
                self.config = config
                self.max_speed = 0.2
                self.max_force = 0.05

            def apply_force(self, force):
                self.acc += force

            def flock(self, agents):
                sep = self.separation(agents)
                ali = self.alignment(agents)
                coh = self.cohesion(agents)
                cen = self.center_attraction()
                
                # Weights
                self.apply_force(sep * 2.5)
                self.apply_force(ali * 1.0)
                self.apply_force(coh * 0.8)
                self.apply_force(cen * 0.3)

            def update(self):
                self.vel += self.acc
                if self.vel.length > self.max_speed:
                    self.vel = self.vel.normalized() * self.max_speed
                
                self.pos += self.vel
                self.acc *= 0 
                self.history.append(self.pos.copy())

            def separation(self, agents):
                import mathutils
                Vector = mathutils.Vector
                steer = Vector((0, 0, 0))
                count = 0
                r = self.config['SEPARATION_RADIUS']
                for other in agents:
                    if other.id != self.id:
                        d = (self.pos - other.pos).length
                        if d < r and d > 0:
                            diff = (self.pos - other.pos).normalized()
                            diff /= d 
                            steer += diff
                            count += 1
                if count > 0:
                    steer /= count
                    if steer.length > 0:
                        steer = steer.normalized() * self.max_speed - self.vel
                        if steer.length > self.max_force:
                            steer = steer.normalized() * self.max_force
                return steer

            def alignment(self, agents):
                import mathutils
                Vector = mathutils.Vector
                sum_vel = Vector((0, 0, 0))
                count = 0
                r = self.config['INFLUENCE_RADIUS']
                for other in agents:
                    d = (self.pos - other.pos).length
                    if d < r and other.id != self.id:
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

            def cohesion(self, agents):
                import mathutils
                Vector = mathutils.Vector
                sum_pos = Vector((0, 0, 0))
                count = 0
                r = self.config['INFLUENCE_RADIUS']
                for other in agents:
                    d = (self.pos - other.pos).length
                    if d < r and other.id != self.id:
                        sum_pos += other.pos
                        count += 1
                if count > 0:
                    sum_pos /= count
                    return self.seek(sum_pos)
                return Vector((0, 0, 0))
                
            def center_attraction(self):
                import mathutils
                Vector = mathutils.Vector
                center = Vector((0,0,0))
                desired = (center - self.pos)
                dist = desired.length
                tangent = desired.cross(Vector((0,0,1))).normalized()
                
                if dist > 5:
                    return self.seek(center)
                else:
                    target_vel = (desired.normalized() * 0.3 + tangent * 0.7).normalized() * self.max_speed
                    steer = target_vel - self.vel
                    if steer.length > self.max_force:
                        steer = steer.normalized() * self.max_force
                    return steer

            def seek(self, target):
                import mathutils
                Vector = mathutils.Vector
                desired = target - self.pos
                desired = desired.normalized() * self.max_speed
                steer = desired - self.vel
                if steer.length > self.max_force:
                    steer = steer.normalized() * self.max_force
                return steer
        
        self.AgentClass = Agent
        self.agents = []
        self.material = self.get_or_create_material()
        self.collection = self.setup_collection()
        
    def setup_collection(self):
        name = self.CONFIG['COLLECTION_NAME']
        if name in bpy.data.collections:
            col = bpy.data.collections[name]
            for obj in col.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
        else:
            col = bpy.data.collections.new(name)
            bpy.context.scene.collection.children.link(col)
        return col

    def get_or_create_material(self):
        name = self.CONFIG['THIN_FILM_MAT_NAME']
        mat = bpy.data.materials.get(name)
        if not mat:
            mat = bpy.data.materials.new(name=name)
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            nodes.clear()
            
            out = nodes.new('ShaderNodeOutputMaterial')
            out.location = (300, 0)
            
            bsdf = nodes.new('ShaderNodeBsdfPrincipled')
            bsdf.location = (0, 0)
            bsdf.inputs['Metallic'].default_value = 1.0
            bsdf.inputs['Roughness'].default_value = 0.1
            
            layer_weight = nodes.new('ShaderNodeLayerWeight')
            layer_weight.location = (-600, 0)
            layer_weight.inputs['Blend'].default_value = 0.4
            
            cramp = nodes.new('ShaderNodeValToRGB')
            cramp.location = (-300, 0)
            cramp.color_ramp.interpolation = 'CARDINAL'
            
            cramp.color_ramp.elements[0].color = (0.2, 0.1, 0.5, 1)
            cramp.color_ramp.elements.new(0.25).color = (0.1, 0.6, 0.6, 1)
            cramp.color_ramp.elements.new(0.5).color = (0.6, 0.8, 0.2, 1)
            cramp.color_ramp.elements.new(0.75).color = (0.8, 0.2, 0.5, 1)
            cramp.color_ramp.elements[-1].color = (0.3, 0.0, 0.4, 1)
            
            links.new(layer_weight.outputs['Facing'], cramp.inputs['Fac'])
            links.new(cramp.outputs['Color'], bsdf.inputs['Base Color'])
            links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
        
        return mat

    def init_agents(self):
        import random
        import math
        for i in range(self.CONFIG['AGENT_COUNT']):
            angle = random.uniform(0, math.pi * 2)
            radius = random.uniform(2, 4)
            z = random.uniform(-2, 2)
            x = math.cos(angle) * radius
            y = math.sin(angle) * radius
            
            self.agents.append(self.AgentClass((x, y, z), i, self.CONFIG))
            
    def run_simulation(self):
        steps = self.CONFIG['STEPS']
        print(f"Generating Organic Ore ({self.CONFIG['AGENT_COUNT']} agents, {steps} steps)...")
        
        for s in range(steps):
            current_state = list(self.agents) 
            for agent in self.agents:
                agent.flock(current_state)
                agent.update()
                
        self.build_geometry()
        
    def build_geometry(self):
        print("Building Geometry...")
        self.create_paths()
        self.create_diagrid()
        self.create_fins()
        print("Geometry Generation Complete.")

    def create_paths(self):
        curve_data = bpy.data.curves.new('Organic_Paths', type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.bevel_depth = 0.04
        curve_data.resolution_u = 4
        
        for agent in self.agents:
            spline = curve_data.splines.new('POLY')
            spline.points.add(len(agent.history) - 1)
            for i, p in enumerate(agent.history):
                spline.points[i].co = (p.x, p.y, p.z, 1)
                
        obj = bpy.data.objects.new("Primary_Structure", curve_data)
        self.collection.objects.link(obj)
        obj.data.materials.append(self.material)
        
    def create_diagrid(self):
        import bmesh
        import bpy
        mesh = bpy.data.meshes.new("Diagrid_Mesh")
        bm = bmesh.new()
        
        step_interval = 8
        steps = self.CONFIG['STEPS']
        
        for t in range(0, steps, step_interval):
            positions = []
            for agent in self.agents:
                if t < len(agent.history):
                    positions.append(agent.history[t])
            
            # Track created verts to avoid duplicates
            vert_lookup = {} # key: (x,y,z), value: bm.vert
            
            for i in range(len(positions)):
                p1 = positions[i]
                connected_count = 0
                for j in range(i + 1, len(positions)):
                    p2 = positions[j]
                    dist = (p1 - p2).length
                    
                    if 0.4 < dist < 1.2 and connected_count < 3:
                        # Get or create v1
                        k1 = (p1.x, p1.y, p1.z)
                        if k1 not in vert_lookup:
                            vert_lookup[k1] = bm.verts.new(p1)
                        v1 = vert_lookup[k1]
                        
                        # Get or create v2
                        k2 = (p2.x, p2.y, p2.z)
                        if k2 not in vert_lookup:
                            vert_lookup[k2] = bm.verts.new(p2)
                        v2 = vert_lookup[k2]
                        
                        try:
                            bm.edges.new((v1, v2))
                        except ValueError:
                            pass # Edge exists
                        
                        connected_count += 1
                        
        bm.to_mesh(mesh)
        bm.free()
        
        obj = bpy.data.objects.new("Diagrid_Tension", mesh)
        self.collection.objects.link(obj)
        
        mod_wire = obj.modifiers.new("Wireframe", 'WIREFRAME')
        mod_wire.thickness = 0.02
        mod_wire.use_replace = False
        
        obj.data.materials.append(self.material)

    def create_fins(self):
        import bpy
        from mathutils import noise
        curve_data = bpy.data.curves.new('Fins', type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.bevel_depth = 0.005
        
        for agent in self.agents:
            for i in range(5, len(agent.history) - 1, 4):
                p1 = agent.history[i]
                p2 = agent.history[i+1]
                tangent = (p2 - p1).normalized()
                if tangent.length == 0: continue
                
                noise_scale = 0.5
                noise_val = noise.noise_vector(p1 * noise_scale)
                
                perp = tangent.cross(noise_val).normalized() * 0.4
                
                spline = curve_data.splines.new('POLY')
                spline.points.add(1)
                
                start = p1
                end = p1 + perp
                
                spline.points[0].co = (start.x, start.y, start.z, 1)
                spline.points[1].co = (end.x, end.y, end.z, 1)

        obj = bpy.data.objects.new("Secondary_Fins", curve_data)
        self.collection.objects.link(obj)
        obj.data.materials.append(self.material)
        
if __name__ == "__main__":
    if 'bpy' in locals():
        sim = BioStructure()
        sim.init_agents()
        sim.run_simulation()
