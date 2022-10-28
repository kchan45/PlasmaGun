"""
Test file for connecting to the spectrometer. This file should be run with a
command line argument that specifies the length of measurement time.
i.e.,
python3 spectrometer_test.py 100
runs the measurement for 100 seconds


Written/Modified By: Dogan Gidon, Angelo Bonzanini, Ketong Shao (?), Kimberly Chan
(c) Mesbah Lab, University of California, Berkeley
"""

import sys
import argparse
from seabreeze.spectrometers import Spectrometer, list_devices
import numpy as np
import matplotlib.pyplot as plt
import time
print('\n--------------------------------')

# Check that the number of arguments is correct
numArg = 2
if len(sys.argv)!=numArg:
	print("Function expects "+str(numArg-1)+" argument(s). Example: 'spectrometer_test.py 30' measures spectrometer for 30 seconds")
	exit()

# Parameters
loopTime = int(sys.argv[1])

# Obtain the spectrometer object
devices = list_devices()
print(devices)
spec = Spectrometer(devices[0])
spec.integration_time_micros(200000)

# Generate live plot
plt.ion()

# Start counting the time
tStart = time.time()

# Update the live graph
while(time.time()-tStart<=loopTime):
	wavelengthsPlot = spec.wavelengths()[20:]
	intensityPlot = spec.intensities()[20:]
	totalIntensity = sum(intensityPlot)
	print("Total Intensity = ", totalIntensity)
	plt.plot(wavelengthsPlot,intensityPlot)
	plt.draw()
	plt.pause(1)
	plt.clf()
