"""
Oscilloscope utilities for the plasma gun setup. The main testing script uses
exactly the ps2000a streaming example.

Inspired by the ps2000a streaming and block read examples at
https://github.com/picotech/picosdk-python-wrappers


Written/Modified By: Kimberly Chan
(c) 2022 GREMI, University of Orleans
(c) 2022 Mesbah Lab, University of California, Berkeley
"""
# PS2000 Series (A API) STREAMING MODE EXAMPLE
# This example demonstrates how to call the ps2000a driver API functions in
# order to open a device, setup 2 channels and collects streamed data (1 buffer)
# This data is then plotted as mV against time in ns.

from enum import Enum
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
    def __init__(self, mode='block', single_buff_size=500, n_buffs=10, pretrigger_size=2000, posttrigger_size=8000):
        # self.super().__init__()

        # initialize the oscilloscope object by:
        # 1) setting up a handle to refer to the device
        # 2) initializing a dict of statuses
        # 3) setting up the capture size of the channels
        self.chandle = ctypes.c_int16()
        self.status = {}
        self.mode = mode
        self.set_capture_size(single_buff_size, n_buffs, pretrigger_size, posttrigger_size)
        self.channels_info = None
        self.buffers_info = None
        self.channel_datas = None
        self.time_data = None

    def open_device(self):
        '''
        short wrapper function to open the device
        Inputs:
        N/A
        Outputs:
        returns the output of the assert_pick_ok function (0 or no output
            corresponds to PICO_OK status)
        '''
        self.status['openunit'] = ps.ps2000aOpenUnit(ctypes.byref(self.chandle), None)
        return assert_pico_ok(self.status['openunit'])

    def set_capture_size(self, single_buff_size, n_buffs, pretrigger_size, posttrigger_size):
        '''
        short helper function to set the capture size of the data buffers when
        collecting data.
        '''
        if self.mode == 'streaming':
            total_buff_size = single_buff_size * n_buffs
            self.single_buff_size = single_buff_size
            self.n_buffs = n_buffs
        elif self.mode == 'block':
            total_buff_size = pretrigger_size + posttrigger_size
            self.pretrigger_size = pretrigger_size
            self.posttrigger_size = posttrigger_size

        self.total_buff_size = total_buff_size
        return

    def set_channels(self, channels):
        '''
        function to set the channels for data collection of the oscilloscope.
        Inputs:
        channels        a list of dictionaries that each correspond to a
                        dictionary of channel information/settings

        Outputs:
        status          the current status dictionary of the Oscilloscope instance
        '''
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
                ch_name = f'CH_{channel["name"]}'
                ch_args.append(Channel[ch_name].value)
                ch_name = channel['name']
            elif len(channel['name']) == 4:
                ch_args.append(Channel[channel['name']].value)
                ch_name = channel['name'][-1]
            else:
                print('Invalid Channel Name!')
                raise

            # add the enabled status, if not provided, use the default (defaults defined above in code)
            if 'enable_status' in channel:
                ch_args.append(channel['enable_status'])
            else:
                ch_args.append(default_enable_status)
                print(f'No enabled status provided, using default: {default_enable_status}.')

            # add the coupling type, if not provided, use the default (defaults defined above in code)
            if 'coupling_type' in channel:
                ch_args.append(channel['coupling_type'])
            else:
                ch_args.append(default_coupling_type)
                print(f'No coupling type provided, using default: {default_coupling_type}.')

            # add the range, if not provided, use the default (defaults defined above in code)
            if 'range' in channel:
                ch_args.append(channel['range'])
            else:
                ch_args.append(default_range)
                print(f'No range provided, using default: {default_range}.')

            # add the analog offset, if not provided, use the default (defaults defined above in code)
            if 'analog_offset' in channel:
                ch_args.append(channel['analog_offset'])
            else:
                ch_args.append(default_analog_offset)
                print(f'No offset provided, using default: {default_analog_offset}.')
            print(ch_args)

            # set the channel connection
            self.status[f'set_ch{ch_name}'] = ps.ps2000aSetChannel(self.chandle, *ch_args)
            assert_pico_ok(self.status[f'set_ch{ch_name}'])

        self.channels_info = channels
        self.channel_datas = [{"name": channel["name"]} for channel in channels]
        # # TODO: add return status
        return self.status

    def set_data_buffers(self, buffers):
        '''
        function to set the data buffers for data collection of the oscilloscope.
        Inputs:
        buffers         a list of dictionaries that each correspond to a
                        dictionary of buffer information/settings

        Outputs:
        status          the current status dictionary of the Oscilloscope instance
        '''
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
            self.buffer_maxes = []
            self.buffer_mins = []
            for buff in buffers:
                buff_args = []
                if len(buff['name']) == 1:
                    ch_name = f'CH_{buff["name"]}'
                    buff_args.append(Channel[ch_name].value)
                    ch_name = buff['name']
                elif len(channel['name']) == 4:
                    buff_args.append(Channel[buff['name']].value)
                    ch_name = buff['name'][-1]
                else:
                    print('Invalid Channel Name!')
                    raise

                # pointer to buffer max
                if self.mode == 'streaming':
                    bufferMax = np.zeros(shape=self.single_buff_size, dtype=np.int16)
                    buff_args.append(bufferMax.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)))
                elif self.mode == 'block':
                    # bufferMax = np.zeros(shape=self.total_buff_size, dtype=np.int16)
                    bufferMax = (ctypes.c_int16 * self.total_buff_size)()
                    buff_args.append(ctypes.byref(bufferMax))
                self.buffer_maxes.append(bufferMax)


                # pointer to buffer min
                if self.mode == 'streaming':
                    bufferMin = np.zeros(shape=self.single_buff_size, dtype=np.int16)
                    buff_args.append(bufferMin.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)))
                elif self.mode == 'block':
                    # bufferMin = np.zeros(shape=self.total_buff_size, dtype=np.int16)
                    bufferMin = (ctypes.c_int16 * self.total_buff_size)()
                    buff_args.append(ctypes.byref(bufferMin))
                self.buffer_mins.append(bufferMin)


                # buffer length
                if self.mode == 'streaming':
                    buff_args.append(self.single_buff_size)
                elif self.mode == 'block':
                    buff_args.append(self.total_buff_size)

                # add the segment index, if not provided, use the default (defaults defined above in code)
                if 'seg_idx' in buff:
                    buff_args.append(buff['seg_idx'])
                elif 'segment_index' in buff:
                    buff_args.append(buff['segment_index'])
                else:
                    buff_args.append(default_segment_idx)
                    print(f'No segment index provided, using default: {default_segment_idx}.')

                # add the ratio mode, if not provided, use the default (defaults defined above in code)
                if 'ratio_mode' in buff:
                    buff_args.append(buff['ratio_mode'])
                else:
                    buff_args.append(default_ratio_mode)
                    print(f'No ratio mode provided, using default: {default_ratio_mode}.')
                print(buff_args)

                self.status[f'setBuffer{ch_name}'] = ps.ps2000aSetDataBuffers(self.chandle, *buff_args)
                assert_pico_ok(self.status[f'setBuffer{ch_name}'])

            self.buffers_info = buffers
            # # TODO: add return status
            return self.status

    def set_trigger(self, trigger):
        '''
        function to set the trigger for data collection of the oscilloscope
        (for use in "block" mode)
        Inputs:
        trigger        a dictionary of trigger information/settings

        Outputs:
        status          the current status dictionary of the Oscilloscope instance
        '''
        default_enable_status = 1
        default_channel = Channel["CH_A"].value
        default_threshold = 1024 # ADC counts
        default_direction = ps.PS2000A_THRESHOLD_DIRECTION['PS2000A_RISING']
        default_delay = 0 # in s
        default_auto_trigger = 500 # in ms

        trigger_args = []

        if 'enable_status' in trigger:
            trigger_args.append(trigger['enable_status'])
        else:
            trigger_args.append(default_enable_status)
            print(f'No enable status provided, using default: {default_enable_status}.')

        if 'source' in trigger:
            trigger_args.append(trigger['source'])
        else:
            trigger_args.append(default_channel)
            print(f'No source provided, using default: {default_channel}.')

        if 'threshold' in trigger:
            trigger_args.append(trigger['threshold'])
        else:
            trigger_args.append(default_threshold)
            print(f'No threshold provided, using default: {default_threshold}.')

        if 'direction' in trigger:
            trigger_args.append(trigger['direction'])
        else:
            trigger_args.append(default_direction)
            print(f'No direction provided, using default: {default_direction}.')

        if 'delay' in trigger:
            trigger_args.append(trigger['delay'])
        else:
            trigger_args.append(default_delay)
            print(f'No delay provided, using default: {default_delay}.')

        if 'auto_trigger' in trigger:
            trigger_args.append(trigger['auto_trigger'])
        else:
            trigger_args.append(default_auto_trigger)
            print(f'No auto trigger time provided, using default: {default_auto_trigger}.')

        self.status['trigger'] = ps.ps2000aSetSimpleTrigger(self.chandle, *trigger_args)

        return self.status

    def set_timebase(self, timebase):
        self.timebase = timebase
        self.timeIntervalns = ctypes.c_float()
        returnedMaxSamples = ctypes.c_int32()
        self.oversample = ctypes.c_int16(0)
        self.status['get_timebase'] = ps.ps2000aGetTimebase2(self.chandle,
                                                             self.timebase,
                                                             self.total_buff_size,
                                                             ctypes.byref(self.timeIntervalns),
                                                             self.oversample,
                                                             ctypes.byref(returnedMaxSamples),
                                                             0,
                                                            )
        print("Time Interval (ns): ", self.timeIntervalns.value)
        assert_pico_ok(self.status['get_timebase'])
        return self.status

    def set_timebase_iterative(self, timebase):

        correct_timebase = False
        self.timebase = timebase
        while not correct_timebase:
            self.timeIntervalns = ctypes.c_float()
            returnedMaxSamples = ctypes.c_int32()
            self.oversample = ctypes.c_int16(0)
            self.status['get_timebase'] = ps.ps2000aGetTimebase2(self.chandle,
                                                                 self.timebase,
                                                                 self.total_buff_size,
                                                                 ctypes.byref(self.timeIntervalns),
                                                                 self.oversample,
                                                                 ctypes.byref(returnedMaxSamples),
                                                                 0,
                                                                )
            print("Time Interval (ns): ", self.timeIntervalns.value)
            assert_pico_ok(self.status['get_timebase'])
            good_time_interval = input("Is the time interval above good? [Y/n]\n")
            correct_timebase = True if good_time_interval in ["Y", "y"] else False
            if not correct_timebase:
                self.timebase = int(input("Press Enter/Return to increment the current timebase\nOR\nEnter a new timebase: \n") or self.timebase+1)

        print(f"Timebase set! The time interval between samples will be {self.timeIntervalns} ns.")

    def initialize_streaming(self):
        '''
        function to start the streaming process; should be called each time you
        want to stream values from the oscilloscope
        '''
        # Begin streaming mode:
        sampleInterval = ctypes.c_int32(250)
        sampleUnits = ps.PS2000A_TIME_UNITS['PS2000A_US']
        # We are not triggering:
        maxPreTriggerSamples = 0
        autoStopOn = 1
        # No downsampling:
        downsampleRatio = 1
        self.status["runStreaming"] = ps.ps2000aRunStreaming(self.chandle,
                                                        ctypes.byref(sampleInterval),
                                                        sampleUnits,
                                                        maxPreTriggerSamples,
                                                        self.total_buff_size,
                                                        autoStopOn,
                                                        downsampleRatio,
                                                        ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_NONE'],
                                                        self.single_buff_size)
        assert_pico_ok(self.status["runStreaming"])

        actualSampleInterval = sampleInterval.value
        actualSampleIntervalNs = actualSampleInterval * 1000

        print("Capturing at sample interval %s ns" % actualSampleIntervalNs)

        # We need a big buffer, not registered with the driver, to keep our complete capture in.
        self.complete_buffers = [np.zeros(shape=self.total_buff_size, dtype=np.int16) for _ in range(len(self.channels_info))]
        self.nextSample = 0
        self.autoStopOuter = False
        self.wasCalledBack = False


        def streaming_callback(handle, noOfSamples, startIndex, overflow, triggerAt, triggered, autoStop, param):
            # global nextSample, autoStopOuter, wasCalledBack
            self.wasCalledBack = True
            destEnd = self.nextSample + noOfSamples
            sourceEnd = startIndex + noOfSamples
            for complete_buffer,buffer_max in zip(self.complete_buffers,self.buffer_maxes):
                complete_buffer[self.nextSample:destEnd] = buffer_max[startIndex:sourceEnd]
            # bufferCompleteA[nextSample:destEnd] = bufferAMax[startIndex:sourceEnd]
            # bufferCompleteB[nextSample:destEnd] = bufferBMax[startIndex:sourceEnd]
            self.nextSample += noOfSamples
            if autoStop:
                self.autoStopOuter = True


        # Convert the python function into a C function pointer.
        self.cFuncPtr = ps.StreamingReadyType(streaming_callback)
        print("done initializing streaming")

        # Create time data
        self.time_data = np.linspace(0, (self.total_buff_size-1) * actualSampleIntervalNs, self.total_buff_size)

    def collect_data_streaming(self):
        '''
        function to collect data acquired through streaming
        Inputs:
        N/A
        Outputs: a tuple of time and channel data
        time_data       the time vector corresponding to the data collection
        channel_data    a list of dictionaries containing the data acquired from
                        a particular channel; each dictionary will contain the
                        name of the channel where data was acquired and the data
                        itself
        '''
        self.initialize_streaming()
        # Fetch data from the driver in a loop, copying it out of the registered buffers and into our complete one.
        while self.nextSample < self.total_buff_size and not self.autoStopOuter:
            self.wasCalledBack = False
            self.status["getStreamingLastestValues"] = ps.ps2000aGetStreamingLatestValues(self.chandle, self.cFuncPtr, None)
            if not self.wasCalledBack:
                # If we weren't called back by the driver, this means no data is ready. Sleep for a short while before trying
                # again.
                time.sleep(0.01)

        print("Done grabbing values.")

        # Find maximum ADC count value
        # handle = chandle
        # pointer to value = ctypes.byref(maxADC)
        maxADC = ctypes.c_int16()
        self.status["maximumValue"] = ps.ps2000aMaximumValue(self.chandle, ctypes.byref(maxADC))
        assert_pico_ok(self.status["maximumValue"])

        # Convert ADC counts data to mV
        for channel_info,channel_data,complete_buffer in zip(self.channels_info,self.channel_datas,self.complete_buffers):
            assert channel_info["name"] == channel_data["name"]
            channel_data["data"] = adc2mV(complete_buffer, channel_info["range"], maxADC)

        return self.time_data, self.channel_datas

    def collect_data_block(self):
        '''
        function to collect data acquired through block collection
        Inputs:
        N/A
        Outputs: a tuple of time and channel data
        time_data       the time vector corresponding to the data collection
        channel_data    a list of dictionaries containing the data acquired from
                        a particular channel; each dictionary will contain the
                        name of the channel where data was acquired and the data
                        itself
        '''

        self.status['run_block'] = ps.ps2000aRunBlock(self.chandle,
                                                      self.pretrigger_size,
                                                      self.posttrigger_size,
                                                      self.timebase,
                                                      self.oversample,
                                                      None, 0, None, None)
        assert_pico_ok(self.status['run_block'])

        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            self.status['is_ready'] = ps.ps2000aIsReady(self.chandle, ctypes.byref(ready))

        self.overflow = ctypes.c_int16()
        self.c_total_samples = ctypes.c_int32(self.total_buff_size)

        self.status['get_values'] = ps.ps2000aGetValues(self.chandle, 0,
                                                        ctypes.byref(self.c_total_samples),
                                                        0, 0, 0,
                                                        ctypes.byref(self.overflow))
        assert_pico_ok(self.status['get_values'])

        maxADC = ctypes.c_int16()
        self.status['maximumValue'] = ps.ps2000aMaximumValue(self.chandle, ctypes.byref(maxADC))
        assert_pico_ok(self.status['maximumValue'])

        # Convert ADC counts data to mV
        for channel_info,channel_data,buffer_max in zip(self.channels_info,self.channel_datas,self.buffer_maxes):
            assert channel_info["name"] == channel_data["name"]
            channel_data["data"] = adc2mV(buffer_max, channel_info["range"], maxADC)

        self.time_data = np.linspace(0,((self.c_total_samples.value)-1)*self.timeIntervalns.value, self.c_total_samples.value)

        return self.time_data, self.channel_datas

    def get_time_data(self):
        '''
        short function to retrieve the time vector of the data
        '''
        return self.time_data

    def initialize_device(self, channels, buffers, trigger={}, timebase=8):
        '''
        all-in-one function wrapper to initialize the device by setting the
        channels at which to acquire data from, the buffers corresponding to
        those channels, and the trigger to start data collection if using
        "block" mode
        '''
        self.status['all_channels_set'] = self.set_channels(channels)
        self.status['all_data_buffers_set'] = self.set_data_buffers(buffers)
        if self.mode == 'block':
            self.set_trigger(trigger)
            self.set_timebase(timebase)
        return self.status

    def plot_data(self):
        '''
        short, simple function to plot the data acquired from the oscilloscope
        '''
        fig, ax = plt.subplots()
        for channel_data in channel_datas:
            ax.plot(self.time_data, channel_data["data"][:], label=channel_data["name"])
        ax.set_xlabel('Time (ns)')
        ax.set_ylabel('Voltage (mV)')
        # plt.show()
        return fig, ax

    def stop_and_close_device(self):
        '''
        wrapper function to stop and close the device
        prints and returns the status dictionary of the particular Oscilloscope
        instance
        '''
        # handle = chandle
        self.status["stop"] = ps.ps2000aStop(self.chandle)
        assert_pico_ok(self.status["stop"])

        # Disconnect the scope
        # handle = chandle
        self.status["close"] = ps.ps2000aCloseUnit(self.chandle)
        assert_pico_ok(self.status["close"])

        # Display status returns
        print(self.status)
        return self.status

if __name__ == "__main__":
    # for troubleshooting streaming mode, run the example script derived from
    # the picosdk-wrapper Github

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
    channel_range = ps.PS2000A_RANGE['PS2000A_10V']
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
    sizeOfOneBuffer = 100
    numBuffersToCapture = 1

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
