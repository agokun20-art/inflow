"""Adventures of Bo v2 - Blender scene: set, lights, hero prop, character objects."""
import math
import os

import bpy
import numpy as np
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'tex')
rng = np.random.default_rng(3)


# ------------------------------------------------------------------ helpers
def new_mat(name, color=(0.5, 0.5, 0.5), rough=0.5, metal=0.0, coat=0.0, spec=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    p.inputs['Coat Weight'].default_value = coat
    p.inputs['Specular IOR Level'].default_value = spec
    return m


def img_node(m, path, coords='UV', repeat=True, alpha=False):
    nt = m.node_tree
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path, check_existing=True)
    tex.extension = 'REPEAT' if repeat else 'CLIP'
    return tex


def textured_mat(name, path, rough=0.6, bump=0.0, scale=(1, 1, 1), coords='UV', emission=0.0):
    m = new_mat(name, rough=rough)
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    tex = img_node(m, path)
    if coords != 'UV' or scale != (1, 1, 1):
        tc = nt.nodes.new('ShaderNodeTexCoord')
        mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = scale
        nt.links.new(tc.outputs[coords], mp.inputs['Vector'])
        nt.links.new(mp.outputs['Vector'], tex.inputs['Vector'])
    nt.links.new(tex.outputs['Color'], p.inputs['Base Color'])
    if bump:
        b = nt.nodes.new('ShaderNodeBump')
        b.inputs['Strength'].default_value = bump
        b.inputs['Distance'].default_value = 0.002
        nt.links.new(tex.outputs['Color'], b.inputs['Height'])
        nt.links.new(b.outputs['Normal'], p.inputs['Normal'])
    if emission:
        nt.links.new(tex.outputs['Color'], p.inputs['Emission Color'])
        p.inputs['Emission Strength'].default_value = emission
    return m


def mesh_obj(name, V, F, mats=None, mat_idx=None, smooth=True, coll=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], [tuple(f) for f in F])
    me.update()
    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    if mats:
        for m in mats:
            me.materials.append(m)
    if mat_idx is not None:
        me.polygons.foreach_set('material_index', np.asarray(mat_idx, np.int32))
    if smooth:
        me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), bool))
    return ob


