import shutil
from creategrid import CreateGrid
import os
import time
from pathlib import Path
# from visualizesurf import VisualizeSurf
import matplotlib.pyplot as plt
from geomdl import fitting, tessellate
from geomdl.visualization import VisVTK
from rich.console import Console
from rich.progress import track
from vedo import mesh, pointcloud, plotter

from stp2surf import Stp2Surf
from surf2stp import Surf2Stp
from tools.smmothstep_ls import smoothstep_sample
from utilities import *


fit_weight = 0.5
fit_numIteration = 4

strategie = 'mean'

start0 = time.time()

console = Console(color_system='256', style=None)

opt_degree_u = 3
opt_degree_v = 2
opt_numctrlpts_u = 54
opt_numctrlpts_v = 84

figureindex = 0
targetStl = mesh.Mesh("data/targets/target_AF_bs.stl")
targetStl_cut = targetStl.clone()
targetStl_cut.cutWithBox([-78, 308, -71, 65, -1000, 1000], invert=False)

start1 = time.time()
# CreateGrid("data/targets/3DS_target_mesh.stl", "data/Gemessen", False, "gemessen")
# CreateGrid("data/targets/target_AF_bs.stl", "X:/Ergebnisse/median/0.5/i4/simulation", True, "grids_simulated/i0")
end1 = time.time()
run_time1 = (end1 - start1) / 3600
print("\033[1;35m Time CreateGrid = {:.2f} h\033[0m".format(run_time1))
size_u = 97
size_v = 161

# fit target b-spline surface and create triangular mesh
if not os.path.exists('target_fit_surf'):
    targetGridPoints = np.genfromtxt("targetgridpoints/gridpointsfinal.csv", delimiter=",")
    targetFitSurf = fitting.approximate_surface(targetGridPoints, size_u, size_v, degree_u=opt_degree_u,
                                                degree_v=opt_degree_v, ctrlpts_size_u=opt_numctrlpts_u,
                                                ctrlpts_size_v=opt_numctrlpts_v)
    Path("target_fit_surf").mkdir(parents=True, exist_ok=True)
    np.savetxt("target_fit_surf/target_crtlpts.csv", targetFitSurf.ctrlpts, delimiter=",")
    np.savetxt("target_fit_surf/target_knotvector_u.csv", targetFitSurf.knotvector_u, delimiter=",")
    np.savetxt("target_fit_surf/target_knotvector_v.csv", targetFitSurf.knotvector_v, delimiter=",")
else:
    targetFitSurf = BSpline.Surface()
    targetFitSurf.degree_u = opt_degree_u
    targetFitSurf.degree_v = opt_degree_v
    targetFitSurf.ctrlpts_size_u = opt_numctrlpts_u
    targetFitSurf.ctrlpts_size_v = opt_numctrlpts_v
    targetFitSurf.ctrlpts = np.genfromtxt("target_fit_surf/target_crtlpts.csv", delimiter=",").tolist()
    targetFitSurf.knotvector_u = np.genfromtxt("target_fit_surf/target_knotvector_u.csv", delimiter=",").tolist()
    targetFitSurf.knotvector_v = np.genfromtxt("target_fit_surf/target_knotvector_v.csv", delimiter=",").tolist()

targetFitSurf.delta = 0.01
targettrimesh = tessellate.make_triangle_mesh(targetFitSurf.evalpts, targetFitSurf.sample_size_u,
                                              targetFitSurf.sample_size_v)
faces = [x.vertex_ids for x in targettrimesh[1]]
vertices = [x.data for x in targettrimesh[0]]
targetMesh = mesh.Mesh([vertices, faces])
targetMesh.c("white")

start2 = time.time()

