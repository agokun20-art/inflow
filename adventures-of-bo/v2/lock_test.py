import sys, time, math
sys.path.insert(0, '.')
import bpy, numpy as np
from mathutils import Vector
import scene as S
from rig import Character, BO
bpy.ops.wm.read_factory_settings(use_empty=True)
t0 = time.time()
S.build_set(); S.build_lights(); clock, hands = S.build_clock()
ch = Character(BO)
co = S.CharObjects(ch, decimate=int(sys.argv[1]) if len(sys.argv) > 1 else 1)
print('build', round(time.time() - t0, 1), 's')
st = dict(x=0.0, y=0.10, lift=0.0, heading=math.pi, sy=1.0, bx=0.0, by=0.0, gx=0.0, gy=0.0,
          blinkL=0.0, blinkR=0.0, squintL=0.0, squintR=0.0, widen=0.0, fluff=0.0, fur_dyn=(0, 0, 0), omega=0.0, spinlag=0.0)
geo = ch.evaluate(st)
cam_d = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cam_d); bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam
S.setup_render(res=(960, 402), spp=int(sys.argv[2]) if len(sys.argv) > 2 else 24, mb=False)
def aim(loc, tgt, lens, fstop=2.8):
    cam.location = Vector(loc); cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lens; cam_d.dof.use_dof = True; cam_d.dof.focus_distance = (Vector(tgt) - Vector(loc)).length; cam_d.dof.aperture_fstop = fstop
views = {'front34': ((0.42, 0.95, 0.20), (0.0, 0.12, 0.15), 50), 'profile': ((0.95, 0.10, 0.13), (0.0, 0.18, 0.13), 50),
         'wide_low': ((-0.35, -1.05, 0.07), (0.05, 0.3, 0.22), 24)}
for name, (loc, tgt, lens) in views.items():
    aim(loc, tgt, lens)
    co.apply(geo, geo, geo, 1/24, ring=4.0, cam=cam)
    bpy.context.scene.render.filepath = f'out/lock_{name}.png'
    t1 = time.time(); bpy.ops.render.render(write_still=True); print(name, round(time.time() - t1, 1), 's')
bpy.ops.wm.save_as_mainfile(filepath='/home/user/inflow/adventures-of-bo/v2/out/lock_scene.blend')