def box(name, size, loc, mat, rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    ob = bpy.context.object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        md = ob.modifiers.new('bev', 'BEVEL')
        md.width = bevel
        md.segments = 3
    ob.data.materials.append(mat)
    return ob


def cyl(name, r, depth, loc, mat, rot=(0, 0, 0), verts=48, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    ob = bpy.context.object
    ob.name = name
    if bevel:
        md = ob.modifiers.new('bev', 'BEVEL')
        md.width = bevel
        md.segments = 3
        md.limit_method = 'ANGLE'
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(mat)
    return ob


def sphere(name, r, loc, mat, scale=(1, 1, 1), seg=48):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(mat)
    return ob


# ------------------------------------------------------------------ set
ROOM = dict(x0=-1.3, x1=1.3, y0=-1.25, y1=1.2, wall_h=1.05)
WINDOW = dict(x=0.05, z=0.62, r=0.27)
CLOCK_POS = Vector((0.0, 0.42, 0.0))


def wood_floor_mat():
    m = new_mat('floor', rough=0.45)
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Mortar Size'].default_value = 0.0012
    br.inputs['Brick Width'].default_value = 0.62
    br.inputs['Row Height'].default_value = 0.082
    br.inputs['Color1'].default_value = (0.36, 0.20, 0.10, 1)
    br.inputs['Color2'].default_value = (0.25, 0.135, 0.065, 1)
    br.inputs['Mortar'].default_value = (0.03, 0.018, 0.01, 1)
    br.offset = 0.37
    wv = nt.nodes.new('ShaderNodeTexWave')
    wv.wave_type = 'BANDS'
    wv.bands_direction = 'Y'
    wv.inputs['Scale'].default_value = 28
    wv.inputs['Distortion'].default_value = 7
    wv.inputs['Detail'].default_value = 3
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 3.5
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Factor'].default_value = 0.35
    nt.links.new(tc.outputs['Object'], br.inputs['Vector'])
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    nt.links.new(br.outputs['Color'], mix.inputs['A'])
    nt.links.new(wv.outputs['Color'], mix.inputs['B'])
    nt.links.new(mix.outputs['Result'], p.inputs['Base Color'])
    ramp = nt.nodes.new('ShaderNodeMapRange')
    ramp.inputs['To Min'].default_value = 0.32
    ramp.inputs['To Max'].default_value = 0.6
    nt.links.new(nz.outputs['Fac'], ramp.inputs['Value'])
    nt.links.new(ramp.outputs['Result'], p.inputs['Roughness'])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.35
    bump.inputs['Distance'].default_value = 0.0015
    nt.links.new(br.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], p.inputs['Normal'])
    return m


def build_set():
    sc = bpy.context.scene
    R = ROOM
    W, D = R['x1'] - R['x0'], R['y1'] - R['y0']
    # floor
    bpy.ops.mesh.primitive_plane_add(size=1, location=((R['x0'] + R['x1']) / 2, (R['y0'] + R['y1']) / 2, 0))
    fl = bpy.context.object
    fl.name = 'floor'
    fl.scale = (W, D, 1)
    bpy.ops.object.transform_apply(scale=True)
    fl.data.materials.append(wood_floor_mat())
    # rug
    rug_m = textured_mat('rug', os.path.join(TEX, 'rug.png'), rough=0.9, bump=0.15)
    rug = box('rug', (1.25, 0.84, 0.007), (-0.05, -0.12, 0.0035), rug_m, bevel=0.003)
    rug.data.uv_layers.new()
    bpy.context.view_layer.objects.active = rug
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.cube_project(cube_size=1.0)
    bpy.ops.object.mode_set(mode='OBJECT')
    # use top-down projection for rug texture
    uv = rug.data.uv_layers.active.data
    for poly in rug.data.polygons:
        for li in poly.loop_indices:
            v = rug.data.vertices[rug.data.loops[li].vertex_index].co
            uv[li].uv = ((v.x + 0.625) / 1.25, (v.y + 0.42) / 0.84)
    # walls (plaster) with a baseboard
    pl = textured_mat('plaster', os.path.join(TEX, 'plaster.png'), rough=0.85, bump=0.25, scale=(1.6, 1.6, 1.6), coords='Object')
    trim = new_mat('trim', (0.62, 0.52, 0.38), rough=0.4)
    h = R['wall_h']
    walls = {
        'wall_back': ((W, 0.04, h), (0, R['y1'] + 0.02, h / 2)),
        'wall_front': ((W, 0.04, h), (0, R['y0'] - 0.02, h / 2)),
        'wall_left': ((0.04, D, h), (R['x0'] - 0.02, 0, h / 2)),
        'wall_right': ((0.04, D, h), (R['x1'] + 0.02, 0, h / 2)),
    }
    for name, (s, loc) in walls.items():
        box(name, s, loc, pl)
    for name, (s, loc) in walls.items():
        bs = (s[0] + 0.001 if s[0] > 0.05 else 0.012, s[1] + 0.001 if s[1] > 0.05 else 0.012, 0.075)
        off = Vector((0, 0, 0))
        if name == 'wall_back':
            off = Vector((0, -0.025, 0))
        if name == 'wall_front':
            off = Vector((0, 0.025, 0))
        if name == 'wall_left':
            off = Vector((0.025, 0, 0))
        if name == 'wall_right':
            off = Vector((-0.025, 0, 0))
        box(name + '_base', bs, Vector((loc[0], loc[1], 0.0375)) + off, trim, bevel=0.002)
    # round window: cut the back wall
    wb = bpy.data.objects['wall_back']
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=WINDOW['r'], depth=0.3,
                                        location=(WINDOW['x'], R['y1'] + 0.02, WINDOW['z']), rotation=(math.pi / 2, 0, 0))
    cutter = bpy.context.object
    md = wb.modifiers.new('win', 'BOOLEAN')
    md.object = cutter
    md.operation = 'DIFFERENCE'
    bpy.context.view_layer.objects.active = wb
    bpy.ops.object.modifier_apply(modifier='win')
    bpy.data.objects.remove(cutter)
    frame_m = new_mat('window_frame', (0.78, 0.72, 0.62), rough=0.35)
    bpy.ops.mesh.primitive_torus_add(major_radius=WINDOW['r'] + 0.012, minor_radius=0.022, major_segments=96,
                                     location=(WINDOW['x'], R['y1'] - 0.005, WINDOW['z']), rotation=(math.pi / 2, 0, 0))
    tor = bpy.context.object
    tor.name = 'window_frame'
    tor.scale = (1, 1, 1.0)
    bpy.ops.object.shade_smooth()
    tor.data.materials.append(frame_m)
    box('mullion_v', (0.018, 0.02, WINDOW['r'] * 2), (WINDOW['x'], R['y1'] + 0.005, WINDOW['z']), frame_m)
    box('mullion_h', (WINDOW['r'] * 2, 0.02, 0.018), (WINDOW['x'], R['y1'] + 0.005, WINDOW['z']), frame_m)
    box('sill', (WINDOW['r'] * 2.3, 0.07, 0.025), (WINDOW['x'], R['y1'] - 0.03, WINDOW['z'] - WINDOW['r'] - 0.03), frame_m, bevel=0.004)
    # outside: night sky backdrop + falling rain
    sky_m = new_mat('sky')
    nt = sky_m.node_tree
    for nd in list(nt.nodes):
        if nd.type == 'BSDF_PRINCIPLED':
            nt.nodes.remove(nd)
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Strength'].default_value = 1.4
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(os.path.join(TEX, 'night_sky.png'))
    nt.links.new(tex.outputs['Color'], em.inputs['Color'])
    nt.links.new(em.outputs[0], nt.nodes['Material Output'].inputs[0])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(WINDOW['x'], R['y1'] + 1.6, WINDOW['z'] + 0.1), rotation=(math.pi / 2, 0, 0))
    sky = bpy.context.object
    sky.name = 'sky'
    sky.scale = (3.4, 1.7, 1)
    sky.data.materials.append(sky_m)
    rain_m = bpy.data.materials.new('rain')
    rain_m.use_nodes = True
    nt = rain_m.node_tree
    for nd in list(nt.nodes):
        if nd.type == 'BSDF_PRINCIPLED':
            nt.nodes.remove(nd)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.name = 'rain_map'
    mp.inputs['Scale'].default_value = (3, 1.5, 1)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(os.path.join(TEX, 'rain.png'))
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    emr = nt.nodes.new('ShaderNodeEmission')
    emr.inputs['Color'].default_value = (0.65, 0.75, 1.0, 1)
    emr.inputs['Strength'].default_value = 0.9
    mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], tex.inputs['Vector'])
    nt.links.new(tex.outputs['Alpha'], mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(emr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs[0])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(WINDOW['x'], R['y1'] + 0.35, WINDOW['z']), rotation=(math.pi / 2, 0, 0))
    rp = bpy.context.object
    rp.name = 'rain'
    rp.scale = (1.2, 1.0, 1)
    rp.data.materials.append(rain_m)
    rp.visible_shadow = False
    sky.visible_shadow = False
    # left wall: low bookshelf with books, plant, records leaning on the floor
    wood = textured_mat('shelf_wood', os.path.join(TEX, 'wood_2.png'), rough=0.5, scale=(3, 3, 3), coords='Object')
    sx = R['x0'] + 0.16
    box('shelf_side_a', (0.3, 0.025, 0.56), (sx, -0.55, 0.28), wood, bevel=0.003)
    box('shelf_side_b', (0.3, 0.025, 0.56), (sx, 0.35, 0.28), wood, bevel=0.003)
    for z in (0.012, 0.28, 0.55):
        box(f'shelf_{z}', (0.3, 0.92, 0.024), (sx, -0.1, z), wood, bevel=0.003)
    box('shelf_back', (0.01, 0.92, 0.56), (R['x0'] + 0.012, -0.1, 0.28), wood)
    cols = [(0.45, 0.12, 0.08), (0.12, 0.25, 0.32), (0.55, 0.42, 0.15), (0.2, 0.32, 0.18), (0.38, 0.2, 0.32), (0.72, 0.64, 0.5), (0.1, 0.1, 0.12)]
    for zb in (0.024, 0.292):
        y = -0.52
        while y < 0.30:
            w = rng.uniform(0.022, 0.04)
            hh = rng.uniform(0.16, 0.235)
            dep = rng.uniform(0.17, 0.22)
            c = cols[rng.integers(len(cols))]
            mb = new_mat(f'book_{y:.3f}_{zb}', tuple(np.array(c) * rng.uniform(0.8, 1.1)), rough=rng.uniform(0.4, 0.7))
            tilt = 0.0 if rng.random() > 0.1 else math.radians(12)
            box(f'book_{y:.3f}', (dep, w, hh), (sx + 0.01, y + w / 2, zb + hh / 2), mb, rot=(tilt, 0, 0), bevel=0.0015)
            y += w + 0.002 + (0.05 if tilt else 0)
            if rng.random() < 0.06:
                y += 0.08
    pot = new_mat('pot', (0.55, 0.26, 0.15), rough=0.6)
    leaf = new_mat('leaf', (0.08, 0.22, 0.07), rough=0.45, spec=0.6)
    cyl('pot', 0.055, 0.1, (sx, 0.18, 0.62), pot, bevel=0.004)
    for k in range(14):
        a = k * 2.4
        L = 0.07 + 0.05 * rng.random()
        sphere(f'leaf{k}', 0.035, (sx + math.cos(a) * L * 0.5, 0.18 + math.sin(a) * L * 0.6, 0.68 + rng.random() * 0.08),
               leaf, scale=(1.0, 0.45, 0.12), seg=16).rotation_euler = (rng.random(), rng.random() * 0.8, a)
    for k in range(5):
        sl = textured_mat(f'sleeve{k}', os.path.join(TEX, f'sleeve_{k}.png'), rough=0.55)
        ob = box(f'record{k}', (0.008, 0.25, 0.25), (R['x0'] + 0.36 + k * 0.012, 0.62 + k * 0.03, 0.123), sl,
                 rot=(0, math.radians(-14 + k * 2.5), math.radians(rng.uniform(-6, 6))))
        ob.data.uv_layers.new()
        uvl = ob.data.uv_layers.active.data
        for poly in ob.data.polygons:
            for li in poly.loop_indices:
                v = ob.data.vertices[ob.data.loops[li].vertex_index].co
                uvl[li].uv = (v.y / 0.25 + 0.5, v.z / 0.25 + 0.5)
    # right wall: side table + brass lamp (warm practical) + Bo's floor cushion
    brass = new_mat('brass', (0.85, 0.62, 0.32), rough=0.28, metal=1.0)
    tx, ty = R['x1'] - 0.25, 0.55
    cyl('table_top', 0.17, 0.025, (tx, ty, 0.42), wood, bevel=0.004)
    for a in (0.6, 2.7, 4.8):
        cyl(f'table_leg{a}', 0.012, 0.42, (tx + math.cos(a) * 0.11, ty + math.sin(a) * 0.11, 0.21), wood)
    cyl('lamp_base', 0.06, 0.02, (tx, ty, 0.443), brass, bevel=0.005)
    cyl('lamp_stem', 0.008, 0.26, (tx, ty, 0.58), brass)
    shade = bpy.data.materials.new('lamp_shade')
    shade.use_nodes = True
    nt = shade.node_tree
    p = nt.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (0.95, 0.78, 0.55, 1)
    p.inputs['Roughness'].default_value = 0.8
    p.inputs['Transmission Weight'].default_value = 0.0
    p.inputs['Subsurface Weight'].default_value = 0.0
    p.inputs['Emission Color'].default_value = (1.0, 0.72, 0.4, 1)
    p.inputs['Emission Strength'].default_value = 3.0
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=0.15, radius2=0.09, depth=0.15, location=(tx, ty, 0.72), end_fill_type='NOTHING')
    sh = bpy.context.object
    sh.name = 'lamp_shade'
    md = sh.modifiers.new('sol', 'SOLIDIFY')
    md.thickness = 0.004
    bpy.ops.object.shade_smooth()
    sh.data.materials.append(shade)
    lamp = bpy.data.lights.new('lamp_bulb', 'POINT')
    lamp.energy = 26
    lamp.shadow_soft_size = 0.03
    lamp.color = (1.0, 0.7, 0.42)
    lo = bpy.data.objects.new('lamp_bulb', lamp)
    lo.location = (tx, ty, 0.69)
    sc.collection.objects.link(lo)
    cush = new_mat('cushion', (0.28, 0.36, 0.42), rough=0.85)
    c = cyl('bo_cushion', 0.2, 0.06, (R['x1'] - 0.42, 0.18, 0.03), cush, verts=64, bevel=0.022)
    # front wall: door ajar to a dark hallway + a small framed picture
    door_m = new_mat('door', (0.32, 0.2, 0.12), rough=0.5)
    box('door_frame_l', (0.04, 0.05, 0.72), (0.55, R['y0'] + 0.02, 0.36), trim, bevel=0.003)
    box('door_frame_r', (0.04, 0.05, 0.72), (0.98, R['y0'] + 0.02, 0.36), trim, bevel=0.003)
    box('door_frame_t', (0.47, 0.05, 0.04), (0.765, R['y0'] + 0.02, 0.72), trim, bevel=0.003)
    box('door_gap', (0.39, 0.03, 0.70), (0.765, R['y0'] - 0.0, 0.35), new_mat('dark', (0.004, 0.004, 0.006), rough=1))
    box('door_leaf', (0.38, 0.03, 0.69), (0.62, R['y0'] + 0.17, 0.345), door_m, rot=(0, 0, math.radians(68)), bevel=0.004)
    pic = textured_mat('picture', os.path.join(TEX, 'sleeve_2.png'), rough=0.4)
    box('picture', (0.2, 0.012, 0.16), (-0.4, R['y0'] + 0.01, 0.62), pic, bevel=0.003)
    # ceiling beams (attic)
    beam = textured_mat('beam', os.path.join(TEX, 'wood_2.png'), rough=0.6, scale=(2, 2, 2), coords='Object')
    for x in np.linspace(R['x0'] + 0.2, R['x1'] - 0.2, 5):
        box(f'beam{x:.2f}', (0.06, D, 0.08), (x, 0, R['wall_h'] + 0.04), beam)
    box('ceiling', (W, D, 0.02), (0, 0, R['wall_h'] + 0.09), pl)
    dress(pl, trim, wood)
    return dict(rain_map=rain_m.node_tree.nodes['rain_map'])