simulatedDiffNormList = list()
simulatedSurfaces = list()
simulatedCtrlPts = list()
simulatedEvalDiff = list()
meanSimulatedCtrlPts = list()
if not os.path.exists('simulated_fit_surf'):
    Path("simulated_fit_surf").mkdir(parents=True, exist_ok=True)
    # read simulated grid points
    simulatedGridPoints = list()
    # example file path: grids_simulated/i0/gridpoints00/gridpointsfinal.csv
    numSimulatedIterations = 0
    for iterationFile in os.listdir("grids_simulated"):
        currIterGridPoints = list()
        for file in os.listdir("grids_simulated/" + iterationFile):
            gridPoints = np.genfromtxt("grids_simulated/" + iterationFile + "/" + file + "/gridpointsfinal.csv",
                                       delimiter=",").tolist()
            currIterGridPoints.append(gridPoints)
        simulatedGridPoints.append(currIterGridPoints)
        numSimulatedIterations += 1

    iterNum = 0
    # fit b-spline surfaces on simulated grids
    for iteration in simulatedGridPoints:
        iterationPath = "simulated_fit_surf/" + str(iterNum)
        Path(iterationPath).mkdir(parents=True, exist_ok=True)
        currIterSimulatedDiffNormList = list()
        currIterSimulatedSurfaces = list()
        currIterMeanSimulatedCtrlPts = np.zeros((opt_numctrlpts_u * opt_numctrlpts_v, 3))
        currIterSimulatedCtrlPts = list()
        currIterSimulatedEvalDiff = list()
        index = 1
        for gridPoints in track(iteration, description='[cyan] Generating simulated_fit_surf'):

            print(index)

            simulatedFitSurf = approximate_surface_with_knotvector(gridPoints, size_u, size_v, degree_u=opt_degree_u,
                                                                   degree_v=opt_degree_v,
                                                                   knotvector_u=targetFitSurf.knotvector_u,
                                                                   knotvector_v=targetFitSurf.knotvector_v,
                                                                   ctrlpts_size_u=opt_numctrlpts_u,
                                                                   ctrlpts_size_v=opt_numctrlpts_v)
            simulatedFitSurf.delta = 0.01
            simulatedTri = tessellate.make_triangle_mesh(simulatedFitSurf.evalpts,
                                                         simulatedFitSurf.sample_size_u,
                                                         simulatedFitSurf.sample_size_v)
            faces = [x.vertex_ids for x in simulatedTri[1]]
            vertices = [x.data for x in simulatedTri[0]]
            simulatedMesh = mesh.Mesh([vertices, faces])
            simulatedMesh.distanceToMesh(targetStl, signed=True)
            simulatedDistance = simulatedMesh.getPointArray("Distance")
            currIterSimulatedEvalDiff.append(np.abs(simulatedDistance))
            surfPath = iterationPath + "/simulated" + str(index)
            Path(surfPath).mkdir(parents=True, exist_ok=True)
            np.savetxt(surfPath + "/simulated_crtlpts.csv", simulatedFitSurf.ctrlpts,
                       delimiter=",")
            np.savetxt(surfPath + "/simulated_knotvector_u.csv", simulatedFitSurf.knotvector_u,
                       delimiter=",")
            np.savetxt(surfPath + "/simulated_knotvector_v.csv", simulatedFitSurf.knotvector_v,
                       delimiter=",")
            index += 1

            currIterSimulatedSurfaces.append(simulatedFitSurf)
            diffvectors = np.subtract(targetFitSurf.ctrlpts, simulatedFitSurf.ctrlpts)
            diffnorms = np.linalg.norm(diffvectors, axis=1)
            currIterSimulatedDiffNormList.append(diffnorms)
            currIterMeanSimulatedCtrlPts = currIterMeanSimulatedCtrlPts + simulatedFitSurf.ctrlpts
            currIterSimulatedCtrlPts.append(simulatedFitSurf.ctrlpts)
            time.sleep(0.01)
        simulatedEvalDiff.append(currIterSimulatedEvalDiff)
        currIterMeanSimulatedCtrlPts = np.divide(currIterMeanSimulatedCtrlPts, len(iteration))
        simulatedDiffNormList.append(currIterSimulatedDiffNormList)
        simulatedSurfaces.append(currIterSimulatedSurfaces)
        meanSimulatedCtrlPts.append(currIterMeanSimulatedCtrlPts)
        simulatedCtrlPts.append(currIterSimulatedCtrlPts)
        iterNum += 1
else:
    numSimulatedIterations = len(os.listdir("simulated_fit_surf"))
    for iteration in os.listdir("simulated_fit_surf"):
        currIterSimulatedDiffNormList = list()
        currIterSimulatedSurfaces = list()
        currIterMeanSimulatedCtrlPts = np.zeros((opt_numctrlpts_u * opt_numctrlpts_v, 3))
        currIterSimulatedCtrlPts = list()
        currIterSimulatedEvalDiff = list()

        iterPath = "simulated_fit_surf/" + iteration
        ctrlpts = None
        knotvector_u = None
        knotvector_v = None
        for files in track(os.listdir(iterPath), description='[cyan] loading simulated_fit_surf'):
            surf = BSpline.Surface()
            surf.degree_u = opt_degree_u
            surf.degree_v = opt_degree_v
            surf.ctrlpts_size_u = opt_numctrlpts_u
            surf.ctrlpts_size_v = opt_numctrlpts_v
            surf.delta = 0.01
            for file in os.listdir(iterPath + "/" + files):
                filePath = iterPath + "/" + files + "/" + file
                if file == "simulated_crtlpts.csv":
                    ctrlpts = np.genfromtxt(filePath, delimiter=",").tolist()
                    surf.ctrlpts = ctrlpts
                elif file == "simulated_knotvector_u.csv":
                    knotvector_u = np.genfromtxt(filePath, delimiter=",").tolist()
                    surf.knotvector_u = knotvector_u
                elif file == "simulated_knotvector_v.csv":
                    knotvector_v = np.genfromtxt(filePath, delimiter=",").tolist()
                    surf.knotvector_v = knotvector_v
            simulatedTri = tessellate.make_triangle_mesh(surf.evalpts,
                                                         surf.sample_size_u,
                                                         surf.sample_size_v)
            faces = [x.vertex_ids for x in simulatedTri[1]]
            vertices = [x.data for x in simulatedTri[0]]
            simulatedMesh = mesh.Mesh([vertices, faces])
            simulatedMesh.distanceToMesh(targetStl, signed=True)
            simulatedDistance = simulatedMesh.getPointArray("Distance")
            currIterSimulatedEvalDiff.append(np.abs(simulatedDistance))
            currIterSimulatedSurfaces.append(surf)
            diffvectors = np.subtract(targetFitSurf.ctrlpts, surf.ctrlpts)
            diffnorms = np.linalg.norm(diffvectors, axis=1)
            currIterSimulatedDiffNormList.append(diffnorms)
            currIterMeanSimulatedCtrlPts = currIterMeanSimulatedCtrlPts + surf.ctrlpts
            currIterSimulatedCtrlPts.append(surf.ctrlpts)
            time.sleep(0.01)
        simulatedEvalDiff.append(currIterSimulatedEvalDiff)
        currIterMeanSimulatedCtrlPts = np.divide(currIterMeanSimulatedCtrlPts, len(os.listdir(iterPath)))
        simulatedDiffNormList.append(currIterSimulatedDiffNormList)
        simulatedSurfaces.append(currIterSimulatedSurfaces)
        meanSimulatedCtrlPts.append(currIterMeanSimulatedCtrlPts)
        simulatedCtrlPts.append(currIterSimulatedCtrlPts)

