# pyhoff

The pyhoff package allows to read and write the most common
Beckhoff and WAGO bus terminals ("Busklemmen") using the bus
coupler ("Busskoppler") BK9000, BK9050, BK9100 or WAGO 750_352
over Ethernet TCP/IP based on ModBus TCP.

It depends on the package pyModbusTCP. This can be installed with:

    pip install pyModbusTCP

It is easy to use as the following example code shows:

```python
from pyhoff import *

#connect to the BK9050 by tcp/ip on default port 502
bus_coupler = ModBusBK9050("172.16.17.1")

#list of all bus terminals connected to the bus coupler
#in the order of the physical arrangement
terminal_list = [KL2404, KL2424, KL9100, KL1104, KL3202,
                 KL4002, KL9188, KL3054, KL3214, KL4004,
                 KL9010]

terminals = bus_coupler.add_bus_terminals(terminal_list)

#Set 1. output of the first bus terminal (KL2404) to hi
terminals[0].write_coil(0, True)

#read the temperature from the 2. channel of the 5. bus
#terminal (KL3202)
t = terminals[4].read_temperature(1)
print(f"t = {t:.1f} °C")

#Set 1. output of the 6. bus terminal (KL4002) to 4.2 V
terminals[5].set_voltage(0, 4.2)

```

The following terminals are implemented:
- KL1104: 4x digital input 24 V
- KL2404: 4x digital output with 500 mA
- KL2424: 4x digital output with 2000 mA
- KL3054: 4x analog input 4...20 mA 12 Bit single-ended
- KL3202: 2x analog input PT100 16 Bit 3-wire
- KL3214: 4x analog input PT100 16 Bit 3-wire
- KL4002: 2x analog output 0...10 V 12 Bit differentiell
- KL4004: 4x analog output 0...10 V 12 Bit differentiell
- Dummy terminals without io functionality: KL9100, KL9183, KL9188

Other analog and digital io-terminals are easy to complement. Pull requests are welcome.