def dress(pl, trim, wood):
    R = ROOM
    wain = new_mat('wainscot', (0.20, 0.27, 0.27), rough=0.45)
    nt = wain.node_tree
    p = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Brick Width'].default_value = 0.09
    br.inputs['Row Height'].default_value = 2.0
    br.inputs['Mortar Size'].default_value = 0.0018
    br.inputs['Color1'].default_value = (0.17, 0.25, 0.25, 1)
    br.inputs['Color2'].default_value = (0.15, 0.22, 0.22, 1)
    br.inputs['Mortar'].default_value = (0.04, 0.05, 0.05, 1)
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value = (math.pi / 2, 0, 0)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], br.inputs['Vector'])
    nt.links.new(br.outputs['Color'], p.inputs['Base Color'])
    bm = nt.nodes.new('ShaderNodeBump')
    bm.inputs['Strength'].default_value = 0.5
    bm.inputs['Distance'].default_value = 0.001
    nt.links.new(br.outputs['Fac'], bm.inputs['Height'])
    nt.links.new(bm.outputs['Normal'], p.inputs['Normal'])
    W = R['x1'] - R['x0']
    D = R['y1'] - R['y0']
    hw = 0.34
    box('wain_back', (W, 0.012, hw), (0, R['y1'] - 0.006, hw / 2), wain)
    box('wain_right', (0.012, D, hw), (R['x1'] - 0.006, 0, hw / 2), wain)
    box('wain_front_a', (1.7, 0.012, hw), (-0.43, R['y0'] + 0.006, hw / 2), wain)
    box('rail_back', (W, 0.03, 0.02), (0, R['y1'] - 0.014, hw), trim, bevel=0.003)
    box('rail_right', (0.03, D, 0.02), (R['x1'] - 0.014, 0, hw), trim, bevel=0.003)
    box('rail_front', (1.7, 0.03, 0.02), (-0.43, R['y0'] + 0.014, hw), trim, bevel=0.003)
    # curtains: folded panels either side of the round window
    cur = new_mat('curtain', (0.42, 0.16, 0.12), rough=0.75)
    cur.node_tree.nodes['Principled BSDF'].inputs['Sheen Weight'].default_value = 0.6
    for side in (-1, 1):
        cx = WINDOW['x'] + side * (WINDOW['r'] + 0.13)
        nx, nz = 40, 30
        V, F = [], []
        for j in range(nz):
            z = WINDOW['z'] + 0.42 - j * (0.95 / (nz - 1))
            gather = 1.0 if z > WINDOW['z'] - 0.1 else 0.55 + 0.45 * (z - (WINDOW['z'] - 0.53)) / 0.43
            for i in range(nx):
                u = i / (nx - 1) - 0.5
                x = cx + u * 0.20 * max(0.5, gather)
                y = R['y1'] - 0.06 + 0.018 * math.sin(i / (nx - 1) * 7 * math.pi) * (1.4 - gather * 0.4)
                V.append((x, y, max(z, 0.02)))
        for j in range(nz - 1):
            for i in range(nx - 1):
                F.append((j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i))
        ob = mesh_obj(f'curtain{side}', np.array(V), F, [cur])
        md = ob.modifiers.new('sol', 'SOLIDIFY')
        md.thickness = 0.004
    rod = bpy.data.materials.get('brass')
    cyl('curtain_rod', 0.008, (WINDOW['r'] + 0.3) * 2, (WINDOW['x'], R['y1'] - 0.06, WINDOW['z'] + 0.43), rod or trim, rot=(0, math.pi / 2, 0))
    # sill: small cactus + jar
    sz = WINDOW['z'] - WINDOW['r'] - 0.017
    potm = bpy.data.materials.get('pot')
    cact = new_mat('cactus', (0.12, 0.3, 0.16), rough=0.5)
    c1 = cyl('sill_pot', 0.03, 0.045, (WINDOW['x'] - 0.17, R['y1'] - 0.03, sz + 0.0225), potm or trim, bevel=0.003)
    sphere('cactus', 0.026, (WINDOW['x'] - 0.17, R['y1'] - 0.03, sz + 0.07), cact, scale=(1, 1, 1.5), seg=24)
    jar = new_mat('jar', (0.85, 0.75, 0.5), rough=0.15)
    jar.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value = 0.6
    cyl('sill_jar', 0.022, 0.05, (WINDOW['x'] + 0.18, R['y1'] - 0.035, sz + 0.025), jar, bevel=0.004)
    # floor clutter near the window wall: two stacked books
    for k, (c, w_, h_) in enumerate([((0.45, 0.14, 0.1), 0.2, 0.03), ((0.16, 0.28, 0.33), 0.18, 0.025)]):
        box(f'floorbook{k}', (w_, 0.14, h_), (0.55, 0.95, 0.015 + k * 0.028), new_mat(f'fb{k}', c, rough=0.55),
            rot=(0, 0, math.radians(12 - k * 20)), bevel=0.002)


