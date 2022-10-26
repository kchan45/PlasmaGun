"""
Testing code for the oscilloscope (PicoScope)

Written/Modified By: Kimberly Chan
(c) 2022 GREMI, University of Orleans
(c) 2022 Mesbah Lab, University of California, Berkeley
"""

from picosdk.ps2000a import ps2000a as ps
import matplotlib.pyplot as plt

from ..utils.oscilloscope import Oscilloscope


# Create an instance of the oscilloscope
osc = Oscilloscope()

# Open the oscilloscope
status = osc.open_osc()
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
            "range": ps.PS2000A_RANGE['PS2000A_2V'],
            "analog_offset": 0.0,
            }

channelB = {"name": "B"}
channelC = {"name": "C"}
channelD = {"name": "D"}

channels = [channelA, channelB, channelC, channelD]
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

buffers = [bufferA, bufferB, bufferC, bufferD]
# status = osc.set_data_buffers(buffers)
# print(status)

## ALTERNATIVE: Oscilloscope.initialize_oscilloscope(channels, buffers)
status = osc.initialize_oscilloscope(channels, buffers)







# stop and close the unit after finished
status = osc.stop_and_close_oscilloscope()
print(status)
