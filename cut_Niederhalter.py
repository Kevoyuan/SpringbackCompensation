from vedo import *

Blechhalter = Mesh("test/Blechhalter.stl").c('yellow')

targetCut = Mesh("mesh_ausgerichtet/mesh_ausgerichtet1.stl").c('red')


mergeM = targetCut + Blechhalter

# BlechhalterCut.show(axes=1)
# mergeM.show(axes=1)


ax = Axes(Blechhalter)
plt = Plotter(shape=[1, 3], interactive=False, size=[1600, 600])
plt.show(Blechhalter, ax, at=2, interactive=False)
plt.show(targetCut, ax, at=0, interactive=0)
plt.show(mergeM, ax, at=1, interactive=1)
plt.close()

# BlechhalterCut.write('test/BlechhalterCut.stl')