def build_lights():
    sc = bpy.context.scene
    # moonlight through the round window
    moon = bpy.data.lights.new('moon', 'SPOT')
    moon.energy = 2200
    moon.spot_size = math.radians(34)
    moon.spot_blend = 0.25
    moon.shadow_soft_size = 0.05
    moon.color = (0.55, 0.66, 1.0)
    mo = bpy.data.objects.new('moon', moon)
    sc.collection.objects.link(mo)
    wc = Vector((WINDOW['x'], ROOM['y1'], WINDOW['z']))
    tgt = Vector((-0.02, 0.22, 0.0))
    dirn = (tgt - wc).normalized()
    mo.location = wc - dirn * 1.1
    direction = tgt - mo.location
    mo.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    # soft warm fill from the room side (bounce off the lamp-lit walls)
    fill = bpy.data.lights.new('fill', 'AREA')
    fill.energy = 5
    fill.size = 1.2
    fill.color = (1.0, 0.78, 0.6)
    fo = bpy.data.objects.new('fill', fill)
    sc.collection.objects.link(fo)
    fo.location = (0.3, -1.0, 0.95)
    fo.rotation_euler = (Vector((0, 0.2, 0.1)) - fo.location).to_track_quat('-Z', 'Y').to_euler()
    rim = bpy.data.lights.new('moon_rim', 'AREA')
    rim.energy = 35
    rim.size = 0.5
    rim.color = (0.55, 0.68, 1.0)
    ro = bpy.data.objects.new('moon_rim', rim)
    sc.collection.objects.link(ro)
    ro.location = (WINDOW['x'], ROOM['y1'] - 0.15, WINDOW['z'] + 0.05)
    ro.rotation_euler = (Vector((0, 0.1, 0.12)) - ro.location).to_track_quat('-Z', 'Y').to_euler()
    # warm bounce from the lamp-lit room: motivates a key on Bo whenever he faces into the room
    bnc = bpy.data.lights.new('room_bounce', 'AREA')
    bnc.energy = 22
    bnc.size = 0.9
    bnc.color = (1.0, 0.72, 0.48)
    bo_ = bpy.data.objects.new('room_bounce', bnc)
    sc.collection.objects.link(bo_)
    bo_.location = (0.55, -1.0, 0.55)
    bo_.rotation_euler = (Vector((0.0, -0.05, 0.15)) - bo_.location).to_track_quat('-Z', 'Y').to_euler()
    sc.world = bpy.data.worlds.new('night')
    sc.world.use_nodes = True
    sc.world.node_tree.nodes['Background'].inputs[0].default_value = (0.004, 0.006, 0.012, 1)


