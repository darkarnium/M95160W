''' Attempts to dump an M95160W EEPROM using an FT2232H. '''

import sys
import time
import logging
import binascii
import multiprocessing

import executor


def bits_to_bytes(data):
    ''' Convert a list of bits to bytes. '''
    result = 0x0

    data.reverse()
    for idx, bit in enumerate(data):
        result |= bit << idx

    return result


def main():
    ''' Attempts to dump an M95160W EEPROM using an FT2232H. '''
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(process)d - [%(levelname)s] %(message)s',
    )
    log = logging.getLogger()

    # NOTE: Enabling debug logging has an impact on clock jitter!
    log.setLevel(logging.DEBUG)

    # We're using queues to communicate with the main execution process - 
    # which is responsible for doing the actual bit banging. This is in
    # order to (hopefully) reduce clock jitter.
    log.debug("Setting up requests queue")
    request = multiprocessing.Queue()
    log.debug("Setting up response queue")
    response = multiprocessing.Queue()
    
    # Kick off the bit banger.
    log.debug("Setting up bit banger")
    banger = executor.Executor(request, response)
    banger.start()

    # Push in a READ message - per page 16 of ST 022580 Rev 8.
    log.info("Sending READ starting from address 0x0000")

    # Start the READ from 0x0000. Per page 23 of ST 022580 Rev 8, if we
    # continue to drive CS low - which we do as part of the banger - then
    # "the internal address register is incremented automatically". This
    # allows us to read the ENTIRE contents of the EEPROM with a "single READ
    # instruction". Just bang in a read, keep CS low, and keep reading until
    # we've had our fill.
    size = 2048
    operation = [0, 0, 0, 0, 0, 0, 1, 1]
    operation.extend([0b0] * 16)
    request.put({
        "bits": operation,
        "size": 2048,
    })

    # ...and fetch the response!
    log.info("Starting read, will output to %s", 'eeprom.bin')
    with open('eeprom.bin', 'wb') as fout:
        read = 0

        while read <= size:
            payload = response.get()
            log.debug(
                "Response from EEPROM was: %s (%s)",
                "{0:08b}".format(bits_to_bytes(payload)),
                "0x{0:04x}".format(bits_to_bytes(payload)),
            )
            read += len(payload)
            fout.write(bits_to_bytes(payload))

    # Done, so write!
    log.info("Read all %s bits of EEPROM!")
    sys.exit(0)


if __name__ == '__main__':
    main()
