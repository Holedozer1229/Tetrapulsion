import numpy as np
import matplotlib.pyplot as plt
from skimage import measure  # for marching cubes
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# Grid definition
N = 50
x = np.linspace(-2, 2, N)
y = np.linspace(-2, 2, N)
z = np.linspace(-2, 2, N)
X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
kappa = 2.5

# Tetrahedral wavefunction
psi_tetra = 0.25*(np.sin(kappa*(X+Y+Z)) +
                  np.sin(kappa*(X-Y-Z)) +
                  np.sin(kappa*(-X+Y-Z)) +
                  np.sin(kappa*(-X-Y+Z)))

# Marching cubes
verts, faces, _, _ = measure.marching_cubes(psi_tetra, level=0.0)

# Convert voxel coordinates to physical coordinates
verts[:, 0] = x[0] + verts[:, 0]*(x[-1]-x[0])/(N-1)
verts[:, 1] = y[0] + verts[:, 1]*(y[-1]-y[0])/(N-1)
verts[:, 2] = z[0] + verts[:, 2]*(z[-1]-z[0])/(N-1)

# Plot isosurface
fig = plt.figure(figsize=(8,6))
ax = fig.add_subplot(111, projection='3d')
mesh = Poly3DCollection(verts[faces], alpha=0.7)
mesh.set_facecolor('cyan')
ax.add_collection3d(mesh)
ax.set_xlim(-2,2); ax.set_ylim(-2,2); ax.set_zlim(-2,2)
ax.set_title('Tetrahedral Wave Ψ_tetra Isosurface')
plt.tight_layout()
plt.show()
