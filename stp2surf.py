from steputils import p21
from geomdl import BSpline
from geomdl.visualization import VisMPL
from geomdl.visualization import VisVTK
from geomdl import multi
from geomdl import control_points


class Stp2Surf:
    def __init__(self, file):
        self.filename = file
        try:
            self.stepfile = p21.readfile(self.filename)
        except IOError as e:
            print(str(e))
        except SyntaxError as e:
            print(str(e))

        self.datasection = self.stepfile.data[0]
        [self.curvedegrees, self.curvectrlpts, self.curveknotvectors] = self.bsplinecurves(self.datasection)
        [self.surfdegrees, self.surfmanagers, self.surfknotvectors, self.sizevector] = self.bsplinesurfaces(
            self.datasection)

        # create list of curve objects
        self.curves = []
        for i in range(len(self.curvedegrees)):
            self.curves.append(BSpline.Curve())
            self.curves[i].degree = self.curvedegrees[i]
            self.curves[i].ctrlpts = self.curvectrlpts[i]
            self.curves[i].knotvector = self.curveknotvectors[i]

        # create list of surface objects
        self.surfaces = []
        for i in range(len(self.surfdegrees)):
            self.surfaces.append(BSpline.Surface())
            self.surfaces[i].degree_u = self.surfdegrees[i][0]
            self.surfaces[i].degree_v = self.surfdegrees[i][1]
            self.surfaces[i].ctrlpts_size_u = self.sizevector[i][0]
            self.surfaces[i].ctrlpts_size_v = self.sizevector[i][1]
            self.surfaces[i].ctrlpts = self.surfmanagers[i].ctrlpts
            self.surfaces[i].knotvector_u = self.surfknotvectors[i][0]
            self.surfaces[i].knotvector_v = self.surfknotvectors[i][1]

    def bsplinecurves(self, datasection):
        # get degrees, control points and knot vectors for each b-spline curve defined in the step file
        datasectionlen = datasection.__len__()
        it = iter(datasection.__iter__())

        degrees = []
        ctrlpts = []
        knotvectors = []

        for i in range(datasectionlen):
            instance = next(it)
            if p21.is_simple_entity_instance(instance):
                entity = instance.entity
                if entity.name == 'B_SPLINE_CURVE_WITH_KNOTS':
                    entityparams = entity.params

                    degree = entityparams[1]
                    controlpointrefs = entityparams[2]
                    numberofknots = entityparams[6]
                    knots = entityparams[7]

                    degrees.append(degree)

                    controlpointvector = []
                    for ref in controlpointrefs:
                        controlpointvector.append(datasection.get(ref).entity.params[1])
                    ctrlpts.append(controlpointvector)

                    knotvector = []
                    for j in range(len(numberofknots)):
                        knotvector.extend([knots[j] for x in range(numberofknots[j])])
                    knotvectors.append(knotvector)
        return degrees, ctrlpts, knotvectors

    def bsplinesurfaces(self, datasection):
        # get degrees, surface manager objects, knot vectors and number of control points for each b-spline surface
        # defined in the step file

        datasectionlen = datasection.__len__()
        it = iter(datasection.__iter__())

        degrees = []
        surfacemanagers = []
        knotvectors = []
        numpoints = []

        for i in range(datasectionlen):
            instance = next(it)
            if p21.is_simple_entity_instance(instance):
                entity = instance.entity
                if entity.name == 'B_SPLINE_SURFACE_WITH_KNOTS':
                    entityparams = entity.params

                    degrees.append([entityparams[1], entityparams[2]])

                    controlpointrefs = entityparams[3]
                    size_u = len(controlpointrefs)
                    size_v = len(controlpointrefs[0])
                    numpoints.append([size_u, size_v])

                    numberofknots_u = entityparams[8]
                    numberofknots_v = entityparams[9]
                    knots_u = entityparams[10]
                    knots_v = entityparams[11]

                    points = control_points.SurfaceManager(size_u, size_v)
                    for u in range(size_u):
                        for v in range(size_v):
                            ref = controlpointrefs[u][v]
                            pt = datasection.get(ref).entity.params[1]
                            points.set_ctrlpt(pt, u, v)
                    surfacemanagers.append(points)

                    knotvector_u = []
                    for j in range(len(numberofknots_u)):
                        knotvector_u.extend([knots_u[j] for x in range(numberofknots_u[j])])

                    knotvector_v = []
                    for j in range(len(numberofknots_v)):
                        knotvector_v.extend([knots_v[j] for x in range(numberofknots_v[j])])

                    knotvector = [knotvector_u, knotvector_v]
                    knotvectors.append(knotvector)

        return degrees, surfacemanagers, knotvectors, numpoints

    def renderallcurves(self, delta):
        # put curves into a curve container (Not needed if surfaces will be treated separately. If this is the case,
        # curves should be rendered individually.)
        mcrv = multi.CurveContainer()
        mcrv.add(self.curves)
        mcrv.delta = delta
        mcrv.vis = VisMPL.VisCurve3D()
        mcrv.render(evalcolor='#428df5')

    def renderallsurfaces(self, delta):
        # put surfaces into a curve container (Not needed if surfaces will be treated separately. If this is the case,
        # surfaces should be rendered individually.)
        msurf = multi.SurfaceContainer()
        msurf.add(self.surfaces)
        msurf.delta = delta
        msurf.vis = VisVTK.VisSurface()
        msurf.render(evalcolor='#ff6200')

    def getevalpoints(self, bsplinetype, index, delta):
        if bsplinetype == 'curve':
            try:
                self.curves[index].delta = delta
                return self.curves[index].evalpts
            except IndexError:
                print("This curve does not exist")

        elif bsplinetype == 'surface':
            try:
                self.surfaces[index].delta = delta
                return self.surfaces[index].evalpts
            except IndexError:
                print("This surface does not exist")

    def getsurfsamplesize(self, index, delta):
        self.surfaces[index].delta = delta
        u = self.surfaces[index].sample_size_u
        v = self.surfaces[index].sample_size_v
        return [u, v]
