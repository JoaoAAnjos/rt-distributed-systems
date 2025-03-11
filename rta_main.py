import numpy as np
import sys

import exercise as ex

data = np.loadtxt(sys.argv[1], delimiter=",", skiprows=1,usecols=range(1, 6))
ex.run_RTA(data)

