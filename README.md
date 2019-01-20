## M95160W

This repository contains an example script to dump M95160W EEPROMs with an
FT2232H and Python.

This code was written to dump the contents of a VW Golf MK5 'Gateway' (J533)
via SOIC-8 test clip. In lieu of a proper write-up of this process, please
see the following Twitter thread for more information:

* https://twitter.com/Darkarnium/status/1086374380555436032

### Usage

1) Connect the candidate M95160W to the FT2232H.
2) Run the tool with `python3 m95160w.py`
3) The contents of the EEPROM should be dumped to `eeprom.bin`.

I'd recommend moving the `eeprom.bin` to another file, running the tool a
second time, and then hashing both files. After both dumps are complete, both
hashes should match. Although not definitative, this process should help to
identify if there was any issues with the READ.

In the event of differing data, there may be a problem with connectivity 
between the FT2232H. A few potential issues have been listed below, although
there are many reasons a failed READ may occur!

1) Are the leads between the IC and FT2232H are too long?
2) Are the leads properly connected to the correct pins with no bridges?

### Connections

See the M95160W and FT2232H datasheets for more information. The code assumes
that 'Interface 1' on the FT2232H is in use. If required, this can be changed
in the `open_from_url` call in `executor.py`.

```
M95160W PIN 1 (CS) -> FT2232H ADBUS3
M95160W PIN 2 (DO) -> FT2232H ADBUS2 (MISO)
M95160W PIN 3 (WP) -> NOT CONNECTED
M95160W PIN 4 (VSS) -> FT2232H GND
M95160W PIN 5 (DI) -> FT2232H ADBUS1 (MOSI)
M95160W PIN 6 (CLK) -> FT2232H ADBUS0
M95160W PIN 7 (HOLD) -> FT2232H 3V3
M95160W PIN 8 (HOLD) -> FT2232H 3V3
```

### References

* [M95160W Datasheet](https://www.st.com/resource/en/datasheet/m95160-r.pdf)
* [FT2232H Datasheet](https://www.ftdichip.com/Support/Documents/DataSheets/Modules/DS_FT2232H_Mini_Module.pdf)
