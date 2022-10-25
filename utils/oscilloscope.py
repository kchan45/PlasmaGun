"""
Oscilloscope utilities for the plasma gun setup.

Inspired by the ps2000a streaming example at
https://github.com/picotech/picosdk-python-wrappers


Written By: Kimberly Chan
(c) 2022 GREMI, University of Orleans
(c) 2022 Mesbah Lab, University of California, Berkeley
"""
# PS2000 Series (A API) STREAMING MODE EXAMPLE
# This example demonstrates how to call the ps2000a driver API functions in
# order to open a device, setup 2 channels and collects streamed data (1 buffer)
# This data is then plotted as mV against time in ns.

import ctypes
import numpy as np
from picosdk.ps2000a import ps2000a as ps
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, assert_pico_ok
import time

class Channel(Enum):
    CH_A = ps.PS2000A_CHANNEL['PS2000A_CHANNEL_A']
    CH_B = ps.PS2000A_CHANNEL['PS2000A_CHANNEL_B']
    CH_C = ps.PS2000A_CHANNEL['PS2000A_CHANNEL_C']
    CH_D = ps.PS2000A_CHANNEL['PS2000A_CHANNEL_D']

class Oscilloscope():
    """
    The class Oscilloscope defines a custom object that is used to connect to a
    2000a series oscilloscope from PicoTech for the plasma gun setup.
    """
    def __init__(self, single_buff_size=500, n_buffs=10):
        super(self).__init__()

        # initialize the oscilloscope object by:
        # 1) setting up a handle to refer to the device
        # 2) initializing a dict of statuses
        # 3) setting up the capture size of the channels
        self.chandle = ctypes.c_int16()
        self.status = {}
        self.set_capture_size(single_buff_size=single_buff_size, n_buffs=n_buffs)

    def open_osc(self):
        self.status['openunit'] = ps.ps2000aOpenUnit(ctypes.byref(self.chandle), None)
        return assert_pico_ok(self.status['openunit'])

    def set_channels(self, channels):

        # set defaults in case not provided
        default_enable_status = 1
        default_coupling_type = ps.PS2000A_COUPLING['PS2000A_DC']
        default_channel_range = ps.PS2000A_RANGE['PS2000A_2V']
        default_analog_offset = 0.0

        for channel in channels:
            # construct the channel arguments from the input dictionary
            ch_args = []

            # the channel name can be provided in two ways,
            # 1) as a single character denoting the channel, e.g., A, B, C, D
            # 2) as the name within the Enum defined above, e.g., CH_A, CH_B, etc
            # otherwise, throw an error
            if len(channel['name']) == 1:
                ch_name = f'CH_{channel['name']}'
                ch_args.append(Color[ch_name].value)
                ch_name = channel['name']
            elif len(channel['name']) == 4:
                ch_args.append(Color[channel['name']].value)
                ch_name = channel['name'][-1]
            else:
                print('Invalid Channel Name!')
                raise

            # add the enabled status, if not provided, use the default (defaults defined above in code)
            if 'enable_status' in channel:
                ch_args.append(channel['enable_status'])
            else:
                print(f'No enabled status provided, using default: {default_enable_status}.')

            # add the coupling type, if not provided, use the default (defaults defined above in code)
            if 'coupling_type' in channel:
                ch_args.append(channel['coupling_type'])
            else:
                print(f'No coupling type provided, using default: {default_coupling_type}.')

            # add the range, if not provided, use the default (defaults defined above in code)
            if 'range' in channel:
                ch_args.append(channel['range'])
            else:
                print(f'No range provided, using default: {default_range}.')

            # add the analog offset, if not provided, use the default (defaults defined above in code)
            if 'analog_offset' in channel:
                ch_args.append(channel['analog_offset'])
            else:
                print(f'No offset provided, using default: {default_analog_offset}.')
            print(ch_args)

            # set the channel connection
            self.status[f'set_ch{ch_name}'] = ps.ps2000aSetChannel(self.chandle, *[ch_args])
            assert_pico_ok(status[f'set_ch{ch_name}'])

        self.channels_info = channels
        # # TODO: add return status
        return

    def set_capture_size(self, single_buff_size=500, n_buffs=10):

        total_buff_size = single_buff_size * n_buffs

        self.single_buff_size = single_buff_size
        self.n_buffs = n_buffs
        self.total_buff_size = total_buff_size
        return

    def set_data_buffers(self, buffers):

        if self.channels_info is None:
            print('Channels not set!')
            raise

        channels = self.channels_info
        if len(buffers) < len(channels):
            print('Not enough buffers provided for the opened channels.')
            raise
        elif len(buffers) > len(channels):
            print('Too many buffers provided for the opened channels.')
            raise
        else:
            default_segment_idx = 0
            default_ratio_mode = ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_NONE']
            for buff in zip(buffers):
                buff_args = []
                if len(buff['name']) == 1:
                    ch_name = f'CH_{buff['name']}'
                    buff_args.append(Color[ch_name].value)
                    ch_name = buff['name']
                elif len(channel['name']) == 4:
                    buff_args.append(Color[buff['name']].value)
                    ch_name = buff['name'][-1]
                else:
                    print('Invalid Channel Name!')
                    raise

            # pointer to buffer max
            bufferMax = np.zeros(shape=self.single_buff_size, dtype=np.int16)
            buff_args.append(bufferMax.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)))

            # pointer to buffer min
            buff_args.append(None)

            # buffer length
            buff_args.append(self.single_buff_size)

            # add the segment index, if not provided, use the default (defaults defined above in code)
            if 'seg_idx' in buff:
                buff_args.append(buff['seg_idx'])
            elif 'segment_index' in buff:
                buff_args.append(buff['segment_index'])
            else:
                print(f'No segment index provided, using default: {default_segment_idx}.')

            # add the ratio mode, if not provided, use the default (defaults defined above in code)
            if 'ratio_mode' in buff:
                buff_args.append(buff['ratio_mode'])
            else:
                print(f'No ratio mode provided, using default: {default_ratio_mode}.')
            print(buff_args)

            self.status[f'setBuffer{ch_name}'] = ps.ps2000aSetDataBuffers(self.chandle, *buff_args)
            assert_pico_ok(self.status[f'setBuffer{ch_name}'])

            self.buffers_info = buffers
            # # TODO: add return status
            return

    def initialize_oscilloscope(self, channels, buffers):
        self.status['all_channels_set'] = self.set_channels(channels)
        self.status['all_data_buffers_set'] = self.set_data_buffers(buffers)
        return self.status