end2 = time.time()
run_time2 = (end2 - start2) / 60
print("\033[1;36m Time for simulated_fit_surf = {:.2f} min\033[0m".format(run_time2))

# fit b-spline surfaces on measured grids
measuredDiffNormList = list()
measuredSurfaces = list()
measuredCtrlPts = list()
meanMeasuredCtrlPts = list()
measuredEvalDiff = list()
if not os.path.exists('measured_fit_surf'):
    Path("measured_fit_surf").mkdir(parents=True, exist_ok=True)
    # read measured grid points
    measuredGridPoints = list()
    # example file path: grids_measured/i0/gridpoints00/gridpointsfinal.csv
    numMeasuredIterations = 0
    for iterationFile in os.listdir("grids_measured"):
        currIterGridPoints = list()
        for file in os.listdir("grids_measured/" + iterationFile):
            gridPoints = np.genfromtxt("grids_measured/" + iterationFile + "/" + file + "/gridpointsfinal.csv",
                                       delimiter=",").tolist()
            currIterGridPoints.append(gridPoints)
        measuredGridPoints.append(currIterGridPoints)
        numMeasuredIterations += 1

    iterNum = 0
    # fit b-spline surfaces on measured grids
    for iteration in measuredGridPoints:
        iterationPath = "measured_fit_surf/" + str(iterNum)
        Path(iterationPath).mkdir(parents=True, exist_ok=True)
        currIterMeasuredDiffNormList = list()
        currIterMeasuredSurfaces = list()
        currIterMeanMeasuredCtrlPts = np.zeros((opt_numctrlpts_u * opt_numctrlpts_v, 3))
        currIterMeasuredCtrlPts = list()
        currIterMeasuredEvalDiff = list()
        index = 0
        for gridPoints in iteration:
            measuredFitSurf = approximate_surface_with_knotvector(gridPoints, size_u, size_v, degree_u=opt_degree_u,
                                                                  degree_v=opt_degree_v,
                                                                  knotvector_u=targetFitSurf.knotvector_u,
                                                                  knotvector_v=targetFitSurf.knotvector_v,
                                                                  ctrlpts_size_u=opt_numctrlpts_u,
                                                                  ctrlpts_size_v=opt_numctrlpts_v)
            measuredFitSurf.delta = 0.01
            measuredTri = tessellate.make_triangle_mesh(measuredFitSurf.evalpts,
                                                        measuredFitSurf.sample_size_u,
                                                        measuredFitSurf.sample_size_v)
            faces = [x.vertex_ids for x in measuredTri[1]]
            vertices = [x.data for x in measuredTri[0]]
            measuredMesh = mesh.Mesh([vertices, faces])
            measuredMesh.distanceToMesh(targetStl, signed=True)
            measuredDistance = measuredMesh.getPointArray("Distance")
            currIterMeasuredEvalDiff.append(np.abs(measuredDistance))
            surfPath = iterationPath + "/measured" + str(index)
            Path(surfPath).mkdir(parents=True, exist_ok=True)
            np.savetxt(surfPath + "/measured_crtlpts.csv", measuredFitSurf.ctrlpts,
                       delimiter=",")
            np.savetxt(surfPath + "/measured_knotvector_u.csv", measuredFitSurf.knotvector_u,
                       delimiter=",")
            np.savetxt(surfPath + "/measured_knotvector_v.csv", measuredFitSurf.knotvector_v,
                       delimiter=",")
            index += 1

            currIterMeasuredSurfaces.append(measuredFitSurf)
            diffvectors = np.subtract(targetFitSurf.ctrlpts, measuredFitSurf.ctrlpts)
            diffnorms = np.linalg.norm(diffvectors, axis=1)
            currIterMeasuredDiffNormList.append(diffnorms)
            currIterMeanMeasuredCtrlPts = currIterMeanMeasuredCtrlPts + measuredFitSurf.ctrlpts
            currIterMeasuredCtrlPts.append(measuredFitSurf.ctrlpts)
        measuredEvalDiff.append(currIterMeasuredEvalDiff)
        currIterMeanMeasuredCtrlPts = np.divide(currIterMeanMeasuredCtrlPts, len(iteration))
        measuredDiffNormList.append(currIterMeasuredDiffNormList)
        measuredSurfaces.append(currIterMeasuredSurfaces)
        meanMeasuredCtrlPts.append(currIterMeanMeasuredCtrlPts)
        measuredCtrlPts.append(currIterMeasuredCtrlPts)
        iterNum += 1
