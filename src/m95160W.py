''' Attempts to dump an M95160W EEPROM using an FT2232H. '''

import time
import logging
import binascii
import multiprocessing

import executor


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


if __name__ == '__main__':
    main()