# ------------------------------------------------------------------ hero prop: alarm clock
def build_clock():
    enamel = new_mat('clock_enamel', (0.27, 0.55, 0.47), rough=0.22, coat=0.6)
    chrome = new_mat('chrome', (0.9, 0.9, 0.9), rough=0.12, metal=1.0)
    brass = bpy.data.materials.get('brass') or new_mat('brass', (0.85, 0.62, 0.32), rough=0.28, metal=1.0)
    ink = new_mat('clock_ink', (0.02, 0.02, 0.02), rough=0.4)
    red = new_mat('clock_red', (0.6, 0.05, 0.03), rough=0.4)
    C = CLOCK_POS
    cz = 0.085
    root = bpy.data.objects.new('clock', None)
    bpy.context.scene.collection.objects.link(root)
    root.location = C
    root.rotation_euler = (0, 0, math.radians(40))
    parts = []
    parts.append(cyl('clock_body', 0.055, 0.036, (0, 0, cz), enamel, rot=(math.pi / 2, 0, 0), verts=96, bevel=0.006))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.0535, minor_radius=0.0045, major_segments=96, location=(0, -0.019, cz), rotation=(math.pi / 2, 0, 0))
    t = bpy.context.object
    t.name = 'clock_bezel'
    bpy.ops.object.shade_smooth()
    t.data.materials.append(chrome)
    parts.append(t)
    dial = textured_mat('clock_dial', os.path.join(TEX, 'clock_dial.png'), rough=0.35)
    bpy.ops.mesh.primitive_circle_add(vertices=96, radius=0.049, fill_type='NGON', location=(0, -0.0185, cz), rotation=(math.pi / 2, 0, 0))
    d = bpy.context.object
    d.name = 'clock_dial'
    d.data.materials.append(dial)
    d.data.uv_layers.new()
    uvl = d.data.uv_layers.active.data
    for poly in d.data.polygons:
        for li in poly.loop_indices:
            v = d.data.vertices[d.data.loops[li].vertex_index].co
            uvl[li].uv = (v.x / 0.098 + 0.5, v.y / 0.098 + 0.5)
    parts.append(d)
    glass = bpy.data.materials.new('clock_glass')
    glass.use_nodes = True
    gp = glass.node_tree.nodes['Principled BSDF']
    gp.inputs['Transmission Weight'].default_value = 1.0
    gp.inputs['Roughness'].default_value = 0.02
    gp.inputs['IOR'].default_value = 1.45
    g = sphere('clock_glass', 0.05, (0, -0.0195, cz), glass, scale=(1, 0.12, 1), seg=48)
    g.visible_shadow = False
    parts.append(g)
    for side in (-1, 1):
        ang = math.radians(38) * side
        bx, bz = math.sin(ang) * 0.06, cz + math.cos(ang) * 0.06
        b = sphere(f'clock_bell{side}', 0.026, (bx, 0.0, bz), brass, scale=(1, 1, 0.75))
        b.rotation_euler = (0, ang, 0)
        parts.append(b)
        parts.append(cyl(f'clock_post{side}', 0.003, 0.02, (math.sin(ang) * 0.052, 0, cz + math.cos(ang) * 0.052), brass, rot=(0, ang, 0), verts=12))
        parts.append(cyl(f'clock_leg{side}', 0.007, 0.03, (side * 0.032, 0, 0.022), chrome, rot=(0, side * 0.35, 0), verts=24))
    parts.append(cyl('clock_hammer', 0.0025, 0.07, (0, 0.004, cz + 0.068), brass, rot=(0, math.pi / 2, 0), verts=12))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.028, minor_radius=0.003, major_segments=48, location=(0, 0.003, cz + 0.07), rotation=(math.pi / 2, 0, 0))
    hnd = bpy.context.object
    hnd.name = 'clock_handle'
    hnd.scale = (1, 1, 0.7)
    bpy.ops.object.shade_smooth()
    hnd.data.materials.append(chrome)
    parts.append(hnd)
    hands = {}
    for name, L, w, mat, zoff, ang in (('hour', 0.026, 0.0035, ink, -0.0200, math.radians(-25)),
                                       ('minute', 0.039, 0.0025, ink, -0.0203, math.radians(150)),
                                       ('second', 0.042, 0.0010, red, -0.0206, 0.0)):
        pivot = bpy.data.objects.new(f'hand_{name}_pivot', None)
        bpy.context.scene.collection.objects.link(pivot)
        pivot.location = (0, zoff, cz)
        pivot.parent = root
        hob = box(f'hand_{name}', (w, 0.0008, L), (0, 0, L / 2 - 0.006), mat)
        hob.parent = pivot
        pivot.rotation_euler = (0, ang, 0)
        hands[name] = pivot
    cap = cyl('clock_cap', 0.004, 0.004, (0, -0.0212, cz), brass, rot=(math.pi / 2, 0, 0), verts=24)
    parts.append(cap)
    for p in parts:
        p.parent = root
    return root, hands


