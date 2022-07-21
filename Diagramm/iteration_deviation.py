import glob
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

""" 
in tryout.py,

save the "simulated mean evaluated point deviations" after plotting,

use code: np.savetxt("simulated mean evaluated point deviations.txt", simMeanEvalDiffIterations, delimiter=",")
"""
disk = 'X'
alpha = 0.5
strategy = 'median'
# read deviation of iteration 0
Iteration0 = open(
    f'{disk}:/Ergebnisse/i0/simulated mean evaluated point deviations.txt', "r")
lines = Iteration0.readlines()
# print(lines)
# print(len(lines))
Iteration0.close()

# get all *.txt files from all subdirectories

all_files = glob.glob(
    f'{disk}:/Ergebnisse/{strategy}/{str(alpha)}/*/simulated mean evaluated point deviations.txt')

for file in all_files:
    deviation = pd.read_csv(file)
combined_csv = pd.concat([pd.read_csv(f) for f in all_files])
os.chdir(os.path.dirname(__file__))

# merge all txt files into one
combined_csv.to_csv(f"combined_csv_{strategy}_{str(alpha)}.csv", index=False, encoding='utf-8-sig')

# transpose row to column
pd.read_csv(f"combined_csv_{strategy}_{str(alpha)}.csv", header=None).T.to_csv(
    f"combined_csv_{strategy}_{str(alpha)}.csv", header=False, index=False)

# add header
df = pd.read_csv(f"combined_csv_{strategy}_{str(alpha)}.csv", names=["Deviation"])

# adding line of iteration 0
df.loc[-1] = lines
df.index += 1  # shifting index
df.sort_index(inplace=True)

df.to_csv(f"combined_csv_{strategy}_{str(alpha)}.csv")
# print("Data frame")
# print(df)

x, y = np.genfromtxt(f"combined_csv_{strategy}_{str(alpha)}.csv", delimiter=',', unpack=True)
plt.xticks(np.arange(0, len(x), step=1))
plt.plot(x, y, marker='o')
plt.xlabel("iteration")
plt.ylabel("mean deviation")
plt.title(
    f'simulated mean evaluation point deviations of {strategy}_{str(alpha)}')

plt.savefig(f"X:/Modell/tryout-manager/Diagramm/diagramm_{strategy}_{str(alpha)}.png")
plt.show()


plt.close()