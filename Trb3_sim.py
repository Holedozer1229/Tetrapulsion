import numpy as np
import matplotlib.pyplot as plt
from skimage import measure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.animation import FuncAnimation

# --- Grid setup ---
N = 50
x = np.linspace(-2, 2, N)
y = np.linspace(-2, 2, N)
z = np.linspace(-2, 2, N)
X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
kappa = 2.5

# --- Tetrahedral wave Ψ_tetra ---
psi_tetra = 0.25*(np.sin(kappa*(X+Y+Z)) +
                  np.sin(kappa*(X-Y-Z)) +
                  np.sin(kappa*(-X+Y-Z)) +
                  np.sin(kappa*(-X-Y+Z)))

# --- Isosurface generation ---
verts, faces, _, _ = measure.marching_cubes(psi_tetra, level=0.0)
verts[:,0] = x[0] + verts[:,0]*(x[-1]-x[0])/(N-1)
verts[:,1] = y[0] + verts[:,1]*(y[-1]-y[0])/(N-1)
verts[:,2] = z[0] + verts[:,2]*(z[-1]-z[0])/(N-1)

# --- Torsion field ---
Vx = np.sin(kappa*(X+Y+Z))
Vy = np.sin(kappa*(X-Y-Z))
Vz = np.sin(kappa*(-X+Y-Z))
dx = x[1] - x[0]
Txy = np.gradient(Vy, dx, axis=0) - np.gradient(Vx, dx, axis=1)
Txz = np.gradient(Vz, dx, axis=0) - np.gradient(Vx, dx, axis=2)
Tyz = np.gradient(Vz, dx, axis=1) - np.gradient(Vy, dx, axis=2)
T_mag = np.sqrt(Txy**2 + Txz**2 + Tyz**2)
threshold = 0.6
bits = (T_mag > threshold).astype(int)

# --- Craft trajectory ---
craft_pos = np.array([0.0, 0.0, 0.0])
trajectory = [craft_pos.copy()]
torsion_along_traj = []
for _ in range(50):
    idx = np.clip(((craft_pos + 2) / 4 * (N-1)).astype(int), 1, N-2)
    neighborhood = bits[idx[0]-1:idx[0]+2, idx[1]-1:idx[1]+2, idx[2]-1:idx[2]+2]
    grad = np.array([
        np.sum(neighborhood[:,1,1])-np.sum(neighborhood[:,0,1]),
        np.sum(neighborhood[1,:,1])-np.sum(neighborhood[0,:,1]),
        np.sum(neighborhood[1,1,:])-np.sum(neighborhood[0,1,:])
    ])
    craft_pos += 0.05*grad
    craft_pos = np.clip(craft_pos, -2, 2)
    trajectory.append(craft_pos.copy())
    torsion_along_traj.append(T_mag[idx[0], idx[1], idx[2]])
trajectory = np.array(trajectory)
torsion_along_traj = np.array(torsion_along_traj)

# --- TRB-3 holonomy axes ---
axes = np.array([[1,1,1], [-1,-1,1], [1,-1,-1], [-1,1,-1]])
angles = [60.11, 69.95, 79.78, 0.0]  # degrees

# --- Combined figure setup ---
fig = plt.figure(figsize=(14,10))
ax1 = fig.add_subplot(221, projection='3d')
ax2 = fig.add_subplot(222, projection='3d')
ax3 = fig.add_subplot(223, projection='3d')
ax4 = fig.add_subplot(224)
ax4.axis('off'); ax4.text(0.5,0.5,"Figure Captions / Notes", ha='center', va='center', fontsize=12)

# --- Subplot 1: Tetrahedral wave ---
mesh = Poly3DCollection(verts[faces], alpha=0.7, facecolor='cyan')
ax1.add_collection3d(mesh)
ax1.set_xlim(-2,2); ax1.set_ylim(-2,2); ax1.set_zlim(-2,2)
ax1.set_title('Tetrahedral Wave Ψ_tetra')

# --- Subplot 3: TRB-3 axes ---
for i, (axis, angle) in enumerate(zip(axes, angles)):
    ax3.quiver(0,0,0, axis[0], axis[1], axis[2], length=1.0,
               color=plt.cm.viridis(i/4), linewidth=2, arrow_length_ratio=0.1)
    ax3.text(axis[0], axis[1], axis[2], f'{angle}°', color='black')
ax3.set_xlim(-1.5,1.5); ax3.set_ylim(-1.5,1.5); ax3.set_zlim(-1.5,1.5)
ax3.set_title('TRB-3 Holonomy Axes & Sequence')

# --- Subplot 2: animated craft trajectory ---
traj_line, = ax2.plot([], [], [], lw=3)
sc = ax2.scatter([], [], [], c=[], cmap='plasma', s=50)
ax2.set_xlim(-2,2); ax2.set_ylim(-2,2); ax2.set_zlim(-2,2)
ax2.set_title('Craft Trajectory Colored by Torsion')

def init():
    traj_line.set_data([], [])
    traj_line.set_3d_properties([])
    sc._offsets3d = ([], [], [])
    return traj_line, sc

def update(frame):
    traj_line.set_data(trajectory[:frame,0], trajectory[:frame,1])
    traj_line.set_3d_properties(trajectory[:frame,2])
    sc._offsets3d = (trajectory[:frame,0], trajectory[:frame,1], trajectory[:frame,2])
    sc.set_array(torsion_along_traj[:frame])
    ax2.view_init(elev=30, azim=frame*3)  # rotating view
    return traj_line, sc

anim = FuncAnimation(fig, update, frames=len(trajectory), init_func=init,
                     interval=150, blit=False, repeat=True)

plt.tight_layout()
plt.show()
