from vedo import mesh

from mesh2grid import Mesh2Grid

# targetmesh.cutWithBox([-78, 308, -71, 65, -1000, 1000], invert=False)
targetCut = mesh.Mesh("mesh_ausgerichtet/mesh_ausgerichtet2.stl")

# targetCut.cutWithBox([-78, 308, -65, 63, -1000, 1000], invert=False)
# targetCut.cutWithCylinder([175, 382, 0], r=335, axis='z', invert=True)
# targetCut.cutWithCylinder([148, -318, 0], r=260, axis='z', invert=True)
# targetCut.cutWithBox([170, 320, 47, 75, -1000, 1000], invert=True)
# targetCut.cutWithBox([155, 310, -75, -58, -1000, 1000], invert=True)

targetCut.cutWithBox([-78, 308, -65, 63, -1000, 1000], invert=False)
targetCut.cutWithCylinder([175, 382, 0], r=335, axis='z', invert=True)
targetCut.cutWithCylinder([148, -316, 0], r=260, axis='z', invert=True)
targetCut.cutWithBox([170, 320, 45, 75, -1000, 1000], invert=True)
targetCut.cutWithBox([155, 310, -75, -56, -1000, 1000], invert=True)


# msh = mesh.Mesh("test/Blechhalter.stl")
#
# targetCut.cutWithMesh(msh)
targetCut.fillHoles()
targetCut.show(axes=1)

mesh2gridtarget = Mesh2Grid(targetCut, 3, 5)
mesh2gridtarget.creategrid(5, "test_gridpoints2")
