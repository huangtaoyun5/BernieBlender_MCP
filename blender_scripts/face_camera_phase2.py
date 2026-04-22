"""
face_camera_phase2.py
Rotate all eligible objects in AR_PHASE2_V2 to face the active camera.
Uses the same rotation formula as face_camera_text() — baked Euler, no constraint.
Removes any previous Track To constraints first.
"""

import bpy
import math
from mathutils import Vector

COLLECTION_NAME = "AR_PHASE2_V2"
CAMERA_NAME = "starightzkm.fspy"

SKIP_NAMES = {"P2V2_ShatteredGeo", "P2V2_Tendrils", "P2V2_ScanGrid"}
SKIP_PREFIXES = ("P2V2_Tendril", "P2V2_Grid", "P2V2_Scan")

col = bpy.data.collections.get(COLLECTION_NAME)
cam = bpy.data.objects.get(CAMERA_NAME)

if not col:
    raise RuntimeError(f"Collection '{COLLECTION_NAME}' not found")
if not cam:
    raise RuntimeError(f"Camera '{CAMERA_NAME}' not found")

cam_pos = cam.location.copy()
count = 0
skipped = 0

for obj in col.all_objects:
    # Remove old Track To constraints regardless
    for c in list(obj.constraints):
        if c.type == 'TRACK_TO':
            obj.constraints.remove(c)

    skip = False
    if obj.name in SKIP_NAMES:
        skip = True
    for prefix in SKIP_PREFIXES:
        if obj.name.startswith(prefix):
            skip = True
    if obj.type == 'CURVE':
        skip = True

    if skip:
        skipped += 1
        continue

    direction = cam_pos - obj.location
    if direction.length < 0.0001:
        skipped += 1
        continue

    direction.normalize()

    # Same formula as face_camera_text() — validated in phase2_v2_breach.py
    rot_z = math.atan2(direction.y, direction.x) + math.pi / 2
    horiz_dist = math.sqrt(direction.x ** 2 + direction.y ** 2)
    rot_x = math.pi / 2 - math.atan2(direction.z, horiz_dist)

    obj.rotation_euler = (rot_x, 0, rot_z)
    count += 1

print(f"[face_camera_phase2] Rotated {count} objects toward {CAMERA_NAME}, skipped {skipped}")