else:
    numMeasuredIterations = len(os.listdir("measured_fit_surf"))
    for iteration in os.listdir("measured_fit_surf"):
        currIterMeasuredDiffNormList = list()
        currIterMeasuredSurfaces = list()
        currIterMeanMeasuredCtrlPts = np.zeros((opt_numctrlpts_u * opt_numctrlpts_v, 3))
        currIterMeasuredCtrlPts = list()
        currIterMeasuredEvalDiff = list()

        iterPath = "measured_fit_surf/" + iteration
        ctrlpts = None
        knotvector_u = None
        knotvector_v = None
        for files in os.listdir(iterPath):
            surf = BSpline.Surface()
            surf.degree_u = opt_degree_u
            surf.degree_v = opt_degree_v
            surf.ctrlpts_size_u = opt_numctrlpts_u
            surf.ctrlpts_size_v = opt_numctrlpts_v
            surf.delta = 0.01
            for file in os.listdir(iterPath + "/" + files):
                filePath = iterPath + "/" + files + "/" + file
                if file == "measured_crtlpts.csv":
                    ctrlpts = np.genfromtxt(filePath, delimiter=",").tolist()
                    surf.ctrlpts = ctrlpts
                elif file == "measured_knotvector_u.csv":
                    knotvector_u = np.genfromtxt(filePath, delimiter=",").tolist()
                    surf.knotvector_u = knotvector_u
                elif file == "measured_knotvector_v.csv":
                    knotvector_v = np.genfromtxt(filePath, delimiter=",").tolist()
                    surf.knotvector_v = knotvector_v
            measuredTri = tessellate.make_triangle_mesh(surf.evalpts,
                                                        surf.sample_size_u,
                                                        surf.sample_size_v)
            faces = [x.vertex_ids for x in measuredTri[1]]
            vertices = [x.data for x in measuredTri[0]]
            measuredMesh = mesh.Mesh([vertices, faces])
            measuredMesh.distanceToMesh(targetStl, signed=True)
            measuredDistance = measuredMesh.getPointArray("Distance")
            currIterMeasuredEvalDiff.append(np.abs(measuredDistance))
            currIterMeasuredSurfaces.append(surf)
            diffvectors = np.subtract(targetFitSurf.ctrlpts, surf.ctrlpts)
            diffnorms = np.linalg.norm(diffvectors, axis=1)
            currIterMeasuredDiffNormList.append(diffnorms)
            currIterMeanMeasuredCtrlPts = currIterMeanMeasuredCtrlPts + surf.ctrlpts
            currIterMeasuredCtrlPts.append(surf.ctrlpts)
        measuredEvalDiff.append(currIterMeasuredEvalDiff)
        currIterMeanMeasuredCtrlPts = np.divide(currIterMeanMeasuredCtrlPts, len(os.listdir(iterPath)))
        measuredDiffNormList.append(currIterMeasuredDiffNormList)
        measuredSurfaces.append(currIterMeasuredSurfaces)
        meanMeasuredCtrlPts.append(currIterMeanMeasuredCtrlPts)
        measuredCtrlPts.append(currIterMeasuredCtrlPts)

# create b-spline surface and triangular mesh from simulated mean control points
meanSimulatedSurface = BSpline.Surface()
meanSimulatedSurface.degree_u = opt_degree_u
meanSimulatedSurface.degree_v = opt_degree_v
meanSimulatedSurface.ctrlpts_size_u = opt_numctrlpts_u
meanSimulatedSurface.ctrlpts_size_v = opt_numctrlpts_v
meanSimulatedSurface.ctrlpts = meanSimulatedCtrlPts[-1].tolist()
meanSimulatedSurface.knotvector_u = targetFitSurf.knotvector_u
meanSimulatedSurface.knotvector_v = targetFitSurf.knotvector_v
meanSimulatedSurface.delta = 0.01
meanSimulatedTri = tessellate.make_triangle_mesh(meanSimulatedSurface.evalpts, meanSimulatedSurface.sample_size_u,
                                                 meanSimulatedSurface.sample_size_v)
faces = [x.vertex_ids for x in meanSimulatedTri[1]]
vertices = [x.data for x in meanSimulatedTri[0]]
meanSimulatedMesh = mesh.Mesh([vertices, faces])
meanSimulatedMesh.distanceToMesh(targetStl, signed=True)
simulatedDistance = meanSimulatedMesh.getPointArray("Distance")

meanSimulatedMesh.write('test/meanSimulatedMesh.stl')

