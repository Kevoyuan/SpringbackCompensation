from vedo import *
from vedo.pyplot import plot

# load aligned mesh
mean_simulated_mesh = Mesh('mesh_ausgerichtet/mesh_ausgerichtet_z-40.stl')


def slider(widget, event):
    cutx = widget.GetRepresentation().GetValue()
    pl.x(cutx)

    # Intersection
    targetSection = target_mesh.intersectWith(pl).join(reset=True)
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
    ps2 = plot(x, y, '-',
               lw=2,
               xlim=(-80, 80),
               ylim=(-80, 10),
               xtitle='y',
               ytitle='z',
               title='Cutting Section',
               lc='red5',
               pad=0.0).plot(x1, y1, '-', lc='green5')
    plt.remove(objs[1], at=1).add(ps2, at=1, resetcam=1)
    plt.remove(objs[2], at=1).add(lbox, at=1)
    objs[1] = ps2
    objs[2] = lbox


# load target mesh
targetStl = Mesh("data/targets/target_AF_bs.stl")
targetStl_cut = targetStl.clone()

target_mesh = targetStl_cut.clone()
ax = Axes(target_mesh)
txt = Text2D(font='Calco', bg='yellow')

objs = [None, None, None]  # empty placeholders
pl = Grid(resx=1, resy=1, sx=100, sy=200).triangulate()
pl.rotateY(90).z(-30)
pl.c('green').alpha(0.4).wireframe(0).lw(0)

# declare the instance of the class
plt = Plotter(shape=(1, 2), sharecam=0, interactive=0, size=[1600, 600], bg="white")
plt.addSlider2D(slider,
                -77, 307,
                value=-77,
                pos="bottom-left",
                title="section in x direction",
                )

# add Legendbox
l1 = target_mesh.clone().c('green')
l2 = mean_simulated_mesh.clone().c('red')

l1.legend('target')
l2.legend('simulation')

lbox = LegendBox([l1, l2], width=0.2)

mergeMesh = l1 + l2

# plt.show(target_mesh, mean_simulated_mesh, ax, at=0, interactive=0, azimuth=0, elevation=-30, roll=-80)
plt.show(mergeMesh, ax, at=0, interactive=0, azimuth=0, elevation=-30, roll=-80)
plt.show(interactive=1)
plt.close()
