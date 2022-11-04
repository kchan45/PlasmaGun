"""
Testing code for the oscilloscope (PicoScope)

Written/Modified By: Kimberly Chan
(c) 2022 GREMI, University of Orleans
(c) 2022 Mesbah Lab, University of California, Berkeley
"""

import sys
import argparse
import time
from picosdk.ps2000a import ps2000a as ps
import matplotlib.pyplot as plt

from utils.oscilloscope import Oscilloscope

print('\n--------------------------------')
TEST_STREAMING = False

# Check that the number of arguments is correct
numArg = 2
if len(sys.argv)!=numArg:
	print("Function expects "+str(numArg-1)+" argument(s). Example: 'oscilloscope_test.py 30' measures oscilloscope for 30 seconds")
	raise

loopTime = int(sys.argv[1])

# Create an instance of the oscilloscope
if TEST_STREAMING:
    osc = Oscilloscope(mode='streaming')
else:
    osc = Oscilloscope(mode='block')

# Open the oscilloscope
status = osc.open_device()
print(status)

# set the channels to read from oscilloscope
# up to four channels may be set: A, B, C, D
# you should pass a list of dictionaries for the settings of each channel. The
# dictionary for a channel should contain the following keys:
#   "name": the name of the channel, specified either as a single letter
#           ("A", "B", "C", and/or "D") or with the format "CH_A"
#           (i.e., "CH_A", "CH_B", "CH_C", "CH_D"); this is the minimum required
#           for these dictionaries; if only the name is provided, then pre-defined
#           default settings will be used
#   "enable_status": 0 or 1 indicating whether or not to enable this channel;
#           default: 1
#   "coupling_type": AC or DC, specified using the Enums provided in the ps2000a
#           package; default: ps.PS2000A_COUPLING['PS2000A_DC']
#   "range": the range of the signal, spcified using the Enums provided in the
#           ps2000a package; default ps.PS2000A_RANGE['PS2000_2V']
#   "analog_offset": the offset for the analog reading; default: 0.0
channelA = {"name": "A",
            "enable_status": 1,
            "coupling_type": ps.PS2000A_COUPLING['PS2000A_DC'],
            "range": ps.PS2000A_RANGE['PS2000A_10V'],
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

channels = [channelA]#, channelC]
# channels = [channelA, channelB, channelC, channelD]
# status = osc.set_channels(channels)
# print(status)

# set the buffers for the data read from the oscilloscope
# each of the channels should be set accordingly, if they were specified previously
# you should pass a list of dictionaries for the settings of each channel. The
# dictionary for the buffer of a channel should contain the following keys:
#   "name": the name of the channel, specified either as a single letter
#           ("A", "B", "C", and/or "D") or with the format "CH_A"
#           (i.e., "CH_A", "CH_B", "CH_C", "CH_D"); this is the minimum required
#           for these dictionaries; if only the name is provided, then pre-defined
#           default settings will be used
#   "segment_index" (or "seg_idx"): default: 0
#   "ratio_mode": ratio mode, specified using the Enums provided in the ps2000a
#           package; default: ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_NONE']
bufferA = {"name": "A",
           "segment_index": 0,
           "ratio_mode": ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_NONE'],
           }
bufferB = {"name": "B"}
bufferC = {"name": "C"}
bufferD = {"name": "D"}

buffers = [bufferA]#, bufferC]
# buffers = [bufferA, bufferB, bufferC, bufferD]

# a trigger is defined to capture the specific pulse characteristics of the plasma
trigger = {"enable_status": 1,
           "source": ps.PS2000A_CHANNEL['PS2000A_CHANNEL_A'],
           "threshold": 1024, # in ADC counts
           "direction": ps.PS2000A_THRESHOLD_DIRECTION['PS2000A_RISING'],
           "delay": 0, # in seconds
           "auto_trigger": 200} # in milliseconds


timebase = 8

## ALTERNATIVE: Oscilloscope.initialize_oscilloscope(channels, buffers)
# initialize_oscilloscope sets the channels, buffers and trigger (optional)
if TEST_STREAMING:
    status = osc.initialize_device(channels, buffers)
else:
    status = osc.initialize_device(channels, buffers, trigger=trigger, timebase=timebase)

plt.ion()
tStart = time.time()

while(time.time()-tStart<=loopTime):
    s = time.time()
    if TEST_STREAMING:
        t, ch_datas = osc.collect_data_streaming()
    else:
        t, ch_datas = osc.collect_data_block()
    print(f"time to collect data: {time.time()-s}")
    t = osc.get_time_data()
    for ch_data in ch_datas:
        data = ch_data["data"]
        plt.plot(t, data[:], label=ch_data["name"])

    plt.xlabel('Time (ns)')
    plt.ylabel('Voltage (mV)')
    plt.legend()
    plt.draw()
    plt.pause(1)
    plt.clf()


# stop and close the unit after finished
status = osc.stop_and_close_device()
