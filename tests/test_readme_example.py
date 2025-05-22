from pyhoff.devices import KL2404, KL2424, KL9100, KL1104, \
    KL3202, KL4002, KL9188, KL3054, KL3214, KL4004, KL9010, BK9050


def test_readme_example():
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
