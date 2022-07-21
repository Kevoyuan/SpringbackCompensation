#Locale settings
import locale
# Set to German locale to get comma decimal separater
locale.setlocale(locale.LC_NUMERIC, "de_DE")

import numpy as np
import matplotlib.pyplot as plt
plt.rcdefaults()

# Tell matplotlib to use the locale we set above
plt.rcParams['axes.formatter.use_locale'] = True

# make the figure and axes
fig,ax = plt.subplots(1)

# Some example data
x=np.arange(0,1,0.001)
y= x**5 * (126-420*x+540*x**2-315*x**3+70*x**4)

# plot the data
ax.plot(x,y,'r-')

plt.show()