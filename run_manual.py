

import sys
sys.dont_write_bytecode = True
import numpy as np
from seabreeze.spectrometers import Spectrometer, list_devices
import time
import os
from datetime import datetime
# import asyncio
# # pickle import to save class data
# try:
#     import cPickle as pickle
# except ModuleNotFoundError:
#     import pickle
# import argparse
import pandas as pd
from picosdk.ps2000a import ps2000a as ps

## import user functions
from utils.oscilloscope import Oscilloscope

TEST = False

collect_spec = True
collect_osc = False
samplingTime = 1.0 # sampling time in seconds
n_iterations = 20 # number of sampling iterations
set_v = 5.0 # voltage in Volts
set_freq = 0.2 # frequency in kilohertz
set_flow = 1.0 # flow rate in liters per minute
# addl_notes = "chicken muscle at 5mm distance, 3rd location, original orientation"
addl_notes = "background"

## collect time stamp for data collection
timeStamp = datetime.now().strftime('%Y_%m_%d_%H'+'h%M''m%S'+'s')
print('Timestamp for save files: ', timeStamp)

# set save location
directory = os.getcwd()
saveDir = directory+"/data/"+timeStamp+"/"
if not os.path.exists(saveDir):
	os.makedirs(saveDir, exist_ok=True)
print('\nData will be saved in the following directory:')
print(saveDir)

f = open(saveDir+"notes.txt", 'a')
f.write(f"# Data Timestamp: {timeStamp}\n")
f.write(f"# Input Parameters: Voltage={set_v}V; Frequency={set_freq}kHz; Carrier gas flow rate={set_flow}.\n")
f.write(f"# {addl_notes}\n")

if collect_spec:
    f1 = open(saveDir+timeStamp+"_spectra_data.csv", 'a')
    f1.write(f"# Data Timestamp: {timeStamp}\n")
    f1.write(f"# Input Parameters: Voltage={set_v}V; Frequency={set_freq}kHz; Carrier gas flow rate={set_flow}.\n")
    f1.write(f"# {addl_notes}\n")

if collect_osc:
    f2 = open(saveDir+timeStamp+"_osc_data.csv", 'a')
    f2.write(f"# Data Timestamp: {timeStamp}\n")
    f2.write(f"# Input Parameters: Voltage={set_v}V; Frequency={set_freq}kHz; Carrier gas flow rate={set_flow}.\n")
    f2.write(f"# {addl_notes}\n")

################################################################################
# CONNECT TO DEVICES
################################################################################
# Spectrometer
if collect_spec:
    if TEST:
        pass
    else:
        devices = list_devices()
        print(devices)
        spec = Spectrometer(devices[0])
        spec.integration_time_micros(200000)

# Oscilloscope
if collect_osc:
    osc = Oscilloscope()
    status = osc.open_device()
    # see /test/oscilloscope_test.py for more information on defining the channels
    channelA = {"name": "A",
                "enable_status": 0,
                "coupling_type": ps.PS2000A_COUPLING['PS2000A_DC'],
                "range": ps.PS2000A_RANGE['PS2000A_5V'],
                "analog_offset": 0.0,
                }

    channelB = {"name": "B",
                "enable_status": 1,
                "coupling_type": ps.PS2000A_COUPLING['PS2000A_DC'],
                "range": ps.PS2000A_RANGE['PS2000A_20MV'],
                "analog_offset": 0.0,
                }
    channelC = {"name": "C",
                "enable_status": 1,
                "coupling_type": ps.PS2000A_COUPLING['PS2000A_DC'],
                "range": ps.PS2000A_RANGE['PS2000A_20MV'],
                "analog_offset": 0.0,
                }
    channelD = {"name": "D",
                "enable_status": 1,
                "coupling_type": ps.PS2000A_COUPLING['PS2000A_DC'],
                "range": ps.PS2000A_RANGE['PS2000A_5V'],
                "analog_offset": 0.0,
                }

    channels = [channelA, channelB, channelC]
    # see /test/oscilloscope_test.py for more information on defining the buffers
    bufferA = {"name": "A",
               "segment_index": 0,
               "ratio_mode": ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_NONE'],
               }
    bufferB = {"name": "B"}
    bufferC = {"name": "C"}
    bufferD = {"name": "D"}
    buffers = [bufferA, bufferB, bufferC, bufferD]
    status = osc.initialize_device(channels, buffers)

################################################################################
# PERFORM DATA COLLECTION
################################################################################
# set up containers for data
spec_keys = []
osc_keys = []
spec_list = []
osc_list = []
if collect_spec:
    spec_keys = ["wavelengths", "intensities"]
if collect_osc:
    osc_keys = ["timebase", *[f"{channel['name']}" for channel in channels]]


for i in range(int(n_iterations)):
    startTime = time.time()
    if collect_spec:
        if TEST:
            spec_list.append(np.random.randn(300))
            spec_list.append(np.random.randn(300))
        else:
            spec_list.append(spec.wavelengths())
            spec_list.append(spec.intensities())
    if collect_osc:
        if TEST:
            osc_list.append(np.random.randn(240))
            for ch in channels:
                osc_list.append(np.random.randn(240))
        else:
            t, osc_data = osc.collect_data()


    if i%10 == 0:
        if collect_spec:
            spec_save = np.vstack(spec_list)
            df = pd.DataFrame(spec_save)
            df.to_hdf(saveDir+"data.h5", key="spec", complevel=8)

        if collect_osc:
            osc_save = np.vstack(osc_list)
            df = pd.DataFrame(osc_save)
            df.to_hdf(saveDir+"data.h5", key="osc", complevel=8)

    endTime = time.time()
    runTime = endTime-startTime
    print(f'Total Runtime of Iteration {i} was {runTime:.2f} sec.')
    if runTime < samplingTime:
        pauseTime = samplingTime - runTime
        time.sleep(pauseTime)
        print(f'Pausing for {pauseTime:.2f} sec.')
    elif runTime > samplingTime:
        print('WARNING: Measurement time was greater than sampling time! Data may be inaccurate.')


if collect_spec:
    spec_save = np.vstack(spec_list)
    print(spec_save)
    df = pd.DataFrame(spec_save)
    print(df)
    df.to_csv(f1)
    df.to_hdf(saveDir+"data.h5", key="spec", complevel=8)

if collect_osc:
    osc_save = np.vstack(osc_list)
    df = pd.DataFrame(osc_save)
    print(df)
    df.to_csv(f2)
    df.to_hdf(saveDir+"data.h5", key="osc", complevel=8)

if collect_osc:
    status = osc.stop_and_close_oscilloscope()
