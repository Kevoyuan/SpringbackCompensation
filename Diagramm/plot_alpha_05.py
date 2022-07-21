import numpy as np
import matplotlib.pyplot as plt

import pandas as pd
from matplotlib.ticker import MaxNLocator
from pyparsing import alphas



# deviation = pd.read_csv(r"X:/Modell/tryout-manager/Diagramm/alpha_05.csv")


data_list = []
# col_names = ["Iteration", "Deviation"]
data_array = pd.read_csv("alpha_05.csv", index_col=None
                             )
data_list.append(data_array)



fig = plt.figure()

# x = np.arange(5)

print(data_list[0])
xdata = []
ydata = []
xdata = data.ix[:,'列名1']   #将csv中列名为“列名1”的列存入xdata数组中
							#如果ix报错请将其改为loc
ydata = data.ix[:,'列名2']   #将csv中列名为“列名2”的列存入ydata数组中



# y_max_0_5 = data_list[0]
# y_mean_0_5 = data_list[1]
# y_median_0_5 = data_list[2]

# plt.plot(x, y_mean_0_5, label="mean_0,5", marker='o')
# plt.plot(x, y_median_0_5, label="median_0,5", marker='o')
# plt.plot(x, y_max_0_5, label="max_0,5", marker='o')


# plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
# plt.xlabel("Iteration")
# plt.ylabel("Abweichung")
# plt.title('gemittelte evaluierte Punktabweichung')
# plt.legend()
# plt.savefig(f"alpha_0,5.svg")
# plt.show()

