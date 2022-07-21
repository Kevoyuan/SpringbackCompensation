from vedo import *
import pymeshlab
import trimesh

# load target mesh
# targetCut = mesh.Mesh("data/Simulation/i0/i0_2Export-Surfaces.stl")
targetCut = Mesh('test/test_ausgerichtet.stl')
# targetCut = mesh.Mesh("data/targets/target_AF_bs.stl")

# vertices = targetCut.vertices()
# numVertices = len(vertices)
# halfPoint = numVertices // 2
# upperPart = vertices[halfPoint:]

# ms = pymeshlab.MeshSet()
# pc = pymeshlab.Mesh(upperPart)
# ms.add_mesh(pc)
# ms.surface_reconstruction_ball_pivoting()
# currentMesh = ms.current_mesh()

# seperatedVertices = currentMesh.vertex_matrix()
# seperatedFaces = currentMesh.face_matrix()
# sourceTrimesh = trimesh.Trimesh(seperatedVertices, seperatedFaces)
# sourceTrimesh.export("test/testcut.stl")

# targetCut = Mesh("test/testcut.stl")

targetCut.cutWithBox([-76, 307, -65, 63, -1000, 1000], invert=False)
targetCut.cutWithCylinder([175, 382, 0], r=335, axis='z', invert=True)
targetCut.cutWithCylinder([148, -316, 0], r=260, axis='z', invert=True)
targetCut.cutWithBox([170, 320, 45, 75, -1000, 1000], invert=True)
targetCut.cutWithBox([155, 310, -75, -56, -1000, 1000], invert=True)

#
# msh = Mesh("test/Blechhalter.stl").c('red')
# msh.cutWithBox([170, 320, 35, 75, -1000, -75], invert=True)
# # #
# targetCut.cutWithMesh(msh,invert=False)
targetCut.fillHoles()

# mergemesh = targetCut+msh
# mergemesh.show(axes=1)
targetCut.show(axes=1)
# msh.show(axes=1)
# mergemesh.write('test/testcut.stl')
targetCut.write('test\testcut.stl')
