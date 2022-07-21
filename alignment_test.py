import pymeshlab
import trimesh

import time
from vedo import *
from vedo.pyplot import plot

TARGETFILE = "data/targets/target_AF_bs.stl"
trimesh.tol.merge = 1e-7

sourceFile = "data/Simulation/i0/i3_median_08_1Export-Surfaces.stl"
exportFileName = "test/test_ausgerichtet.stl"

# load target mesh
targetVedo = Mesh(TARGETFILE)
targetVedo.cutWithBox([-78, 308, -71, 65, -1000, 1000], invert=False)
targetVedo.cutWithCylinder([170, 375, 0], r=330, axis="z", invert=True)
targetVedo.cutWithCylinder([148, -280, 0], r=224, axis="z", invert=True)
targetVedo.cutWithBox([170, 320, 44, 75, -1000, 1000], invert=True)
targetVedo.cutWithBox([155, 310, -75, -55, -1000, 1000], invert=True)

targetVedo.fillHoles()
targetVedoBack = targetVedo.clone()
targetVedoFront = targetVedo.clone()
targetVedoBack.cutWithBox([-78, 40, -71, 65, -50, 1000], invert=False)
targetVedoFront.cutWithBox([220, 290, -71, 65, -50, 1000], invert=False)
targetMesh = targetVedo.to_trimesh()
targetMeshBack = targetVedoBack.to_trimesh()
targetMeshFront = targetVedoFront.to_trimesh()
print("target mesh loaded")

start = time.time()


# alignedFileName = 'test/aligned_mesh.stl'

sourceMesh = Mesh(sourceFile)
sourceMesh.fillHoles()

sourceMesh.cutWithBox([-78, 308, -71, 65, -1000, 1000], invert=False)

vertices = sourceMesh.vertices()
numVertices = len(vertices)
halfPoint = numVertices // 2
upperPart = vertices[halfPoint:]

ms = pymeshlab.MeshSet()
pc = pymeshlab.Mesh(upperPart)
ms.add_mesh(pc)


ms.surface_reconstruction_ball_pivoting()
currentMesh = ms.current_mesh()

seperatedVertices = currentMesh.vertex_matrix()
seperatedFaces = currentMesh.face_matrix()

sourceTrimesh = trimesh.Trimesh(seperatedVertices, seperatedFaces)

# sourceTrimesh = sourceMesh.to_trimesh()
transformationMatrix, _ = trimesh.registration.mesh_other(
    sourceTrimesh, targetMesh, icp_final=500, samples=1000
)
sourceTrimesh.apply_transform(transformationMatrix)

sourceVedo = Mesh([sourceTrimesh.vertices, sourceTrimesh.faces])

sourceVedoBack = sourceVedo.cutWithBox([-78, 40, -71, 65, -50, 1000], invert=False)

sourceTrimeshBack = sourceVedoBack.to_trimesh()
transformationMatrix, _ = trimesh.registration.mesh_other(
    sourceTrimeshBack, targetMeshBack, icp_final=500, samples=1000
)
sourceTrimesh.apply_transform(transformationMatrix)
print("back mesh aligned")

sourceVedo = Mesh([sourceTrimesh.vertices, sourceTrimesh.faces])

sourceVedoFront = sourceVedo.cutWithBox([220, 290, -71, 65, -50, 1000], invert=False)
sourceTrimeshFront = sourceVedoFront.to_trimesh()
transformationMatrix, _ = trimesh.registration.mesh_other(
    sourceTrimeshFront, targetMeshFront, icp_final=500, samples=1000
)
sourceTrimesh.apply_transform(transformationMatrix)
print("front mesh aligned")

sourceTrimesh.export(exportFileName)

# alignedMesh = mesh.Mesh(exportFileName)
#
# alignedMesh.cutWithBox([-78, 308, -65, 60, -1000, 1000], invert=False)
# alignedMesh.cutWithCylinder([160, 255, 0], r=205, axis='z', invert=True)
# alignedMesh.cutWithBox([160, 308, 50, 60, -1000, 1000], invert=True)
#
# # alignedMesh.write(alignedFileName)
#
# print('alignment done')


end = time.time()
run_time = (end - start) / 60
print("\033[1;35m Time Total = {:.2f} min\033[0m".format(run_time))

mean_simulated_mesh = Mesh(exportFileName)


def slider(widget, event):
    cutx = widget.GetRepresentation().GetValue()
    pl.x(cutx)

    # Intersection
    targetSection = targetStl.intersectWith(pl).join(reset=True)
    simulatedSection = mean_simulated_mesh.intersectWith(pl).join(reset=True)

    # 1st render
    plt.remove(objs[0], at=0).add(pl, at=0, render=False)
    objs[0] = pl

    # simulatedSection render

    x = simulatedSection.points()[:, 1]
    y = simulatedSection.points()[:, 2]

    #  targetSection render
    x1 = targetSection.points()[:, 1]
    y1 = targetSection.points()[:, 2]

    # calculate normal distance form simulated result to target
    # ...

    # plot comparison for two sections
    ps2 = plot(
        x,
        y,
        "-",
        lw=2,
        xlim=(-80, 80),
        ylim=(-80, 10),
        xtitle="y",
        ytitle="z",
        title="Schnittfläche",
        lc="red5",
        pad=0.0,
    ).plot(x1, y1, "-", lc="green5")
    plt.remove(objs[1], at=1).add(ps2, at=1, resetcam=1)
    plt.remove(objs[2], at=1).add(lbox, at=1)
    objs[1] = ps2
    objs[2] = lbox


# load target mesh
targetStl = targetVedo
ax = Axes(targetStl)
txt = Text2D(font="Arial", bg="yellow")

objs = [None, None, None]  # empty placeholders
pl = Grid(resx=1, resy=1, sx=100, sy=200).triangulate()
pl.rotateY(90).z(-30)
pl.c("green").alpha(0.4).wireframe(0).lw(0)

# declare the instance of the class
plt = Plotter(shape=(1, 2), sharecam=0, interactive=0, size=[1600, 600], bg="white")
plt.addSlider2D(
    slider,
    -77,
    307,
    value=-77,
    pos="bottom-left",
    title="Schnittfläche in x-Richtung",
)

# add Legendbox
l1 = targetStl.clone().c("green")
l2 = mean_simulated_mesh.clone().c("red")

l1.legend("Referenzgeometrie")
l2.legend("Simuliertes Werkstück")

lbox = LegendBox([l1, l2], width=0.2)

mergeMesh = l1 + l2

# plt.show(target_mesh, mean_simulated_mesh, ax, at=0, interactive=0, azimuth=0, elevation=-30, roll=-80)
plt.show(mergeMesh, ax, at=0, interactive=0, azimuth=0, elevation=-30, roll=-80)
plt.show(interactive=1)
plt.screenshot(filename="screenshot.png")  # writer

plt.close()
