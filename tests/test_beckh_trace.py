import pyhoff as pyhoff
from typing import Type
from pyhoff.devices import KL2404, KL2424, KL9100, KL1104, \
    KL9188, KL3054, KL3214, KL4004, KL9010, BK9050


def test_against_old_traces():
    """
    Test modbus tcp byte streams against data from an old
    known good implementation for some Beckhoff terminals.
    """

    debug_data: list[str] = list()

    # dummy modbus send function
    def debug_send_dummy(data: bytes) -> int:
        print(f"-> Send:     {' '.join(hex(b) for b in data)}")
        for b in data:
            debug_data.append(f"{b:02X}")
        return len(data)

    terminals_list: list[Type[pyhoff.BusTerminal]] = [KL2404, KL2424, KL2424, KL2424, KL9100, KL1104,
                                                      KL1104, KL2404, KL9188, KL3054, KL3054, KL3214,
                                                      KL3214, KL3214, KL4004, KL4004, KL9010]

    bk = BK9050("localhost", 11255, timeout=0.001)

    # injecting debug function
    bk.modbus._send = debug_send_dummy  # type: ignore

    bts = bk.add_bus_terminals(terminals_list)

    terminal1 = bts[15]
    assert isinstance(terminal1, KL4004)
    ref_data = ['86', 'E2', '00', '00', '00', '06', '01', '06', '08', '35', '71', 'A9']
    debug_data.clear()
    terminal1.set_voltage(3, 8.88)
    assert debug_data[2:] == ref_data[2:], print('test:' + ' '.join(debug_data) + '\nref: ' + ' '.join(ref_data) + '\n')

    terminal2 = bts[13]
    assert isinstance(terminal2, KL3214)
    ref_data = ['8B', '18', '00', '00', '00', '06', '01', '04', '00', '25', '00', '01']
    debug_data.clear()
    terminal2.read_temperature(3)
    assert debug_data[2:] == ref_data[2:], print('test:' + ' '.join(debug_data) + '\nref: ' + ' '.join(ref_data) + '\n')

    ref_data = ['08', 'F8', '00', '00', '00', '06', '01', '04', '00', '27', '00', '01']
    debug_data.clear()
    terminal2.read_temperature(4)
    assert debug_data[2:] == ref_data[2:], print('test:' + ' '.join(debug_data) + '\nref: ' + ' '.join(ref_data) + '\n')

    terminal3 = bts[7]
    assert isinstance(terminal3, KL2404)
    ref_data = ['80', '8F', '00', '00', '00', '06', '01', '05', '00', '12', 'FF', '00']
    debug_data.clear()
    terminal3.write_coil(3, True)
    assert debug_data[2:] == ref_data[2:], print('test:' + ' '.join(debug_data) + '\nref: ' + ' '.join(ref_data) + '\n')

    ref_data = ['23', '96', '00', '00', '00', '06', '01', '01', '00', '13', '00', '01']
    debug_data.clear()
    terminal3.read_coil(4)
    assert debug_data[2:] == ref_data[2:], print('test:' + ' '.join(debug_data) + '\nref: ' + ' '.join(ref_data) + '\n')


if __name__ == '__main__':
    test_against_old_traces()