# create b-spline surface and triangular mesh from measured mean control points
meanMeasuredSurface = BSpline.Surface()
meanMeasuredSurface.degree_u = opt_degree_u
meanMeasuredSurface.degree_v = opt_degree_v
meanMeasuredSurface.ctrlpts_size_u = opt_numctrlpts_u
meanMeasuredSurface.ctrlpts_size_v = opt_numctrlpts_v
meanMeasuredSurface.ctrlpts = meanMeasuredCtrlPts[-1].tolist()
meanMeasuredSurface.knotvector_u = targetFitSurf.knotvector_u
meanMeasuredSurface.knotvector_v = targetFitSurf.knotvector_v
meanMeasuredSurface.delta = 0.01
meanMeasuredTri = tessellate.make_triangle_mesh(meanMeasuredSurface.evalpts, meanMeasuredSurface.sample_size_u,
                                                meanMeasuredSurface.sample_size_v)
faces = [x.vertex_ids for x in meanMeasuredTri[1]]
vertices = [x.data for x in meanMeasuredTri[0]]
meanMeasuredMesh = mesh.Mesh([vertices, faces])
meanMeasuredMesh.distanceToMesh(targetStl, signed=True)
measuredDistance = meanMeasuredMesh.getPointArray("Distance")

maxDistance = max(max(abs(simulatedDistance)), max(abs(measuredDistance)))

meanMeasuredMesh.cmap("jet", measuredDistance, vmin=-maxDistance, vmax=maxDistance)
meanSimulatedMesh.cmap("jet", simulatedDistance, vmin=-maxDistance, vmax=maxDistance)
# meanSimulatedMesh.addScalarBar(title='Signed\nDistance')
# meanMeasuredMesh.addScalarBar(title='Signed\nDistance')

meanSimulatedMesh.addScalarBar(title='Signed\nDistance')
meanMeasuredMesh.addScalarBar(title='Signed\nDistance')

meanSimulatedPc = pointcloud.Points(meanSimulatedCtrlPts[-1])
meanMeasuredPc = pointcloud.Points(meanMeasuredCtrlPts[-1])
simulatedLastIterPc = pointcloud.Points(simulatedSurfaces[-1][0].ctrlpts)
simulatedLastIterPc.c("green")
measuredLastIterPc = pointcloud.Points(measuredSurfaces[-1][0].ctrlpts)
measuredLastIterPc.c("blue")

max_iterations = max(numMeasuredIterations, numSimulatedIterations)

simMeanDiffIterations = [np.mean(it) for it in simulatedDiffNormList]
measuredMeanDiffIterations = [np.mean(it) for it in measuredDiffNormList]
simMeanEvalDiffIterations = [np.mean(it) for it in simulatedEvalDiff]
measuredMeanEvalDiffIterations = [np.mean(it) for it in measuredEvalDiff]

simLastIterDiff = np.array(simulatedEvalDiff[-1])
maxIndices = np.argmax(simLastIterDiff, axis=0)
simMaxDiff = simLastIterDiff[maxIndices, np.arange(len(simLastIterDiff[0]))]
simMeanDiff = np.mean(simLastIterDiff, axis=0)
simMedianDiff = np.median(simLastIterDiff, axis=0)




np.savetxt('simulatedDistance.csv', simulatedDistance, delimiter=',')

np.savetxt('simLastIterDiff.csv', simLastIterDiff, delimiter=',')

np.savetxt('simMaxDiff.csv', simMaxDiff, delimiter=',')
np.savetxt('simMeanDiff.csv', simMeanDiff, delimiter=',')
np.savetxt('simMedianDiff.csv', simMedianDiff, delimiter=',')


SaveDir2 = f'X:/Ergebnisse/{strategie}/{str(fit_weight)}/i{str(fit_numIteration)}'
os.chdir(f'X:/Modell/tryout-manager')

shutil.copy('simulatedDistance.csv', SaveDir2)

# if strategie == "max":
#     print("\nSaving simMaxDiff...")
#     shutil.copy('simMaxDiff.csv', SaveDir2)
# if strategie == "mean":
#     print("\nSaving simMeanDiff...")
#     shutil.copy('simMeanDiff.csv', SaveDir2)
# if strategie == "median":
#     print("\nSaving simMedianDiff...")
#     shutil.copy('simMedianDiff.csv', SaveDir2)
    



measuredLastIterDiff = np.array(measuredEvalDiff[-1])
maxIndices = np.argmax(measuredLastIterDiff, axis=0)
measuredMaxDiff = measuredLastIterDiff[maxIndices, np.arange(len(measuredLastIterDiff[0]))]
measuredMeanDiff = np.mean(measuredLastIterDiff, axis=0)
measuredMedianDiff = np.median(measuredLastIterDiff, axis=0)







end0 = time.time()
run_time0 = (end0 - start0) / 3600
print("\033[1;34m Time Total = {:.2f} h\033[0m".format(run_time0))

plt.figure(figureindex, figsize=(10, 10))
plt.subplot(2, 2, 1)
plt.scatter(range(numSimulatedIterations), simMeanDiffIterations)
plt.xticks(np.arange(numSimulatedIterations))
plt.xlabel("iteration")
plt.ylabel("mean deviation")
plt.title("simulated mean control point deviations")

plt.subplot(2, 2, 2)
plt.scatter(range(numMeasuredIterations), measuredMeanDiffIterations)
plt.xticks(np.arange(numMeasuredIterations))
plt.xlabel("iteration")
plt.ylabel("mean deviation")
plt.title("measured mean control point deviations")

