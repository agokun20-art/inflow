import bpy, numpy as np, time, math, sys
from mathutils import Vector
N = int(sys.argv[1]) if len(sys.argv) > 1 else 80000
RES = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (1280, 536)
SPP = int(sys.argv[4]) if len(sys.argv) > 4 else 48
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
rng = np.random.default_rng(1)
H, W = 0.30, 0.33          # Bo: 30 cm tall plush
a, b = W/2, H/2
# --- body surface samples (superellipsoid egg) ---
def surf(n):
    u = rng.normal(size=(n,3)); u /= np.linalg.norm(u,axis=1)[:,None]
    x,y,z = u.T            # z up
    e = np.where(z<0, 2.9, 2.15)
    f = lambda v,ee: np.sign(v)*np.abs(v)**(2/ee)
    R = np.stack([a*f(x,e)*(1+0.05*(-z)), a*f(y,e)*(1+0.05*(-z)), b + b*f(z,e)],1)
    nrm = np.stack([x/a, y/a, z/b],1); nrm/=np.linalg.norm(nrm,axis=1)[:,None]
    return R, nrm
# body mesh
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=64, radius=1)
body = bpy.context.object; body.name='Bo_body'
co = np.zeros(len(body.data.vertices)*3); body.data.vertices.foreach_get('co', co); co=co.reshape(-1,3)
x,y,z = co.T; e=np.where(z<0,2.9,2.15); f=lambda v,ee: np.sign(v)*np.abs(v)**(2/ee)
co = np.stack([a*f(x,e)*(1+0.05*(-z))*0.97, a*f(y,e)*(1+0.05*(-z))*0.97, b+b*f(z,e)*0.97],1)
body.data.vertices.foreach_set('co', co.ravel()); body.data.update()
bpy.ops.object.shade_smooth()
m = bpy.data.materials.new('fur_under'); m.use_nodes=True
m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.012,0.012,0.014,1)
m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=0.8
body.data.materials.append(m)
# --- fur curves ---
K = 6
roots, nrm = surf(N)
# eye exclusion zones (front = -y)
eyes = np.array([[-0.05,-0.15,0.175],[0.05,-0.15,0.175]])
dmin = np.min(np.linalg.norm(roots[:,None,:]-eyes[None],axis=2),axis=1)
keep = dmin > 0.022; roots, nrm = roots[keep], nrm[keep]; n=len(roots)
L = 0.017*rng.uniform(0.7,1.3,n)*np.clip((dmin[keep]-0.022)/0.03,0.35,1)
d = nrm + np.array([0,0,-0.35]) + rng.normal(0,0.35,(n,3)); d/=np.linalg.norm(d,axis=1)[:,None]
bend = rng.normal(0,0.3,(n,3))
t = np.linspace(0,1,K)
pts = roots[:,None,:] + (d[:,None,:]*t[None,:,None] + bend[:,None,:]*(t[None,:,None]**2)*0.4 + np.array([0,0,-0.25])*(t[None,:,None]**2))*L[:,None,None]
hc = bpy.data.hair_curves.new('Bo_fur')
hc.add_curves([K]*n)
hc.position_data.foreach_set('vector', pts.reshape(-1).astype(np.float32))
rad = np.tile(np.linspace(0.00016,0.00005,K),n).astype(np.float32)
if 'radius' not in hc.attributes: hc.attributes.new('radius','FLOAT','POINT')
hc.attributes['radius'].data.foreach_set('value', rad)
fur = bpy.data.objects.new('Bo_fur', hc); sc.collection.objects.link(fur)
hm = bpy.data.materials.new('fur'); hm.use_nodes=True; nt=hm.node_tree
for nd in list(nt.nodes):
    if nd.type=='BSDF_PRINCIPLED': nt.nodes.remove(nd)
SH = sys.argv[5] if len(sys.argv) > 5 else 'hair'
if SH == 'hair':
    hb = nt.nodes.new('ShaderNodeBsdfHairPrincipled'); hb.parametrization='COLOR'
    hb.inputs['Color'].default_value=(0.03,0.03,0.035,1); hb.inputs['Roughness'].default_value=0.42
else:
    hb = nt.nodes.new('ShaderNodeBsdfPrincipled'); hb.inputs['Base Color'].default_value=(0.03,0.03,0.035,1); hb.inputs['Roughness'].default_value=0.45
nt.links.new(hb.outputs[0], nt.nodes['Material Output'].inputs[0]); hc.materials.append(hm)
# eyes
em = bpy.data.materials.new('eye'); em.use_nodes=True; p=em.node_tree.nodes['Principled BSDF']
p.inputs['Base Color'].default_value=(0.005,0.005,0.006,1); p.inputs['Roughness'].default_value=0.04; p.inputs['Coat Weight'].default_value=1.0
for ex in eyes:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=ex); o=bpy.context.object
    o.scale=(0.012,0.008,0.018); bpy.ops.object.shade_smooth(); o.data.materials.append(em)
# floor + lights + world + camera
bpy.ops.mesh.primitive_plane_add(size=4); fl=bpy.context.object
fm=bpy.data.materials.new('floor'); fm.use_nodes=True; fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.35,0.2,0.1,1); fl.data.materials.append(fm)
def area(name, loc, rot, size, energy, col):
    l=bpy.data.lights.new(name,'AREA'); l.size=size; l.energy=energy; l.color=col
    o=bpy.data.objects.new(name,l); o.location=loc; o.rotation_euler=rot; sc.collection.objects.link(o)
area('key',(0.5,-0.5,0.6),(math.radians(55),0,math.radians(40)),0.3,40,(1.0,0.75,0.5))
area('rim',(-0.4,0.5,0.5),(math.radians(-55),0,math.radians(-140)),0.2,25,(0.55,0.65,1.0))
sc.world = bpy.data.worlds.new('w'); sc.world.use_nodes=True
sc.world.node_tree.nodes['Background'].inputs[0].default_value=(0.02,0.025,0.05,1)
cam = bpy.data.cameras.new('cam'); cam.lens=50; cam.dof.use_dof=True; cam.dof.aperture_fstop=2.8
co_=bpy.data.objects.new('cam',cam); sc.collection.objects.link(co_); sc.camera=co_
co_.location=(0,-1.1,0.2); co_.rotation_euler=(math.radians(88),0,0); cam.dof.focus_distance=0.95
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=SPP; sc.cycles.use_denoising=True
sc.cycles.use_adaptive_sampling=True; sc.cycles.max_bounces=6
sc.render.resolution_x, sc.render.resolution_y = RES; sc.render.resolution_percentage=100
sc.view_settings.view_transform='AgX'; sc.view_settings.look='AgX - Medium High Contrast'
sc.render.filepath=f'/home/user/inflow/adventures-of-bo/v2/out/bench_{SH}_{RES[0]}.png'
sc.render.threads_mode='FIXED'; sc.render.threads=4
t0=time.time(); bpy.ops.render.render(write_still=True); print(f'shader={SH} strands={n} res={RES} spp={SPP} render={time.time()-t0:.1f}s')
