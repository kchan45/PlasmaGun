

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

collect_spec = True
collect_osc = False

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

################################################################################
# CONNECT TO DEVICES
################################################################################
# Spectrometer
if collect_spec:
	devices = list_devices()
	print(devices)
	spec = Spectrometer(devices[0])
	spec.integration_time_micros(200000)

# Oscilloscope
# if collect_osc:
# osc = Oscilloscope()
# # status = osc.open_osc()
# # see /test/oscilloscope_test.py for more information on defining the channels
# channelA = {"name": "A",
#             "enable_status": 0,
#             "coupling_type": ps.PS2000A_COUPLING['PS2000A_DC'],
#             "range": ps.PS2000A_RANGE['PS2000A_5V'],
#             "analog_offset": 0.0,
#             }
#
# channelB = {"name": "B",
#             "enable_status": 1,
#             "coupling_type": ps.PS2000A_COUPLING['PS2000A_DC'],
#             "range": ps.PS2000A_RANGE['PS2000A_20MV'],
#             "analog_offset": 0.0,
#             }
# channelC = {"name": "C",
#             "enable_status": 1,
#             "coupling_type": ps.PS2000A_COUPLING['PS2000A_DC'],
#             "range": ps.PS2000A_RANGE['PS2000A_20MV'],
#             "analog_offset": 0.0,
#             }
# channelD = {"name": "D",
#             "enable_status": 1,
#             "coupling_type": ps.PS2000A_COUPLING['PS2000A_DC'],
#             "range": ps.PS2000A_RANGE['PS2000A_5V'],
#             "analog_offset": 0.0,
#             }
#
# channels = [channelA, channelC]
# # see /test/oscilloscope_test.py for more information on defining the buffers
# bufferA = {"name": "A",
#            "segment_index": 0,
#            "ratio_mode": ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_NONE'],
#            }
# bufferB = {"name": "B"}
# bufferC = {"name": "C"}
# bufferD = {"name": "D"}
# buffers = [bufferA, bufferB, bufferC, bufferD]
# # status = osc.initialize_oscilloscope(channels, buffers)

################################################################################
# PERFORM DATA COLLECTION
################################################################################
# set up containers for data
samp_time = np.arange(100)
data_names = np.array([*["wavelengths", "intensities"]])#, "timebase"], *[f"{channel['name']}" for channel in channels]])
samp_time = np.repeat(samp_time, len(data_names))
print(data_names)
data_names = np.tile(data_names,100)
arrays = [samp_time,data_names]

d_list = []
for i in range(100):
    d = {}
    d["intensities"] = spec.intensities()
    d["wavelengths"] = spec.wavelengths()
    # d["timebase"] = np.random.randn(240)
    # for ch in channels:
    #     d[f'{ch["name"]}'] = np.random.randn(240)
    d_list.append(d)
    # osc_list = [l.append(np.random.randn(240)) for l in osc_list]
    # osc_list.append([np.random.randn(240) for _ in channels])

    # intensity = spec.intensities()
    # wavelength = spec.wavelengths()

    # t, osc_data = osc.collect_data()

    # if i%10 == 0:
    #     current_df = pd.DataFrame([])
    #     global_df = pd.DataFrame


df = pd.DataFrame(d_list)
print(df)

df.to_csv(saveDir+"data_csv")







# status = osc.stop_and_close_oscilloscope()
