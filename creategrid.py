import pymeshlab
from mesh2grid import Mesh2Grid
import trimesh
from vedo import mesh
import os
from rich.console import Console
from rich.progress import track

console = Console(color_system='256', style=None)


def CreateGrid(targetFileName, sourcePath, simulated, exportFolder):
    """
    :param str targetFileName: path of target file (ex. "data/targets/3DS_target_mesh.stl")
    :param str sourcePath: path of source files of current iteration (ex. "data/Simulation/i1")
    :param int simulated: True if data is simulated, False if data is measured
    :param str exportFolder: name of the file that grid points are exported to (ex. "grids_simulated/i1")
    """
    TARGETFILE = targetFileName
    trimesh.tol.merge = 1e-7

    sourceFiles = [sourcePath + "/" + fileName for fileName in os.listdir(sourcePath)]

    # load target mesh
    targetVedo = mesh.Mesh(TARGETFILE)
    targetVedo.cutWithBox([-76, 307, -71, 65, -1000, 1000], invert=False)
    targetVedo.cutWithCylinder([170, 375, 0], r=330, axis='z', invert=True)
    targetVedo.cutWithCylinder([148, -280, 0], r=224, axis='z', invert=True)
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
    print('target mesh loaded')

    index = 1
    for sourceFile in track(sourceFiles, description="[blue] creatgrid working"):
        exportFileName = 'mesh_ausgerichtet/mesh_ausgerichtet' + str(index) + ".stl"

        sourceMesh = mesh.Mesh(sourceFile)
        print(f'{index}th mesh loaded')
        if simulated:
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
            transformationMatrix, _ = trimesh.registration.mesh_other(sourceTrimesh, targetMesh, samples=1000)
            sourceTrimesh.apply_transform(transformationMatrix)

            sourceVedo = mesh.Mesh([sourceTrimesh.vertices, sourceTrimesh.faces])

            sourceVedoBack = sourceVedo.cutWithBox([-78, 40, -71, 65, -50, 1000], invert=False)

            sourceTrimeshBack = sourceVedoBack.to_trimesh()
            transformationMatrix, _ = trimesh.registration.mesh_other(sourceTrimeshBack, targetMeshBack, icp_final=500,
                                                                      samples=1000)
            sourceTrimesh.apply_transform(transformationMatrix)
            print('back mesh aligned')

            sourceVedo = mesh.Mesh([sourceTrimesh.vertices, sourceTrimesh.faces])

            sourceVedoFront = sourceVedo.cutWithBox([220, 290, -71, 65, -50, 1000], invert=False)
            sourceTrimeshFront = sourceVedoFront.to_trimesh()
            transformationMatrix, _ = trimesh.registration.mesh_other(sourceTrimeshFront, targetMeshFront,
                                                                      icp_final=500,
                                                                      samples=1000)
            sourceTrimesh.apply_transform(transformationMatrix)
            print('front mesh aligned')

            sourceTrimesh.export(exportFileName)
        elif not simulated:
            sourceTrimesh = trimesh.load(sourceFile)
            sourceTrimesh.merge_vertices()
            trimesh.smoothing.filter_taubin(sourceTrimesh)
            transformationMatrix, _ = trimesh.registration.mesh_other(sourceTrimesh, targetMesh, samples=1000)
            sourceTrimesh.apply_transform(transformationMatrix)

            sourceVedo = mesh.Mesh([sourceTrimesh.vertices, sourceTrimesh.faces])

            sourceVedoBack = sourceVedo.cutWithBox([-78, 0, -71, 65, -50, 1000], invert=False)
            sourceTrimeshBack = sourceVedoBack.to_trimesh()
            transformationMatrix, _ = trimesh.registration.mesh_other(sourceTrimeshBack, targetMeshBack, icp_final=500,
                                                                      samples=1000)
            sourceTrimesh.apply_transform(transformationMatrix)
            sourceTrimesh.export(exportFileName)
        
        alignedMesh = mesh.Mesh(exportFileName)
        # alignedMesh.cutWithBox([-78, 308, -71, 65, -1000, 1000], invert=False)
        #
        # alignedMesh.cutWithBox([-78, 308, -65, 60, -1000, 1000], invert=False)
        # alignedMesh.cutWithCylinder([160, 255, 0], r=205, axis='z', invert=True)
        # alignedMesh.cutWithBox([160, 308, 50, 60, -1000, 1000], invert=True)

        alignedMesh.cutWithBox([-76, 307, -65, 63, -1000, 1000], invert=False)
        alignedMesh.cutWithCylinder([175, 382, 0], r=335, axis='z', invert=True)
        alignedMesh.cutWithCylinder([148, -318, 0], r=260, axis='z', invert=True)
        alignedMesh.cutWithBox([170, 320, 47, 75, -1000, 1000], invert=True)
        alignedMesh.cutWithBox([155, 310, -75, -58, -1000, 1000], invert=True)
        # msh = mesh.Mesh("test/Blechhalter.stl")
        # alignedMesh.cutWithMesh(msh)
        alignedMesh.fillHoles()

        mesh2grid = Mesh2Grid(alignedMesh, 3, 5)
        mesh2grid.creategrid(5, exportFolder + "/gridpoints" + str(index))
        index = index + 1
