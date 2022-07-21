import matplotlib.pyplot as plt
import pandas as pd
import glob
import os
import numpy as np
from matplotlib.ticker import MaxNLocator
from pyparsing import alphas

path = r'X:/Modell/tryout-manager/Diagramm'  # use your path
all_files = glob.glob(os.path.join(path, "*.csv"))

alpha = 0.8
alpha_str = f'0,{int(alpha*10)}'

data_list = []
col_names = ["Iteration", "Deviation"]

for filename in all_files:
    data_array = pd.read_csv(filename, index_col=None,
                             header=0, names=col_names)
    data_list.append(data_array)
fig = plt.figure()


if alpha == 0.8:
    x = np.arange(4)

    y_max_0_8 = data_list[1]["Deviation"]
    y_mean_0_8 = data_list[3]["Deviation"]
    y_median_0_8 = data_list[5]["Deviation"]

    plt.plot(x, y_mean_0_8, label="mean_0,8", marker='o')
    plt.plot(x, y_median_0_8, label="median_0,8", marker='o')
    plt.plot(x, y_max_0_8, label="max_0,8", marker='o')

elif alpha == 0.5:
    x = np.arange(5)

    y_max_0_5 = data_list[0]["Deviation"]
    y_mean_0_5 = data_list[2]["Deviation"]
    y_median_0_5 = data_list[4]["Deviation"]

    plt.plot(x, y_mean_0_5, label="mean_0,5", marker='o')
    plt.plot(x, y_median_0_5, label="median_0,5", marker='o')
    plt.plot(x, y_max_0_5, label="max_0,5", marker='o')


plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
plt.xlabel("Iteration")
plt.ylabel("Abweichung")
plt.title('gemittelte evaluierte Punktabweichung')
plt.legend()
plt.savefig(f"alpha = {alpha_str}.svg")
plt.show()
# frame = pd.concat(data_list, axis=0, ignore_index=True)