plt.subplot(2, 2, 3)
plt.scatter(range(numSimulatedIterations), simMeanEvalDiffIterations)
plt.xticks(np.arange(numSimulatedIterations))
plt.xlabel("iteration")
plt.ylabel("mean deviation")
plt.title("simulated mean evaluated point deviations")

plt.subplot(2, 2, 4)
plt.scatter(range(numMeasuredIterations), measuredMeanEvalDiffIterations)
plt.xticks(np.arange(numMeasuredIterations))
plt.xlabel("iteration")
plt.ylabel("mean deviation")
plt.title("measured mean evaluated point deviations")
plt.show()
figureindex += 1

np.savetxt("simulated mean evaluated point deviations.txt", simMeanEvalDiffIterations, delimiter=",")


def func(evt):
    global figureindex
    if not evt.actor:
        return
    point = evt.picked3d
    at = evt.at
    pc_point_index = 0
    evalpts_index = 0
    if at == 0 or at == 2:
        # simulated
        pc_point_index = simulatedLastIterPc.closestPoint(point, returnPointId=True)
        evalpts_index = pointcloud.Points(simulatedSurfaces[-1][0].evalpts).closestPoint(point, returnPointId=True)
    elif at == 1:
        # measured
        pc_point_index = measuredLastIterPc.closestPoint(point, returnPointId=True)
        evalpts_index = pointcloud.Points(measuredSurfaces[-1][0].evalpts).closestPoint(point, returnPointId=True)

    simulated_deviations = [[row[pc_point_index] for row in it] for it in simulatedDiffNormList]
    measured_deviations = [[row[pc_point_index] for row in it] for it in measuredDiffNormList]

    simulated_eval_deviations = [[row[evalpts_index] for row in it] for it in simulatedEvalDiff]
    measured_eval_deviations = [[row[evalpts_index] for row in it] for it in measuredEvalDiff]

    variance_simulated = list()
    sigma_simulated = list()
    for iteration in simulated_deviations:
        var = np.var(iteration)
        variance_simulated.append(var)
        sigma_simulated.append(np.sqrt(var))
    variance_measured = list()
    sigma_measured = list()
    for iteration in measured_deviations:
        var = np.var(iteration)
        variance_measured.append(var)
        sigma_measured.append(np.sqrt(var))

    variance_eval_simulated = list()
    sigma_eval_simulated = list()
    for iteration in simulated_eval_deviations:
        var = np.var(iteration)
        variance_eval_simulated.append(var)
        sigma_eval_simulated.append(np.sqrt(var))
    variance_eval_measured = list()
    sigma_eval_measured = list()
    for iteration in measured_eval_deviations:
        var = np.var(iteration)
        variance_eval_measured.append(var)
        sigma_eval_measured.append(np.sqrt(var))

    simulated_eval_mean_deviations = [np.mean([row[evalpts_index] for row in it]) for it in simulatedEvalDiff]
    measured_eval_mean_deviations = [np.mean([row[evalpts_index] for row in it]) for it in measuredEvalDiff]

    simulated_eval_dev_padding = np.pad(simulated_eval_mean_deviations,
                                        (0, max_iterations - len(simulated_eval_mean_deviations)))
    measured_eval_dev_padding = np.pad(measured_eval_mean_deviations,
                                       (0, max_iterations - len(measured_eval_mean_deviations)))

    sigma_simulated_eval_padding = np.pad(sigma_eval_simulated, (0, max_iterations - len(sigma_eval_simulated)))
    sigma_measured_eval_padding = np.pad(sigma_eval_measured, (0, max_iterations - len(sigma_eval_measured)))

    simulated_mean_cp = [it[pc_point_index] for it in meanSimulatedCtrlPts]
    measured_mean_cp = [it[pc_point_index] for it in meanMeasuredCtrlPts]
    soll_cp = targetFitSurf.ctrlpts[pc_point_index]

    xm = np.array([meancp - soll_cp for meancp in measured_mean_cp])
    xs = np.array([meancp - soll_cp for meancp in simulated_mean_cp])
    k = np.cross(xm[-1], xs[-1])
    k = k / np.linalg.norm(k)
    s = np.cross(k, xm[-1])

    v = xm[-1] / np.linalg.norm(xm[-1])
    s = s / np.linalg.norm(s)
    basismatrix = np.vstack((v, s, k)).T
    basismatrixinv = np.linalg.inv(basismatrix)

    measuredcoordinates = np.dot(basismatrixinv, xm[-1])
    simulatedcoordinates = np.dot(basismatrixinv, xs[-1])

    xm_padding = [np.dot(basismatrixinv, a) for a in xm]
    xs_padding = [np.dot(basismatrixinv, a) for a in xs]
    while len(xm_padding) < max_iterations:
        xm_padding = np.vstack((xm_padding, xm_padding[-1]))
    while len(xs_padding) < max_iterations:
        xs_padding = np.vstack((xs_padding, xs_padding[-1]))

    alphalist = list()
    for i in range(max_iterations):
        alpha = np.arccos(np.clip(np.dot(xm_padding[i] / np.linalg.norm(xm_padding[i]),
                                         xs_padding[i] / np.linalg.norm(xs_padding[i])),
                                  -1.0, 1.0)) * 180 / np.pi
        alphalist.append(alpha)

    circlemeasured = plt.Circle(measuredcoordinates, sigma_measured[-1], color='#003359', ls="--", fill=False,
                                alpha=0.8)
    circlesimulated = plt.Circle(simulatedcoordinates, sigma_simulated[-1], color='#005293', ls="--", fill=False,
                                 alpha=0.8)

    sigma_measured_padding = np.pad(sigma_measured, (0, max_iterations - len(sigma_measured)))
    sigma_simulated_padding = np.pad(sigma_simulated, (0, max_iterations - len(sigma_simulated)))
    normmeasured = np.linalg.norm(xm, axis=1)
    normmeasured_padding = np.pad(normmeasured, (0, max_iterations - len(normmeasured)))
    normsimulated = np.linalg.norm(xs, axis=1)
    normsimulated_padding = np.pad(normsimulated, (0, max_iterations - len(normsimulated)))

    plt.figure(figureindex, figsize=(10, 10))
    plt.subplot(2, 2, 1)
    figureindex = figureindex + 1
    axislimit = max(normmeasured[-1] + sigma_measured[-1],
                    normsimulated[-1] + sigma_simulated[-1]) + 0.2

    origin = np.array(([0, 0], [0, 0]))
    plt.quiver(*origin, measuredcoordinates[0], measuredcoordinates[1], color='#003359', angles='xy',
               scale_units='xy', scale=1, label="measured")
    plt.quiver(*origin, simulatedcoordinates[0], simulatedcoordinates[1], color='#005293', angles='xy',
               scale_units='xy', scale=1, label="simulated")
    fig = plt.gcf()
    ax = fig.gca()
    ax.add_patch(circlemeasured)
    ax.add_patch(circlesimulated)
    plt.title("control point " + str(pc_point_index) + ", alpha = " + "{:.1f}".format(alphalist[-1]) + u"\u00b0")
    plt.xlim([-axislimit, axislimit])
    plt.ylim([-axislimit, axislimit])
    plt.xlabel("v")
    plt.ylabel("s")
    plt.legend()

    plt.subplot(2, 2, 2)
    iterations = range(max(numMeasuredIterations, numSimulatedIterations))
    positions = np.arange(len(iterations))
    fig = plt.gcf()
    ax = fig.gca()
    width = 0.35
    rects1 = ax.bar(positions - width / 2, normmeasured_padding, width, yerr=sigma_measured_padding, capsize=10,
                    label='measured', color="#003359")
    rects2 = ax.bar(positions + width / 2, normsimulated_padding, width, yerr=sigma_simulated_padding, capsize=10,
                    label='simulated', color="#005293")
    ax.bar_label(rects1, padding=3)
    ax.bar_label(rects2, padding=3)
    ax.set_xticks(iterations)
    ax.legend()
    plt.xlabel("iteration")
    plt.ylabel("deviation")
    plt.title("mean deviation of control point " + str(pc_point_index))

    plt.subplot(2, 2, 3)
    plt.scatter(iterations, alphalist, c="#3070b3")
    plt.xticks(np.arange(0, len(iterations), 1))
    plt.xlabel("iteration")
    plt.ylabel("degrees (" + u"\u00b0" + ")")
    plt.title("alpha")

    plt.subplot(2, 2, 4)
    fig = plt.gcf()
    ax = fig.gca()
    width = 0.35
    rects3 = ax.bar(positions - width / 2, measured_eval_dev_padding, width, yerr=sigma_measured_eval_padding,
                    capsize=10, label='measured', color="#003359")
    rects4 = ax.bar(positions + width / 2, simulated_eval_dev_padding, width, yerr=sigma_simulated_eval_padding,
                    capsize=10, label='simulated', color="#005293")
    ax.bar_label(rects3, padding=3)
    ax.bar_label(rects4, padding=3)
    ax.set_xticks(iterations)
    ax.legend()
    plt.xlabel("iteration")
    plt.ylabel("deviation")
    plt.title("mean deviation of evaluated point " + str(evalpts_index))
    plt.show()


