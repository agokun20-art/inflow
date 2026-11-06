"""Cast lock sheet: all four characters as locked 3D assets, in the set."""
import sys, os, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
from mathutils import Vector
import scene as S
from cast import CastChar, SPECS
bpy.ops.wm.read_factory_settings(use_empty=True)
S.build_set(); S.build_lights(); S.build_clock()
bpy.data.objects['clock'].location = (0.75, 0.55, 0)
def mat_knit():
    m = S.new_mat('knit', (0.012, 0.012, 0.014), rough=0.85, spec=0.3); nt = m.node_tree; p = nt.nodes['Principled BSDF']
    p.inputs['Sheen Weight'].default_value = 0.08
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 900
    bm = nt.nodes.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = 0.4; bm.inputs['Distance'].default_value = 0.0006
    nt.links.new(nz.outputs['Fac'], bm.inputs['Height']); nt.links.new(bm.outputs['Normal'], p.inputs['Normal']); return m
def mat_clear():
    m = S.new_mat('clear_frame', (0.85, 0.9, 0.95), rough=0.06); p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Transmission Weight'].default_value = 1.0; p.inputs['IOR'].default_value = 1.49; return m
def mat_lens():
    m = S.new_mat('lens', (0.015, 0.02, 0.03), rough=0.02, coat=1.0); p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Transmission Weight'].default_value = 0.35; return m
MATS = {'knit': mat_knit(), 'clear_frame': mat_clear(), 'lens': mat_lens()}
patch_m = S.textured_mat('patch', os.path.join(S.TEX, 'smiley_patch.png'), rough=0.6)
eye_m = S.new_mat('eye_gloss', (0.002, 0.002, 0.0025), rough=0.03, coat=0.0, spec=0.35)
arc_m = S.new_mat('arc_eye', (0.004, 0.004, 0.005), rough=0.12, spec=0.4)
lineup = {'bo': (-0.50, -0.10, 0.10), 'mimi': (-0.16, -0.06, -0.05), 'pip': (0.16, -0.10, 0.06), 'blu': (0.46, -0.05, -0.12)}
eye_objs = []
for name, (x, y, hd) in lineup.items():
    t0 = time.time()
    ch = CastChar(name); sp = SPECS[name]
    st = dict(x=x, y=y, lift=0.0, heading=hd, sy=1.0, bx=0.0, by=0.0, gx=0.0, gy=0.0, blinkL=0.0, blinkR=0.0, squintL=0.0, squintR=0.0,
              widen=0.0, fluff=0.0, fur_dyn=(0, 0, 0), omega=0.0, spinlag=0.0)
    g = ch.evaluate(st)
    co = S.CharObjects(ch, name=name, fur_color=sp['fur_c'], tip_color=sp['tip_c']) if name == 'bo' else None
    if co:
        co.apply(g, g, g, 1 / 24, ring=0.6); eye_objs += list(co.eyes.values()); bpy.data.objects.remove(co.catch); continue
    under = S.new_mat(f'{name}_under', tuple(np.array(sp['fur_c']) * 0.5), rough=0.85)
    S.mesh_obj(f'{name}_body', g['body'], ch.F, [under])
    # fur
    n, K = ch.fur_rest.shape[0], ch.fur_K
    hc = bpy.data.hair_curves.new(f'{name}_fur'); hc.add_curves([K] * n)
    hc.position_data.foreach_set('vector', g['fur'].reshape(-1).astype(np.float32))
    hc.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', np.tile(np.linspace(0.000165, 0.00005, K), n).astype(np.float32))
    hc.attributes.new('shade', 'FLOAT', 'CURVE').data.foreach_set('value', ch.fur_shade.astype(np.float32))
    ob = bpy.data.objects.new(f'{name}_fur', hc); bpy.context.scene.collection.objects.link(ob)
    tmp = S.CharObjects.__new__(S.CharObjects)
    # reuse the fur shader builder by constructing a throwaway material the same way
    fm = bpy.data.materials.new(f'{name}_furmat'); fm.use_nodes = True; nt = fm.node_tree; p = nt.nodes['Principled BSDF']
    p.inputs['Roughness'].default_value = 0.42; p.inputs['Specular IOR Level'].default_value = 0.45
    hi = nt.nodes.new('ShaderNodeHairInfo'); at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'shade'
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (*sp['fur_c'], 1); mx.inputs['B'].default_value = (*sp['tip_c'], 1)
    pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.2
    nt.links.new(hi.outputs['Intercept'], pw.inputs[0]); nt.links.new(pw.outputs[0], mx.inputs['Factor'])
    vr = nt.nodes.new('ShaderNodeMapRange'); vr.inputs['To Min'].default_value = 0.8; vr.inputs['To Max'].default_value = 1.2
    nt.links.new(at.outputs['Fac'], vr.inputs['Value'])
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
    nt.links.new(mx.outputs['Result'], mul.inputs['A']); nt.links.new(vr.outputs['Result'], mul.inputs['B']); nt.links.new(mul.outputs['Result'], p.inputs['Base Color'])
    hc.materials.append(fm)
    # eyes
    for key in ('eyeL', 'eyeR'):
        if sp['eye'] == 'arc':
            pts = g[key]; segs = 10; rows = len(pts) // segs
            F = [(i * segs + k, i * segs + (k + 1) % segs, (i + 1) * segs + (k + 1) % segs, (i + 1) * segs + k) for i in range(rows - 1) for k in range(segs)]
            eye_objs.append(S.mesh_obj(f'{name}_{key}', pts, F, [arc_m]))
        else:
            eye_objs.append(S.mesh_obj(f'{name}_{key}', g[key], ch.eye_faces, [eye_m]))
    for i, (verts, faces, mk) in enumerate(ch.acc_parts):
        S.mesh_obj(f'{name}_acc{i}', g['acc'][i], faces, [MATS[mk]])
    if 'patch' in g:
        po = S.mesh_obj(f'{name}_patch', g['patch'], [(0, 1, 2, 3)], [patch_m], smooth=False)
        po.data.uv_layers.new(); uv = po.data.uv_layers.active.data
        for li, c in zip(range(4), [(0, 0), (1, 0), (1, 1), (0, 1)]): uv[li].uv = c
    print(name, 'strands', n, round(time.time() - t0, 1), 's')
