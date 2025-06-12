# Pyhoff

The pyhoff package allows you to read and write the most common
Beckhoff and WAGO bus terminals ("Busklemmen") using the Ethernet bus
coupler ("Busskoppler") BK9000, BK9050, BK9100, or WAGO 750_352
over Ethernet TCP/IP based on ModBus TCP.

### Key Features
- Supports a wide range of Beckhoff and WAGO analog and digital bus
  terminals.
- Very lightweight: no dependencies; compact code base
- Easy to extend
- Using standardized ModBus TCP.
- Provides high-level abstractions for reading and writing data
  from/to IO-terminals with minimal code

### Usage Scenarios
- Industrial test setups.
- Research automation setups.
- Data acquisition and monitoring.

## Installation
The package has no additional decencies. It can be installed with pip:

```bash
pip install pyhoff
```

## Usage
It is easy to use as the following example code shows:

```python
from pyhoff.devices import *

# connect to the BK9050 by tcp/ip on default port 502
bk = BK9050("172.16.17.1")

# add all bus terminals connected to the bus coupler
# in the order of the physical arrangement
bk.add_bus_terminals(KL2404, KL2424, KL9100, KL1104, KL3202,
                     KL3202, KL4002, KL9188, KL3054, KL3214,
                     KL4004, KL9010)

# Set 1. output of the first KL2404-type bus terminal to hi
bk.select(KL2404, 0).write_coil(1, True)

# read temperature from the 2. channel of the 2. KL3202-type
# bus terminal
t = bk.select(KL3202, 1).read_temperature(2)
print(f"t = {t:.1f} °C")

# Set 1. output of the 1. KL4002-type bus terminal to 4.2 V
bk.select(KL4002, 0).set_voltage(1, 4.2)

```

## Contributing
Other analog and digital IO terminals are easy to complement. Contributions are welcome!
Please open an issue or submit a pull request on GitHub.

## Developer Guide
To get started with developing the `pyhoff` package, follow these steps:

1. First, clone the repository to your local machine using Git:
   ```bash
   git clone https://github.com/Nonannet/pyhoff.git
   cd pyhoff
   ```

2. It is recommended to use a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows/Powershell use `.\venv\Scripts\Activate.ps1`
   ```

3. Install pyhoff from source plus the development dependencies:
   ```bash
   pip install -e .[dev]
   ```

4. Ensure that everything is set up correctly by running the tests:
   ```bash
   pytest
   ```
   
## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.