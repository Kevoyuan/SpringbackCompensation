from vedo import *
from vedo.pyplot import plot

# settings.useDepthPeeling = True

# settings.immediateRendering = False


def slider(widget, event):
    cutx = widget.GetRepresentation().GetValue()
    pl.x(cutx)

    # Intersection
    targetSection = target_mesh.intersect_with(pl).join(reset=True)
    simulatedSection = mean_simulated_mesh.intersect_with(pl).join(reset=True)
    # targetSection.lineWidth(1).c('red')

    # 1st render
    plt.remove(pl, at=0).add(pl, at=0)

    # objs[0] = pl

    # 2nd render
    txt.text(f'cutting x = : {cutx} mm')
    x = simulatedSection.points()[:, 1]
    y = simulatedSection.points()[:, 2]

    #  3rd render
    x1 = targetSection.points()[:, 1]
    y1 = targetSection.points()[:, 2]

    # calculate normal distance form simulated result to target
    # ...

    # plot comparison for two sections
    ps2 = plot(x, y,
               '-',
               lw=2,
               xlim=(-80, 80),
               ylim=(-80, 10),
               xtitle='y',
               ytitle='z',
               title='Cutting Section',
               lc='red'
               ).plot(x1, y1, '-', lc='green')

    plt.remove(objs[1], at=1).add(ps2, at=1, resetcam=1)
    plt.remove(objs[2], at=1).add(lbox, at=1)
    objs[1] = ps2
    objs[2] = lbox


# load target mesh
target_mesh = Mesh('data/targets/target_AF_bs.stl')
target_mesh.cut_with_box([-78, 308, -71, 65, -1000, 1000]).bc("silver")
ax = Axes(target_mesh)
txt = Text2D(font='Calco', bg='yellow')

# load mean simulated mesh
mean_simulated_mesh = Mesh('test/meanSimulatedMesh.stl').bc('yellow')

# load tool mesh
# alignedMesh = Mesh("data/targets/compensatedsurface_mean_simulated_0_8_i0.stp")

objs = [None, None, None]  # empty placeholders
pl = Grid(s=(100, 200), res=(1, 1)).triangulate()
pl.rotate_y(90).z(-30)
pl.c('green').alpha(0.4).wireframe(0).lw(0)

# declare the instance of the class
plt = Plotter(shape=(1, 2), sharecam=0, interactive=0, size=[1200, 500], bg="white")
plt.add_slider(slider,
                -77, 307,
                value=-77,
                pos="bottom-left",
                title="cut in x direction",
                )

l1 = target_mesh.clone().c('green')
l2 = mean_simulated_mesh.clone().c('red')

l1.legend('target')
l2.legend('simulated')
lbox = LegendBox([l1, l2], width=0.2)

plt.show(target_mesh, mean_simulated_mesh, ax, at=0, interactive=0, azimuth=0, elevation=-30, roll=-80)

plt.show(txt, at=1, interactive=1)
plt.close()
