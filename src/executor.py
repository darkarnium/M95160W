'''
Provides an executor - responsible for banging data onto and off of the wire -
which is intended to be run in a separate process. This also handles timing
and has been built to use queues to try and reduce clock jitter.

This was lifted from whatabanger with slight modifications.
 '''

import time
import logging
import multiprocessing

from struct import pack
from struct import unpack
from operator import xor
from pyftdi.gpio import GpioController 


class Executor(multiprocessing.Process):
    '''
    Provides an executor - responsible for banging data onto and off of the
    wire - which is intended to be run in a separate process. This also
    handles timing and has been built to use queues to try and reduce clock
    jitter.

    This was lifted from whatabanger with slight modifications.
    '''

    def __init__(self, req, res, clk=0x01, mosi=0x02, miso=0x04, cs=0x08):
        ''' Ensure a logger is setup, and access to the GPIO is possible. '''
        super(Executor, self).__init__()
        self.log = logging.getLogger(__name__)

        # The initial state is everything pulled LOW.
        self.state = 0x0

        # Ensure the work queue is accessible - this is used for the parent
        # to push request to bang onto the wire.
        self._in = req
        self._out = res

        # Defaults are:
        #     Pin D0 - 0x01 - OUT (CLOCK)
        #     Pin D1 - 0x02 - OUT (MOSI)
        #     Pin D2 - 0x04 - OUT (MISO)
        #     Pin D3 - 0x08 - OUT (CHIP SELECT)
        self.clk = clk
        self.miso = miso
        self.mosi = mosi
        self.cs = cs

        # Setup the clock interval. This isn't the cycle time, but half the
        # target cycle time.
        self.clock_interval = 0.001

        # Setup the interface, ensuring that MISO is set to GPIO IN.
        self.gpio = GpioController()
        direction = xor(0xFF, self.miso)
        self.log.debug(
            "Setting up FT2232 for GPIO (%s)",
            "{0:08b}".format(direction)
        )
        self.gpio.open_from_url(
            url='ftdi://0x0403:0x6010/1',
            direction=direction,
        )

        # Set the initial GPIO state.
        self.log.debug("Setting the initial GPIO state to %s", self.state)
        self.gpio.write_port(self.state)

    def _write_bits(self, bits):
        ''' Write bits onto the wire (Master to Target) communication. '''
        self.log.debug("Starting banging bits (%s)", bits)

        for bit in bits:
            # Pull the clock HIGH, and drive CS low.
            self.state |= self.clk
            self.state &= ~self.cs
            self.gpio.write_port(self.state)
            time.sleep(self.clock_interval)

            # Check whether we need to write a HIGH or LOW for the bit to be
            # transmitted (where HIGH is 1).
            if bit == 1:
                self.state |= self.mosi
            else:
                self.state &= ~self.mosi

            # Send data via MOSI on the FALLING-edge of the clock.
            self.state &= ~self.clk
            self.gpio.write_port(self.state)
            time.sleep(self.clock_interval)

        # If there's not a Logic Analyser connected, determining when all
        # data has been sent is a pain. Thus, this.
        self.log.debug("Finished banging bits")

    def _read_bits(self, count):
        ''' Reads N bits from the wire. '''
        self.log.debug("Reading %s bits", count)

        result = []
        for _ in range(count):
            # Data will be banged onto the wire by the target device on the
            # RISING edge.
            self.state |= self.clk
            self.gpio.write_port(self.state)

            # Finally, read the state of MISO to determine the value sent by
            # the target.
            if(self.gpio.read() & self.miso) == self.miso:
                result.append(1)
            else:
                result.append(0)

            # Sleep and then drive the clock LOW to complete the cycle.
            time.sleep(self.clock_interval)
            self.state &= ~self.clk
            self.gpio.write_port(self.state)
            time.sleep(self.clock_interval)

        self.log.debug("Read %s", result)
        return result

    def _write_clock(self):
        ''' 'Write' a clock cycle without sending any data. '''
        # Pull the clock HIGH.
        self.state |= self.clk
        self.gpio.write_port(self.state)
        time.sleep(self.clock_interval)

        # Pull the clock LOW.
        self.state &= ~self.clk
        self.gpio.write_port(self.state)
        time.sleep(self.clock_interval)

    def run(self):
        ''' Run the clock, and bang bits as required. '''
        self.log.info("Bit banger clock and monitor started")
        while True:
            # If there's anything in the queue, bang away.
            if self._in.qsize() > 0:
                self._write_bits(self._in.get())
                result = self._read_bits(2048)
                return result 
            else:
                # If no data is pending send, make sure we still drive the
                # clock.
                self._write_clock()
