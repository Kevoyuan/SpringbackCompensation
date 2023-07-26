import os

path = 'X:\Ergebnisse\mean\mean_0.3\i3\grids_simulated\i3'
files = os.listdir(path)

index = 17
for index, file in enumerate(files):
    # print (file)
    os.rename(os.path.join(path, file), os.path.join(path, 'gridpoints' + str(index)))