pltr = plotter.Plotter(shape=[2, 2], title="simulated mean, measured mean, control points", size=[1600, 900])
pltr.addCallback('mouse click', func)
pltr.show(meanSimulatedMesh, at=0)
pltr.show(meanMeasuredMesh, at=1)
pltr.show(pointcloud.Points(targetFitSurf.ctrlpts).c("#3070b3"), at=2, interactive=True)

simulatedDiffNormListLastIter = simulatedDiffNormList[-1]
simulatedCtrlPtsLastIter = np.array(simulatedCtrlPts[-1])
maxIndices = np.argmax(simulatedDiffNormListLastIter, axis=0)
simulatedMaxCtrlPts = simulatedCtrlPtsLastIter[maxIndices, np.arange(len(simulatedCtrlPtsLastIter[0]))]
simulatedMeanCtrlPts = np.mean(simulatedCtrlPtsLastIter, axis=0)
simulatedMedianCtrlPts = np.median(simulatedCtrlPtsLastIter, axis=0)





measuredDiffNormListLastIter = measuredDiffNormList[-1]
measuredCtrlPtsLastIter = np.array(measuredCtrlPts[-1])
maxIndices = np.argmax(measuredDiffNormListLastIter, axis=0)
measuredMaxCtrlPts = measuredCtrlPtsLastIter[maxIndices, np.arange(len(measuredCtrlPtsLastIter[0]))]
measuredMeanCtrlPts = np.mean(measuredCtrlPtsLastIter, axis=0)
measuredMedianCtrlPts = np.median(measuredCtrlPtsLastIter, axis=0)