# ------------------------------------------------------------------ character objects
class CharObjects:
    def __init__(self, ch, name='Bo', fur_color=(0.011, 0.011, 0.013), tip_color=(0.055, 0.056, 0.064), decimate=1):
        self.ch = ch
        self.dec = decimate
        sc = bpy.context.scene
        under = new_mat(f'{name}_under', (0.008, 0.008, 0.009), rough=0.85)
        self.body = mesh_obj(f'{name}_body', ch.V, ch.F, [under])
        self.body.data.attributes.new('velocity', 'FLOAT_VECTOR', 'POINT')
        # fur
        n = ch.fur_rest.shape[0] // decimate
        self.nf = n
        K = ch.fur_K
        hc = bpy.data.hair_curves.new(f'{name}_fur')
        hc.add_curves([K] * n)
        rad = np.tile(np.linspace(0.000165, 0.00005, K), n).astype(np.float32) * (1.0 + 0.6 * (decimate > 1))
        hc.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', rad)
        hc.attributes.new('velocity', 'FLOAT_VECTOR', 'POINT')
        hc.attributes.new('shade', 'FLOAT', 'CURVE').data.foreach_set('value', ch.fur_shade[::decimate][:n])
        self.fur = bpy.data.objects.new(f'{name}_fur', hc)
        sc.collection.objects.link(self.fur)
        fm = bpy.data.materials.new(f'{name}_fur')
        fm.use_nodes = True
        nt = fm.node_tree
        p = nt.nodes['Principled BSDF']
        p.inputs['Roughness'].default_value = 0.42
        p.inputs['Specular IOR Level'].default_value = 0.45
        hi = nt.nodes.new('ShaderNodeHairInfo')
        at = nt.nodes.new('ShaderNodeAttribute')
        at.attribute_name = 'shade'
        mixc = nt.nodes.new('ShaderNodeMix')
        mixc.data_type = 'RGBA'
        mixc.inputs['A'].default_value = (*fur_color, 1)
        mixc.inputs['B'].default_value = (*tip_color, 1)
        pw = nt.nodes.new('ShaderNodeMath')
        pw.operation = 'POWER'
        pw.inputs[1].default_value = 2.2
        nt.links.new(hi.outputs['Intercept'], pw.inputs[0])
        nt.links.new(pw.outputs[0], mixc.inputs['Factor'])
        var = nt.nodes.new('ShaderNodeMapRange')
        var.inputs['To Min'].default_value = 0.72
        var.inputs['To Max'].default_value = 1.3
        nt.links.new(at.outputs['Fac'], var.inputs['Value'])
        mul = nt.nodes.new('ShaderNodeMix')
        mul.data_type = 'RGBA'
        mul.blend_type = 'MULTIPLY'
        mul.inputs['Factor'].default_value = 1.0
        nt.links.new(mixc.outputs['Result'], mul.inputs['A'])
        nt.links.new(var.outputs['Result'], mul.inputs['B'])
        nt.links.new(mul.outputs['Result'], p.inputs['Base Color'])
        hc.materials.append(fm)
        # eyes
        eye_m = new_mat('eye_gloss', (0.002, 0.002, 0.0025), rough=0.03, coat=0.0, spec=0.35)
        self.eyes = {}
        for k in ('eyeL', 'eyeR'):
            V = np.zeros((len(ch.eye_unit), 3))
            self.eyes[k] = mesh_obj(f'{name}_{k}', V, ch.eye_faces, [eye_m])
            self.eyes[k].data.attributes.new('velocity', 'FLOAT_VECTOR', 'POINT')
        # headphones
        shell = new_mat('hp_shell', (0.012, 0.012, 0.014), rough=0.38, coat=0.12)
        ring = bpy.data.materials.new('hp_ring')
        ring.use_nodes = True
        rp = ring.node_tree.nodes['Principled BSDF']
        rp.inputs['Base Color'].default_value = (0.35, 0.45, 0.6, 1)
        rp.inputs['Emission Color'].default_value = (0.55, 0.74, 1.0, 1)
        rp.inputs['Emission Strength'].default_value = 0.6
        self.ring_node = rp
        cushion = new_mat('hp_cushion', (0.012, 0.012, 0.014), rough=0.6)
        self.hp = mesh_obj(f'{name}_headphones', ch.hp_V, ch.hp_F, [shell, ring, cushion], ch.hp_M)
        self.hp.data.attributes.new('velocity', 'FLOAT_VECTOR', 'POINT')
        # catchlight lamp linked only to the eyes (gives the reference's white highlights)
        cl = bpy.data.lights.new(f'{name}_catch', 'AREA')
        cl.energy = 4.0
        cl.size = 0.035
        cl.color = (1.0, 0.95, 0.9)
        self.catch = bpy.data.objects.new(f'{name}_catch', cl)
        sc.collection.objects.link(self.catch)
        coll = bpy.data.collections.new(f'{name}_eyes_coll')
        for e in self.eyes.values():
            coll.objects.link(e)
        self.catch.light_linking.receiver_collection = coll

    def _set(self, ob, P, vel, attr='co'):
        if ob.type == 'MESH':
            ob.data.vertices.foreach_set('co', P.astype(np.float32).ravel())
            ob.data.attributes['velocity'].data.foreach_set('vector', vel.astype(np.float32).ravel())
            ob.data.update()
        else:
            ob.data.position_data.foreach_set('vector', P.astype(np.float32).ravel())
            ob.data.attributes['velocity'].data.foreach_set('vector', vel.astype(np.float32).ravel())
            ob.data.update_tag()

    def apply(self, geo, geo_a, geo_b, dt, ring=4.0, cam=None):
        """geo at t, geo_a at t-dt, geo_b at t+dt -> positions + velocity (m/s)."""
        def vel(k):
            return (geo_b[k] - geo_a[k]) / (2 * dt)
        self._set(self.body, geo['body'], vel('body'))
        self._set(self.hp, geo['hp'], vel('hp'))
        for k in ('eyeL', 'eyeR'):
            self._set(self.eyes[k], geo[k], vel(k))
        d = self.dec
        fur = geo['fur'][::d][:self.nf]
        fv = ((geo_b['fur'] - geo_a['fur']) / (2 * dt))[::d][:self.nf]
        self._set(self.fur, fur.reshape(-1, 3), fv.reshape(-1, 3))
        self.ring_node.inputs['Emission Strength'].default_value = ring
        if cam is not None:
            # catchlight sits just above-left of the camera, aimed at the eyes
            eye_c = (geo['eyeL'].mean(0) + geo['eyeR'].mean(0)) / 2
            cpos = np.array(cam.matrix_world.translation)
            vdir = eye_c - cpos
            dist = np.linalg.norm(vdir)
            up = np.array([0, 0, 1.0])
            right = np.cross(vdir / dist, up)
            pos = eye_c - vdir / dist * min(0.35, dist * 0.5) + up * 0.06 + right * -0.05
            self.catch.location = Vector(pos)
            self.catch.rotation_euler = (Vector(eye_c) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()


def setup_render(res=(1280, 536), spp=40, mb=True, preview=False):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = spp
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02 if not preview else 0.1
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    sc.cycles.max_bounces = 6
    sc.cycles.diffuse_bounces = int(os.environ.get('DIFF', 2))
    sc.cycles.glossy_bounces = 3
    sc.cycles.transmission_bounces = 4
    sc.cycles.transparent_max_bounces = 6
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.fps = 24
    sc.render.use_motion_blur = mb
    sc.render.motion_blur_shutter = 0.5
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.view_settings.exposure = 0.0
    sc.render.threads_mode = 'FIXED'
    sc.render.threads = 4
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_depth = '16'
    sc.cycles.film_exposure = 1.0
