import os
import shutil

weight = 0.5
numIteration = 4

disk = 'X'
strategie = 'median'

print("Saving grids_simulated...")
CopyFromDir = f'{disk}:/Modell/tryout-manager/grids_simulated'
SaveDir_grids_simulated = f'{disk}:/Ergebnisse/{strategie}/{str(weight)}/i{str(numIteration)}/grids_simulated'
shutil.copytree(CopyFromDir, SaveDir_grids_simulated)

print("\nSaving deviations...")
SaveDir2 = f'{disk}:/Ergebnisse/{strategie}/{str(weight)}/i{str(numIteration)}'
os.chdir(f'{disk}:/Modell/tryout-manager')
shutil.copy('simulated mean evaluated point deviations.txt', SaveDir2)

print("\nSaving simulated_fit_surf...")
moveFromDir = f'{disk}:/Modell/tryout-manager/simulated_fit_surf'
SaveDir_simulated_fit_surf = f'{disk}:/Ergebnisse/{strategie}/{str(weight)}/i{str(numIteration)}/simulated_fit_surf'
shutil.copytree(moveFromDir, SaveDir_simulated_fit_surf)

print("\nData saved!")