while True:
    print("""
    1. mean measured
    2. max measured
    3. median measured
    4. mean simulated
    5. max simulated
    6. median simulated
    0. exit
    """)
    selectedSurfaceIndex = int(input("Surface: "))
    if selectedSurfaceIndex == 0:
        break

    compWeight = float(input("Compensation Weight: "))
    print()

    targetList = os.listdir("data/targets")
    i = 1
    for target in targetList:
        print(str(i) + ". " + target)
        i += 1
    print()
    selectedTargetIndex = int(input("Select a target file for compensation: "))
    targetFile = targetList[selectedTargetIndex - 1]
    ext = targetFile[-4:]
    toolCtrlPts = targetFitSurf.ctrlpts

    if not ext == ".stl":
        toolCtrlPts = Stp2Surf("data/targets/" + targetFile).surfaces[0].ctrlpts

    selectionDict = {1: [measuredMeanCtrlPts, "mean_measured", measuredMeanDiff],
                     2: [measuredMaxCtrlPts, "max_measured", measuredMaxDiff],
                     3: [measuredMedianCtrlPts, "median_measured", measuredMedianDiff],
                     4: [simulatedMeanCtrlPts, "mean_simulated", simMeanDiff],
                     5: [simulatedMaxCtrlPts, "max_simulated", simMaxDiff],
                     6: [simulatedMedianCtrlPts, "median_simulated", simMedianDiff]}

    deviations = selectionDict[selectedSurfaceIndex][2]
    maxDeviation = max(np.abs(deviations))
    selectedSurfaceCtrlpts = selectionDict[selectedSurfaceIndex][0]
    correspondingDiffs = list()
    for controlPoint in targetFitSurf.ctrlpts:
        evalPointIndex = pointcloud.Points(targetFitSurf.evalpts).closestPoint(controlPoint, returnPointId=True)
        correspondingDiffs.append(deviations[evalPointIndex])

    useBeta = input("Use beta function? (y/n) ")
    useNormals = input("Use normals? (y/n) ")

    if useBeta == "y":
        beta = smoothstep_sample(np.abs(np.array(correspondingDiffs)) / maxDeviation, order=5)
    elif useBeta == "n":
        beta = np.ones(len(correspondingDiffs))
    else:
        continue

    if useNormals == "y":
        compCtrlpts, _, _ = compensatecontrolpoints(targetFitSurf.ctrlpts, toolCtrlPts, selectedSurfaceCtrlpts, beta,
                                                    weight=compWeight, normals=True)
    elif useNormals == "n":
        compCtrlpts, _, _ = compensatecontrolpoints(targetFitSurf.ctrlpts, toolCtrlPts, selectedSurfaceCtrlpts, beta,
                                                    weight=compWeight, normals=False)
    else:
        continue

    compSurf = BSpline.Surface()
    compSurf.degree_u = opt_degree_u
    compSurf.degree_v = opt_degree_v
    compSurf.ctrlpts_size_v = opt_numctrlpts_v
    compSurf.ctrlpts_size_u = opt_numctrlpts_u
    compSurf.ctrlpts = compCtrlpts.tolist()
    compSurf.knotvector_v = targetFitSurf.knotvector_v
    compSurf.knotvector_u = targetFitSurf.knotvector_u
    compSurf.delta = 0.01
    compSurf.vis = VisVTK.VisSurface()
    compSurf.render()

    numIteration = int(input("Current Iteration: "))

    weightString = str(compWeight).replace(".", "_")
    exportName = "data/targets/compensatedsurface_" + selectionDict[selectedSurfaceIndex][1] + \
                 "_" + weightString + "_i" + str(numIteration) + ".stp"
    Surf2Stp(compSurf.ctrlpts2d, knotvector_v=compSurf.knotvector_v, knotvector_u=compSurf.knotvector_u,
             degree_u=opt_degree_u, degree_v=opt_degree_v,
             filename=exportName)

    # =======================================================================================================
    # create form comSurf to toolMesh_.stl
    toolmeshTri = tessellate.make_triangle_mesh(compSurf.evalpts, compSurf.sample_size_u,
                                                compSurf.sample_size_v)
    faces = [x.vertex_ids for x in toolmeshTri[1]]
    vertices = [x.data for x in toolmeshTri[0]]
    toolMesh = mesh.Mesh([vertices, faces])

    toolMesh.cutWithBox([-78, 308, -60, 60, -1000, 1000], invert=False)
    msh = mesh.Mesh("test/Blechhalter.stl")

    toolMesh.cutWithMesh(msh)

    toolMesh.write('data/targets/tool_' + selectionDict[selectedSurfaceIndex][1] +
                   "_" + weightString + "_i" + str(numIteration) + '.stl')

    print("Convert to STL done!")
