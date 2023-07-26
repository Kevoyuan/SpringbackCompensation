from vedo import *

# load target mesh
# targetCut = mesh.Mesh("data/targets/tool_mean_simulated_0_8_i3.stl")
# targetCut = mesh.Mesh("mesh_ausgerichtet/mesh_ausgerichtet1.stl")
targetCut = mesh.Mesh("data/targets/target_AF_bs.stl")

# targetCut.cutWithBox([-78, 308, -62, 59, -1000, 1000], invert=False)
# targetCut.cutWithCylinder([162,269,0], r=227, axis='z', invert=True)
# targetCut.cutWithBox([155, 308, 42, 60, -1000, 1000], invert=True)
# targetCut.cutWithCylinder([148,-277,0], r=224, axis='z', invert=True)
# targetCut.cutWithBox([155, 308, -70, -53, -1000, 1000], invert=True)

# targetCut.cutWithBox([-78, 308, -65, 60, -1000, 1000], invert=False)
# targetCut.cutWithCylinder([160, 255, 0], r=212, axis='z', invert=True)
# targetCut.cutWithBox([155, 308, 43, 60, -1000, 1000], invert=True)
# targetCut.cutWithCylinder([160, -277, 0], r=224, axis='z', invert=True)
# targetCut.cutWithBox([155, 308, -70, -53, -1000, 1000], invert=True)


# targetCut.cutWithBox([-78, 308, -65, 60, -1000, 1000], invert=False)
# targetCut.cutWithCylinder([158, 270, 0], r=227, axis='z', invert=True)
# targetCut.cutWithBox([160, 308, 43, 60, -1000, 1000], invert=True)
# targetCut.cutWithCylinder([160, -277, 0], r=224, axis='z', invert=True)
# targetCut.cutWithBox([155, 308, -70, -53, -1000, 1000], invert=True)

# targetgridpoints

# targetCut.cutWithBox([-78, 308, -62, 59, -1000, 1000], invert=False)
# targetCut.cutWithCylinder([160,377,0], r=330, axis='z', invert=True)
# targetCut.cutWithBox([155, 308, 46, 60, -1000, 1000], invert=True)
# targetCut.cutWithCylinder([148,-277,0], r=224, axis='z', invert=True)
# targetCut.cutWithBox([155, 308, -70, -53, -1000, 1000], invert=True)

targetCut.cutWithBox([-78, 308, -65, 63, -1000, 1000], invert=False)
targetCut.cutWithCylinder([170, 380, 0], r=330, axis='z', invert=True)
# targetCut.cutWithBox([155, 320, 50, 70, -1000, 1000], invert=True)
targetCut.cutWithCylinder([148, -282, 0], r=224, axis='z', invert=True)
# targetCut.cutWithBox([155, 310, -70, -58, -1000, 1000], invert=True)

targetCut.cutWithBox([170, 320, 50, 75, -1000, 1000], invert=True)

targetCut.cutWithBox([155, 310, -75, -58, -1000, 1000], invert=True)

msh = mesh.Mesh("test/Blechhalter.stl")

targetCut.cutWithMesh(msh)
targetCut.fillHoles()
targetCut.show(axes=1)

targetCut.write('test/testcut.stl')
# targetCut.write('data/targets/tool_mean_simulated_0_8_i1.stl')