# shared catchlight for all eyes
cl = bpy.data.lights.new('catch', 'AREA'); cl.energy = 6; cl.size = 0.08
clo = bpy.data.objects.new('catch', cl); bpy.context.scene.collection.objects.link(clo)
coll = bpy.data.collections.new('eyes_all')
for e in eye_objs: coll.objects.link(e)
clo.light_linking.receiver_collection = coll
cam_d = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cam_d); bpy.context.scene.collection.objects.link(cam); bpy.context.scene.camera = cam
S.setup_render(res=(1280, 536), spp=20, mb=False)
bpy.context.scene.cycles.diffuse_bounces = 1
bpy.data.objects['room_bounce'].data.energy *= 2.2
views = {'front': ((0.0, -1.2, 0.2), (-0.02, -0.08, 0.13), 30), 'threequarter': ((0.85, -1.05, 0.28), (-0.02, -0.08, 0.13), 30),
         'mimi_cu': ((-0.05, -0.62, 0.2), (-0.16, -0.06, 0.16), 85), 'blu_cu': ((0.62, -0.55, 0.26), (0.46, -0.05, 0.17), 70)}
ONLY = os.environ.get('VIEWS', '').split(',') if os.environ.get('VIEWS') else list(views)
views = {k: v for k, v in views.items() if k in ONLY}
for nm, (loc, tgt, lens) in views.items():
    cam.location = Vector(loc); cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lens; cam_d.dof.use_dof = True; cam_d.dof.focus_distance = (Vector(tgt) - Vector(loc)).length; cam_d.dof.aperture_fstop = 5.6
    clo.location = Vector(loc) + Vector((0.05, 0.25, 0.08)); clo.rotation_euler = (Vector(tgt) - clo.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.render.filepath = f'out/cast_lock_{nm}.png'
    t0 = time.time(); bpy.ops.render.render(write_still=True); print(nm, round(time.time() - t0, 1), 's')
