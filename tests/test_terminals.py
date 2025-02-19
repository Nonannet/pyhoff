import inspect
import pyhoff as pyhoff
import pyhoff.devices as devices
from pyhoff.devices import DigitalInputTerminal, DigitalOutputTerminal, AnalogInputTerminal, AnalogOutputTerminal


def test_terminal_plausib():
    """
    Test if all implemented BusTerminal classes in devices
    have the plausible parameters
    """

    for n, o in inspect.getmembers(devices):
        if inspect.isclass(o) and o not in [DigitalInputTerminal,
                                            DigitalOutputTerminal,
                                            AnalogInputTerminal,
                                            AnalogOutputTerminal]:
            print('Terminal: ' + n)
            if issubclass(o, DigitalInputTerminal):
                assert o.parameters.get('input_bit_width', 0) > 0
                assert o.parameters.get('output_bit_width', 0) == 0
                assert o.parameters.get('input_word_width', 0) == 0
                assert o.parameters.get('output_word_width', 0) == 0

            if issubclass(o, DigitalOutputTerminal):
                assert o.parameters.get('input_bit_width', 0) == 0
                assert o.parameters.get('output_bit_width', 0) > 0
                assert o.parameters.get('input_word_width', 0) == 0
                assert o.parameters.get('output_word_width', 0) == 0

            if issubclass(o, AnalogInputTerminal):
                assert o.parameters.get('input_bit_width', 0) == 0
                assert o.parameters.get('output_bit_width', 0) == 0
                assert o.parameters.get('input_word_width', 0) > 0

            if issubclass(o, AnalogOutputTerminal):
                assert o.parameters.get('input_bit_width', 0) == 0
                assert o.parameters.get('output_bit_width', 0) == 0
                assert o.parameters.get('output_word_width', 0) > 0


def rw_all_bus_terminals(bus_cupler: pyhoff.BusCoupler):
    for bt in bus_cupler.bus_terminals:
        if isinstance(bt, AnalogOutputTerminal):
            for channel in range(1, bt.parameters.get('output_word_width', 0) + 1):
                bt.set_normalized(channel, 0)
                bt.set_normalized(channel, 1)
                bt.set_normalized(channel, 2)

        if isinstance(bt, AnalogInputTerminal):
            for channel in range(1, bt.parameters.get('input_word_width', 0) + 1):
                assert bt.read_channel_word(channel, 1337) == 1337
                assert bt.read_channel_word(channel, 1337) == 1337
                assert bt.read_channel_word(channel, 1337) == 1337

        if isinstance(bt, DigitalOutputTerminal):
            for channel in range(1, bt.parameters.get('output_bit_width', 0) + 1):
                assert not bt.write_coil(channel, True)
                assert not bt.write_coil(channel, False)

        if isinstance(bt, DigitalInputTerminal):
            for channel in range(1, bt.parameters.get('input_bit_width', 0) + 1):
                assert bt.read_input(channel) is None


def test_terminal_setup():
    """
    Test if all implemented BusTerminal classes in devices can
    be instantiated and connected to a bus coupler
    """

    terminal_classes: list[type[pyhoff.BusTerminal]] = []
    for n, o in inspect.getmembers(devices):
        if inspect.isclass(o) and o not in [DigitalInputTerminal,
                                            DigitalOutputTerminal,
                                            AnalogInputTerminal,
                                            AnalogOutputTerminal]:
            if issubclass(o, pyhoff.BusTerminal):
                print(n)
                terminal_classes.append(o)

    # Beckhoff
    bus_cupler = devices.BK9050('localhost', 11255, terminal_classes, timeout=0.001)

    assert len(terminal_classes) == len(bus_cupler.bus_terminals)
    assert bus_cupler.get_error() == 'connection failed', bus_cupler.get_error()
    rw_all_bus_terminals(bus_cupler)

    # Wago
    bus_cupler = devices.WAGO_750_352('localhost', 11255, terminal_classes, timeout=0.001)

    assert len(terminal_classes) == len(bus_cupler.bus_terminals)
    assert bus_cupler.get_error() == 'connection failed', bus_cupler.get_error()
    rw_all_bus_terminals(bus_cupler)
