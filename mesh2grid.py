import numpy as np
import trimesh
from geomdl import fitting
import time
from collections import defaultdict
from pathlib import Path


class Mesh2Grid:
    def __init__(self, alignedmesh, numdivisionsv, numdivisionsu):
        self.alignedmesh = alignedmesh
        self.alignedmeshvertices = alignedmesh.vertices()
        self.alignedmeshfaces = alignedmesh.faces()
        self.alignedtrimesh = trimesh.Trimesh(self.alignedmeshvertices, self.alignedmeshfaces, process=False)
        self.cellnormals = alignedmesh.normals(cells=True)
        self.edges = self.alignedtrimesh.edges_unique
        self.graph = defaultdict(list)
        for edge in self.edges:
            self.addedge(edge[0], edge[1])

        # grid initialization
        point1 = alignedmesh.closestPoint([-100, -100, -100], 1, returnPointId=True)
        point2 = alignedmesh.closestPoint([340, -100, -100], 1, returnPointId=True)
        point3 = alignedmesh.closestPoint([-100, 100, -100], 1, returnPointId=True)
        point4 = alignedmesh.closestPoint([340, 100, -100], 1, returnPointId=True)
        self.bordergeodesic1 = alignedmesh.geodesic(point1, point2)
        self.bordergeodesic2 = alignedmesh.geodesic(point3, point4)
        self.bordergeodesic3 = alignedmesh.geodesic(point1, point3)
        self.bordergeodesic4 = alignedmesh.geodesic(point2, point4)

        border1points = self.bordergeodesic1.vertices()  # u
        border2points = self.bordergeodesic2.vertices()  # u
        border3points = self.bordergeodesic3.vertices()  # v
        border4points = self.bordergeodesic4.vertices()  # v
        self.borderbspline1 = fitting.approximate_curve(border1points.tolist(), 3, ctrlpts_size=40)
        self.borderbspline2 = fitting.approximate_curve(border2points.tolist(), 3, ctrlpts_size=40)
        self.borderbspline3 = fitting.approximate_curve(border3points.tolist(), 3, ctrlpts_size=100)
        self.borderbspline4 = fitting.approximate_curve(border4points.tolist(), 3, ctrlpts_size=100)
        self.borderbspline1.delta = 0.01
        self.borderbspline2.delta = 0.01
        self.borderbspline3.delta = 0.01
        self.borderbspline4.delta = 0.01

        numsamplesu = numdivisionsu + 1
        numsamplesv = numdivisionsv + 1
        self.borderbspline1.sample_size = numsamplesu
        self.borderbspline2.sample_size = numsamplesu
        self.borderbspline3.sample_size = numsamplesv
        self.borderbspline4.sample_size = numsamplesv

        borderfacepoints1, _, ids1 = trimesh.proximity.closest_point(self.alignedtrimesh, self.borderbspline1.evalpts)
        borderfacepoints2, _, ids2 = trimesh.proximity.closest_point(self.alignedtrimesh, self.borderbspline2.evalpts)
        borderfacepoints3, _, ids3 = trimesh.proximity.closest_point(self.alignedtrimesh, self.borderbspline3.evalpts)
        borderfacepoints4, _, ids4 = trimesh.proximity.closest_point(self.alignedtrimesh, self.borderbspline4.evalpts)

        initisocurvesu = []
        initisocurvesv = []
        borderfacepointsmatrix = np.zeros((numsamplesv, numsamplesu, 3))  # contains face points on border as a matrix

        for i in range(1, numsamplesu - 1):
            isocurve = self.alignedmesh.geodesic(
                self.alignedmesh.closestPoint(borderfacepoints1[i], 1, returnPointId=True),
                self.alignedmesh.closestPoint(borderfacepoints2[i], 1, returnPointId=True))
            initisocurvesv.append(isocurve)
            borderfacepointsmatrix[numsamplesv - 1][numsamplesu - 1 - i] = borderfacepoints1[i]
            borderfacepointsmatrix[0][numsamplesu - 1 - i] = borderfacepoints2[i]

        for i in range(1, numsamplesv - 1):
            isocurve = self.alignedmesh.geodesic(
                self.alignedmesh.closestPoint(borderfacepoints3[i], 1, returnPointId=True),
                self.alignedmesh.closestPoint(borderfacepoints4[i], 1, returnPointId=True))
            initisocurvesu.append(isocurve)
            borderfacepointsmatrix[i][0] = borderfacepoints3[i]
            borderfacepointsmatrix[i][numsamplesu - 1] = borderfacepoints4[i]

        borderfacepointsmatrix[0][0] = borderfacepoints3[0]
        borderfacepointsmatrix[0][numsamplesu - 1] = borderfacepoints4[0]
        borderfacepointsmatrix[numsamplesv - 1][0] = borderfacepoints3[numsamplesv - 1]
        borderfacepointsmatrix[numsamplesv - 1][numsamplesu - 1] = borderfacepoints4[numsamplesv - 1]

        facepointsmatrix = np.zeros((numsamplesv, numsamplesu, 3))  # contains face points not on border as a matrix
        facepoints = np.empty((0, 3))  # contains face points not on border as a list
        for i in range(len(initisocurvesv)):
            for j in range(len(initisocurvesu)):
                intersection = self.findintersections(initisocurvesv[i].vertices(), initisocurvesu[j].vertices())
                facepoints = np.append(facepoints, [intersection[0]], axis=0)
                facepointsmatrix[j + 1][numsamplesv - i] = intersection[0]

        self.springmeshmatrix = facepointsmatrix + borderfacepointsmatrix  # contains all face points as a matrix
        print("grid initialized")

    def addedge(self, u, v):
        self.graph[u].append(v)
        self.graph[v].append(u)

    def BFS(self, src, dest, pred):
        queue = []
        v = max(self.graph) + 1
        visited = [False for i in range(v)]

        for i in range(v):
            pred[i] = -1

        visited[src] = True
        queue.append(src)

        while len(queue) != 0:
            u = queue[0]
            queue.pop(0)
            for i in range(len(self.graph[u])):

                if not visited[self.graph[u][i]]:
                    visited[self.graph[u][i]] = True
                    pred[self.graph[u][i]] = u
                    queue.append(self.graph[u][i])

                    if self.graph[u][i] == dest:
                        return True
        return False

    def calculatepath(self, s, dest):
        # predecessor[i] array stores predecessor of
        # i and distance array stores distance of i
        # from s
        v = max(self.graph) + 1
        pred = [0 for i in range(v)]

        if not self.BFS(s, dest, pred):
            print("Given source and destination are not connected")

        # vector path stores the shortest path
        path = []
        crawl = dest
        path.append(crawl)

        while pred[crawl] != -1:
            path.append(pred[crawl])
            crawl = pred[crawl]
        return path

    def findgeomidpoint(self, facepoint1, facepoint2):
        vertex1id = self.alignedmesh.closestPoint(facepoint1, 1, returnPointId=True)
        vertex2id = self.alignedmesh.closestPoint(facepoint2, 1, returnPointId=True)
        path = self.calculatepath(vertex1id, vertex2id)
        pathlen = len(path)
        halfpoint = int(pathlen / 2)
        geomidpointid = path[halfpoint]
        geomidpoint = self.alignedtrimesh.vertices[geomidpointid]
        return geomidpoint

    def findintersections(self, a, b):
        nrows, ncols = a.shape
        dtype = {'names': ['f{}'.format(i) for i in range(ncols)],
                 'formats': ncols * [a.dtype]}
        c = np.intersect1d(a.view(dtype), b.view(dtype))
        c = c.view(a.dtype).reshape(-1, ncols)
        return c

    def forces(self, point, u, d, l, r):
        pup = u - point
        pdown = d - point
        pleft = l - point
        pright = r - point
        verticalvec = [pup, pdown]
        horizontalvec = [pleft, pright]
        normu = np.linalg.norm(pup)
        normd = np.linalg.norm(pdown)
        norml = np.linalg.norm(pleft)
        normr = np.linalg.norm(pright)
        vertnorms = [normu, normd]
        hornorms = [norml, normr]

        vertrelaxdirindex = vertnorms.index(max(vertnorms))
        vertrelaxdir = verticalvec[vertrelaxdirindex] / vertnorms[vertrelaxdirindex]
        vertrelaxmag = np.abs(normu - normd)
        vertrelax = vertrelaxmag * vertrelaxdir

        horrelaxdirindex = hornorms.index(max(hornorms))
        horrelaxdir = horizontalvec[horrelaxdirindex] / hornorms[horrelaxdirindex]
        horrelaxmag = np.abs(norml - normr)
        horrelax = horrelaxmag * horrelaxdir

        arcresultant = vertrelax + horrelax
        fairresultant = pup + pdown + pleft + pright
        return arcresultant, fairresultant

    def relaxpoint(self, point, arcforce, fairforce, alpha, beta):
        newpoint = point
        force = alpha * fairforce + beta * arcforce
        _, _, cellid = trimesh.proximity.closest_point(self.alignedtrimesh, [newpoint])
        cellnormal = self.cellnormals[cellid][0]
        movevector = force - np.dot(force, cellnormal) * cellnormal
        newpoint = newpoint + movevector
        projectednewpoint, _, _ = trimesh.proximity.closest_point(self.alignedtrimesh, [newpoint])
        return projectednewpoint

    def relaxallpoints(self, numiterations):
        numpointsv = self.springmeshmatrix.shape[0]
        numpointsu = self.springmeshmatrix.shape[1]
        for alpha, beta in zip(np.linspace(0, 1, numiterations), np.linspace(1, 0, numiterations)):
            for i in range(1, numpointsv - 1):
                for j in range(1, numpointsu - 1):
                    currentpoint = self.springmeshmatrix[i][j]
                    u = self.springmeshmatrix[i - 1][j]
                    d = self.springmeshmatrix[i + 1][j]
                    l = self.springmeshmatrix[i][j - 1]
                    r = self.springmeshmatrix[i][j + 1]
                    arcforce, fairforce = self.forces(currentpoint, u, d, l, r)
                    reducedarcforce = arcforce / numiterations
                    reducedfairforce = fairforce / numiterations
                    relaxedpoint = self.relaxpoint(currentpoint, reducedarcforce, reducedfairforce, alpha, beta)
                    self.springmeshmatrix[i][j] = relaxedpoint

    def subdivisionforces(self, pointa, pointb, newpoint):
        p1 = pointa - newpoint
        normp1 = np.linalg.norm(p1)
        p2 = pointb - newpoint
        normp2 = np.linalg.norm(p2)
        vec = [p1, p2]
        norms = [normp1, normp2]
        relaxdirindex = norms.index(max(norms))
        arcforcedir = vec[relaxdirindex] / norms[relaxdirindex]
        arcforcemag = np.abs(normp1 - normp2)
        arcforce = arcforcedir * arcforcemag
        fairforce = p1 + p2
        return arcforce, fairforce

    def subdividespringmesh(self):
        numrows = self.springmeshmatrix.shape[0]
        numcols = self.springmeshmatrix.shape[1]
        newnumrows = 2 * numrows - 1
        newnumcols = 2 * numcols - 1
        newspringmesh = np.zeros((newnumrows, newnumcols, 3))
        self.borderbspline1.sample_size = newnumcols
        self.borderbspline2.sample_size = newnumcols
        self.borderbspline3.sample_size = newnumrows
        self.borderbspline4.sample_size = newnumrows

        borderfacepoints1, _, _ = trimesh.proximity.closest_point(self.alignedtrimesh, self.borderbspline1.evalpts)
        borderfacepoints2, _, _ = trimesh.proximity.closest_point(self.alignedtrimesh, self.borderbspline2.evalpts)
        borderfacepoints3, _, _ = trimesh.proximity.closest_point(self.alignedtrimesh, self.borderbspline3.evalpts)
        borderfacepoints4, _, _ = trimesh.proximity.closest_point(self.alignedtrimesh, self.borderbspline4.evalpts)

        borderfacepointsmatrix = np.zeros((newnumrows, newnumcols, 3))  # contains face points on border as a matrix

        for i in range(1, newnumcols - 1):
            borderfacepointsmatrix[newnumrows - 1][newnumcols - 1 - i] = borderfacepoints1[i]
            borderfacepointsmatrix[0][newnumcols - 1 - i] = borderfacepoints2[i]

        for i in range(0, newnumrows):
            borderfacepointsmatrix[i][0] = borderfacepoints3[i]
            borderfacepointsmatrix[i][newnumcols - 1] = borderfacepoints4[i]

        newspringmesh = newspringmesh + borderfacepointsmatrix

        for i in range(1, numrows - 1):
            for j in range(1, numcols - 1):
                newspringmesh[2 * i][2 * j] = self.springmeshmatrix[i, j]

        for i in range(0, newnumrows - 2, 2):
            for j in range(0, newnumcols - 2, 2):
                if i == 0 and j == 0:
                    continue
                elif j == 0:
                    pointa = newspringmesh[i][j]
                    pointb = newspringmesh[i][j + 2]
                    newpoint = self.findgeomidpoint(pointa, pointb)
                    af, ff = self.subdivisionforces(pointa, pointb, newpoint)
                    reducedaf = af
                    reducedff = ff
                    relaxedpoint = self.relaxpoint(newpoint, reducedaf, reducedff, 0.5, 0.5)
                    newpoint = relaxedpoint[0]
                    newspringmesh[i][j + 1] = newpoint
                elif i == 0:
                    pointa = newspringmesh[i][j]
                    pointb = newspringmesh[i + 2][j]
                    newpoint = self.findgeomidpoint(pointa, pointb)
                    af, ff = self.subdivisionforces(pointa, pointb, newpoint)
                    reducedaf = af
                    reducedff = ff
                    relaxedpoint = self.relaxpoint(newpoint, reducedaf, reducedff, 0.5, 0.5)
                    newpoint = relaxedpoint[0]
                    newspringmesh[i + 1][j] = newpoint
                else:
                    pointa = newspringmesh[i][j]
                    pointb = newspringmesh[i][j + 2]
                    newpoint = self.findgeomidpoint(pointa, pointb)
                    af, ff = self.subdivisionforces(pointa, pointb, newpoint)
                    reducedaf = af
                    reducedff = ff
                    relaxedpoint = self.relaxpoint(newpoint, reducedaf, reducedff, 0.5, 0.5)
                    newpoint = relaxedpoint[0]
                    newspringmesh[i][j + 1] = newpoint

                    pointa = newspringmesh[i][j]
                    pointb = newspringmesh[i + 2][j]
                    newpoint = self.findgeomidpoint(pointa, pointb)
                    af, ff = self.subdivisionforces(pointa, pointb, newpoint)
                    reducedaf = af
                    reducedff = ff
                    relaxedpoint = self.relaxpoint(newpoint, reducedaf, reducedff, 0.5, 0.5)
                    newpoint = relaxedpoint[0]
                    newspringmesh[i + 1][j] = newpoint

        for j in range(1, newnumcols - 1, 2):
            for i in range(0, newnumrows - 2, 2):
                pointa = newspringmesh[i][j]
                pointb = newspringmesh[i + 2][j]
                newpoint = self.findgeomidpoint(pointa, pointb)
                af, ff = self.subdivisionforces(pointa, pointb, newpoint)
                reducedaf = af
                reducedff = ff
                relaxedpoint = self.relaxpoint(newpoint, reducedaf, reducedff, 0.5, 0.5)
                newpoint = relaxedpoint[0]
                newspringmesh[i + 1][j] = newpoint
        self.springmeshmatrix = newspringmesh

    def creategrid(self, iterations, dirname):
        dirpath = "./" + dirname
        Path(dirpath).mkdir(parents=True, exist_ok=True)
        path = dirpath + "/"
        for i in range(iterations):
            filename = "gridpoints" + str(i) + ".csv"
            newfile = path + filename

            starttime = time.time()
            self.relaxallpoints(3)
            print('grid relaxation done  -  iteration:', i + 1, ' -  time:', time.time() - starttime)

            np.savetxt(newfile, self.getpointsarray(), delimiter=",")

            starttime = time.time()
            self.subdividespringmesh()
            print('grid subdivision done  -  iteration:', i + 1, ' -  time:', time.time() - starttime)
        starttime = time.time()
        self.relaxallpoints(3)
        print('final relaxation done  -  time:', time.time() - starttime)
        print("Size in u direction: ", len(self.springmeshmatrix))
        print("Size in v direction: ", len(self.springmeshmatrix[0]))
        np.savetxt(path + "gridpointsfinal.csv", self.getpointsarray(), delimiter=",")

    def getpointsarray(self):
        return self.springmeshmatrix.reshape((self.springmeshmatrix.shape[0] * self.springmeshmatrix.shape[1], 3))

    def getsize(self):
        return [self.springmeshmatrix.shape[0], self.springmeshmatrix.shape[1]]