if __name__ == "__main__":
    # for troubleshooting, run the example script

    # Create chandle and status:
    # chandle keeps track of the connected device
    # status is a dictionary of statuses obtained over the connection to the device
    chandle = ctypes.c_int16()
    status = {}

    # Open PicoScope 2000a Series device
    # Returns handle to chandle for use in future API functions
    status["openunit"] = ps.ps2000aOpenUnit(ctypes.byref(chandle), None)
    assert_pico_ok(status["openunit"])


    enabled = 1
    disabled = 0
    analogue_offset = 0.0

    # Set up channel A
    # handle = chandle
    # channel = PS2000A_CHANNEL_A = 0
    # enabled = 1
    # coupling type = PS2000A_DC = 1
    # range = PS2000A_2V = 7
    # analogue offset = 0 V
    channel_range = ps.PS2000A_RANGE['PS2000A_2V']
    status["setChA"] = ps.ps2000aSetChannel(chandle,
                                            ps.PS2000A_CHANNEL['PS2000A_CHANNEL_A'],
                                            enabled,
                                            ps.PS2000A_COUPLING['PS2000A_DC'],
                                            channel_range,
                                            analogue_offset)
    assert_pico_ok(status["setChA"])

    # Set up channel B
    # handle = chandle
    # channel = PS2000A_CHANNEL_B = 1
    # enabled = 1
    # coupling type = PS2000A_DC = 1
    # range = PS2000A_2V = 7
    # analogue offset = 0 V
    status["setChB"] = ps.ps2000aSetChannel(chandle,
                                            ps.PS2000A_CHANNEL['PS2000A_CHANNEL_B'],
                                            enabled,
                                            ps.PS2000A_COUPLING['PS2000A_DC'],
                                            channel_range,
                                            analogue_offset)
    assert_pico_ok(status["setChB"])

    # Size of capture
    sizeOfOneBuffer = 500
    numBuffersToCapture = 10

    totalSamples = sizeOfOneBuffer * numBuffersToCapture

    # Create buffers ready for assigning pointers for data collection
    bufferAMax = np.zeros(shape=sizeOfOneBuffer, dtype=np.int16)
    bufferBMax = np.zeros(shape=sizeOfOneBuffer, dtype=np.int16)

    memory_segment = 0

    # Set data buffer location for data collection from channel A
    # handle = chandle
    # source = PS2000A_CHANNEL_A = 0
    # pointer to buffer max = ctypes.byref(bufferAMax)
    # pointer to buffer min = ctypes.byref(bufferAMin)
    # buffer length = maxSamples
    # segment index = 0
    # ratio mode = PS2000A_RATIO_MODE_NONE = 0
    status["setDataBuffersA"] = ps.ps2000aSetDataBuffers(chandle,
                                                         ps.PS2000A_CHANNEL['PS2000A_CHANNEL_A'],
                                                         bufferAMax.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
                                                         None,
                                                         sizeOfOneBuffer,
                                                         memory_segment,
                                                         ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_NONE'])
    assert_pico_ok(status["setDataBuffersA"])

    # Set data buffer location for data collection from channel B
    # handle = chandle
    # source = PS2000A_CHANNEL_B = 1
    # pointer to buffer max = ctypes.byref(bufferBMax)
    # pointer to buffer min = ctypes.byref(bufferBMin)
    # buffer length = maxSamples
    # segment index = 0
    # ratio mode = PS2000A_RATIO_MODE_NONE = 0
    status["setDataBuffersB"] = ps.ps2000aSetDataBuffers(chandle,
                                                         ps.PS2000A_CHANNEL['PS2000A_CHANNEL_B'],
                                                         bufferBMax.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
                                                         None,
                                                         sizeOfOneBuffer,
                                                         memory_segment,
                                                         ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_NONE'])
    assert_pico_ok(status["setDataBuffersB"])

    # Begin streaming mode:
    sampleInterval = ctypes.c_int32(250)
    sampleUnits = ps.PS2000A_TIME_UNITS['PS2000A_US']
    # We are not triggering:
    maxPreTriggerSamples = 0
    autoStopOn = 1
    # No downsampling:
    downsampleRatio = 1
    status["runStreaming"] = ps.ps2000aRunStreaming(chandle,
                                                    ctypes.byref(sampleInterval),
                                                    sampleUnits,
                                                    maxPreTriggerSamples,
                                                    totalSamples,
                                                    autoStopOn,
                                                    downsampleRatio,
                                                    ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_NONE'],
                                                    sizeOfOneBuffer)
    assert_pico_ok(status["runStreaming"])

    actualSampleInterval = sampleInterval.value
    actualSampleIntervalNs = actualSampleInterval * 1000

    print("Capturing at sample interval %s ns" % actualSampleIntervalNs)

    # We need a big buffer, not registered with the driver, to keep our complete capture in.
    bufferCompleteA = np.zeros(shape=totalSamples, dtype=np.int16)
    bufferCompleteB = np.zeros(shape=totalSamples, dtype=np.int16)
    nextSample = 0
    autoStopOuter = False
    wasCalledBack = False


    def streaming_callback(handle, noOfSamples, startIndex, overflow, triggerAt, triggered, autoStop, param):
        global nextSample, autoStopOuter, wasCalledBack
        wasCalledBack = True
        destEnd = nextSample + noOfSamples
        sourceEnd = startIndex + noOfSamples
        bufferCompleteA[nextSample:destEnd] = bufferAMax[startIndex:sourceEnd]
        bufferCompleteB[nextSample:destEnd] = bufferBMax[startIndex:sourceEnd]
        nextSample += noOfSamples
        if autoStop:
            autoStopOuter = True


    # Convert the python function into a C function pointer.
    cFuncPtr = ps.StreamingReadyType(streaming_callback)

    # Fetch data from the driver in a loop, copying it out of the registered buffers and into our complete one.
    while nextSample < totalSamples and not autoStopOuter:
        wasCalledBack = False
        status["getStreamingLastestValues"] = ps.ps2000aGetStreamingLatestValues(chandle, cFuncPtr, None)
        if not wasCalledBack:
            # If we weren't called back by the driver, this means no data is ready. Sleep for a short while before trying
            # again.
            time.sleep(0.01)

    print("Done grabbing values.")

    # Find maximum ADC count value
    # handle = chandle
    # pointer to value = ctypes.byref(maxADC)
    maxADC = ctypes.c_int16()
    status["maximumValue"] = ps.ps2000aMaximumValue(chandle, ctypes.byref(maxADC))
    assert_pico_ok(status["maximumValue"])

    # Convert ADC counts data to mV
    adc2mVChAMax = adc2mV(bufferCompleteA, channel_range, maxADC)
    adc2mVChBMax = adc2mV(bufferCompleteB, channel_range, maxADC)

    # Create time data
    time = np.linspace(0, (totalSamples-1) * actualSampleIntervalNs, totalSamples)

    # Plot data from channel A and B
    plt.plot(time, adc2mVChAMax[:])
    plt.plot(time, adc2mVChBMax[:])
    plt.xlabel('Time (ns)')
    plt.ylabel('Voltage (mV)')
    plt.show()

    # Stop the scope
    # handle = chandle
    status["stop"] = ps.ps2000aStop(chandle)
    assert_pico_ok(status["stop"])

    # Disconnect the scope
    # handle = chandle
    status["close"] = ps.ps2000aCloseUnit(chandle)
    assert_pico_ok(status["close"])

    # Display status returns
    print(status)
