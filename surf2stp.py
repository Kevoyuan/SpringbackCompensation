from OCC.Core.Geom import Geom_BSplineSurface
from OCC.Core.TColgp import *
from OCC.Core.gp import *
from OCC.Core.TColStd import *
from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace


def Surf2Stp(controlpoints2d, knotvector_u, knotvector_v, degree_u, degree_v, filename):
    size_u = len(controlpoints2d)
    size_v = len(controlpoints2d[0])
    knotvectorset_u = sorted(set(knotvector_u))
    knotvectorset_v = sorted(set(knotvector_v))
    knotvectorcount_u = list()
    knotvectorcount_v = list()
    for i in knotvectorset_u:
        knotvectorcount_u.append(knotvector_u.count(i))
    for i in knotvectorset_v:
        knotvectorcount_v.append(knotvector_v.count(i))
    poles = TColgp_Array2OfPnt(1, size_u, 1, size_v)
    for i in range(size_u):
        for j in range(size_v):
            point = controlpoints2d[i][j]
            newpoint = gp_Pnt(point[0], point[1], point[2])
            poles.SetValue(i + 1, j + 1, newpoint)

    uknots = TColStd_Array1OfReal(1, len(knotvectorset_u))
    vknots = TColStd_Array1OfReal(1, len(knotvectorset_v))

    for i in range(len(knotvectorset_u)):
        uknots.SetValue(i + 1, knotvectorset_u[i])

    for i in range(len(knotvectorset_v)):
        vknots.SetValue(i + 1, knotvectorset_v[i])

    umult = TColStd_Array1OfInteger(1, len(knotvectorcount_u))
    vmult = TColStd_Array1OfInteger(1, len(knotvectorcount_v))

    for i in range(len(knotvectorcount_u)):
        umult.SetValue(i + 1, knotvectorcount_u[i])

    for i in range(len(knotvectorset_v)):
        vmult.SetValue(i + 1, knotvectorcount_v[i])

    surf = Geom_BSplineSurface(poles, uknots, vknots, umult, vmult,
                               degree_u, degree_v, False, False)

    writer = STEPControl_Writer()
    toposhape = BRepBuilderAPI_MakeFace(surf, 1e-6).Face()
    writer.Transfer(toposhape, STEPControl_AsIs)
    writer.Write(filename)
