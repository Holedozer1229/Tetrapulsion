import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D

# ----------------------------
# 1. Core Functions
# ----------------------------
def tetrahedral_wave(X, Y, Z, kappa=2.5, harmonics=3):
    vertices = np.array([[1,1,1],[1,-1,-1],[-1,1,-1],[-1,-1,1]]) / np.sqrt(3)
    psi_total = np.zeros_like(X)
    for h in range(1, harmonics+1):
        psi_h = np.zeros_like(X)
        for v in vertices:
            psi_h += np.sin(h*kappa*(v[0]*X+v[1]*Y+v[2]*Z))
            psi_h += np.sin(h*kappa*(-v[0]*X-v[1]*Y-v[2]*Z))
        psi_total += psi_h / len(vertices)
    weights = np.sum([1.0/(h**1.5) for h in range(1, harmonics+1)])
    return psi_total / weights

def quantize_bits(psi, levels=8):
    quantized = np.digitize(psi, np.linspace(-1,1,levels)) - 1
    num_bits = int(np.ceil(np.log2(levels)))
    bit_planes = np.stack([(quantized >> i) & 1 for i in range(num_bits)], axis=-1)
    return bit_planes

def info_density(bit_planes):
    return np.sum(bit_planes, axis=-1) / bit_planes.shape[-1]

def platonic_metric(X, Y, Z, kappa=2.5):
    basis = np.array([[1,1,1],[1,-1,-1],[-1,1,-1],[-1,-1,1]]).T / np.sqrt(3)
    tetra_coords = np.stack([X*basis[0,i]+Y*basis[1,i]+Z*basis[2,i] for i in range(4)], axis=-1)
    edges = [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]
    faces = [(0,1,2),(0,1,3),(0,2,3),(1,2,3)]
    metric = np.zeros_like(X)
    for i,j in edges:
        metric += np.sin(kappa*(tetra_coords[...,i]-tetra_coords[...,j]))**2
    for f in faces:
        fc = np.mean(tetra_coords[...,f], axis=-1)
        metric += np.sin(kappa*fc)**2
    return metric / (len(edges)+len(faces))

def torsion_field(X, Y, Z, psi, info_metric, vortices):
    Vx = Vy = Vz = np.zeros_like(X)
    for v in vortices:
        cx,cy,cz = v["center"]
        ax,ay,az = v["axis"]
        phase = v["phase"]
        amp = v["amp"]
        freq = v["frequency"]
        bit_coupling = v["bit_coupling"]
        r2 = (X-cx)**2 + (Y-cy)**2 + (Z-cz)**2
        decay = np.exp(-r2*(1+bit_coupling*info_metric)*2.0)
        total_phase = 3*(X+Y+Z)+phase+psi*1.2+bit_coupling*np.pi*info_metric
        swirl = np.sin(total_phase)+0.6*np.sin(2*total_phase)*info_metric
        Vx += swirl*decay*ax*amp
        Vy += swirl*decay*ay*amp
        Vz += swirl*decay*az*amp
    return Vx, Vy, Vz

def craft_propagation(craft_pos, Vx, Vy, Vz, bit_planes, info_metric):
    N = Vx.shape[0]
    idx = np.clip(((craft_pos+2)/4*(N-1)).astype(int),1,N-2)
    bits_nb = bit_planes[idx[0]-1:idx[0]+2, idx[1]-1:idx[1]+2, idx[2]-1:idx[2]+2,0]
    info_nb = info_metric[idx[0]-1:idx[0]+2, idx[1]-1:idx[1]+2, idx[2]-1:idx[2]+2]
    bit_force = np.array([np.sum(bits_nb[:,1,1])-np.sum(bits_nb[:,0,1]),
                          np.sum(bits_nb[1,:,1])-np.sum(bits_nb[0,:,1]),
                          np.sum(bits_nb[1,1,:])-np.sum(bits_nb[0,1,:])])
    info_force = np.array([np.sum(info_nb[:,1,1])-np.sum(info_nb[:,0,1]),
                           np.sum(info_nb[1,:,1])-np.sum(info_nb[0,:,1]),
                           np.sum(info_nb[1,1,:])-np.sum(info_nb[0,1,:])])
    total_force = 0.02*bit_force + 0.03*info_force
    craft_pos += total_force
    return np.clip(craft_pos,-2,2)

# ----------------------------
# 2. Grid & Vortices
# ----------------------------
N = 30
x = np.linspace(-2,2,N)
y = np.linspace(-2,2,N)
z = np.linspace(-2,2,N)
X,Y,Z = np.meshgrid(x,y,z,indexing='ij')

craft_pos = np.array([0.0,0.0,0.0])
craft_trajectory = [craft_pos.copy()]

vortices = [
    {"center":[1,1,1], "axis":[1,1,1], "phase":0.0, "amp":1.0, "frequency":1.2, "bit_coupling":0.8},
    {"center":[-1,-1,1], "axis":[-1,-1,1], "phase":np.pi/2, "amp":0.9, "frequency":1.4, "bit_coupling":0.7},
]

# ----------------------------
# 3. 3D Visualization Setup
# ----------------------------
fig = plt.figure(figsize=(12,10))
ax3d = fig.add_subplot(111, projection='3d')
ax3d.set_xlim(-2,2)
ax3d.set_ylim(-2,2)
ax3d.set_zlim(-2,2)
ax3d.set_xlabel('X'); ax3d.set_ylabel('Y'); ax3d.set_zlabel('Z')
ax3d.set_title("3D Platonic Information Propulsion")

craft_dot, = ax3d.plot([],[],[],'ro', markersize=6)
traj_line, = ax3d.plot([],[],[],'r-', linewidth=2)
vortex_points = [ax3d.plot([v["center"][0]], [v["center"][1]], [v["center"][2]],
                           'bo' if i%2==0 else 'go', markersize=5)[0] for i,v in enumerate(vortices)]

# ----------------------------
# 4. Animation Function
# ----------------------------
def update(frame):
    global craft_pos, craft_trajectory
    t = frame/20*np.pi
    psi = tetrahedral_wave(X,Y,Z)
    bits = quantize_bits(psi)
    idens = info_density(bits)
    metric = platonic_metric(X,Y,Z)
    Vx,Vy,Vz = torsion_field(X,Y,Z,psi,metric,vortices)
    craft_pos = craft_propagation(craft_pos,Vx,Vy,Vz,bits,metric)
    craft_trajectory.append(craft_pos.copy())
    if len(craft_trajectory)>100: craft_trajectory.pop(0)
    traj = np.array(craft_trajectory)
    craft_dot.set_data(traj[-1,0],traj[-1,1])
    craft_dot.set_3d_properties(traj[-1,2])
    traj_line.set_data(traj[:,0],traj[:,1])
    traj_line.set_3d_properties(traj[:,2])
    return [craft_dot, traj_line]+vortex_points

# ----------------------------
# 5. Run Animation
# ----------------------------
ani = FuncAnimation(fig, update, frames=300, interval=50, blit=False)
plt.show()
