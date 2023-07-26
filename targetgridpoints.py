from vedo import Mesh
from mesh2grid import Mesh2Grid

targetCut = Mesh("data/targets/target_AF_bs.stl")

targetCut.cut_with_box([-76, 307, -65, 63, -1000, 1000], invert=False)
targetCut.cut_with_cylinder([175, 382, 0], r=335, axis='z', invert=True)
targetCut.cut_with_cylinder([148, -318, 0], r=260, axis='z', invert=True)
targetCut.cut_with_box([170, 320, 47, 75, -1000, 1000], invert=True)
targetCut.cut_with_box([155, 310, -75, -58, -1000, 1000], invert=True)

# msh = Mesh("test/Blechhalter.stl")
# targetCut.cutWithMesh(msh)
targetCut.fill_holes()  # Changed from fillHoles() to fill_holes()

mesh2gridtarget = Mesh2Grid(targetCut, 3, 5)
mesh2gridtarget.creategrid(5, "targetgridpoints")
