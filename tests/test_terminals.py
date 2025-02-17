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

    bus_cupler = devices.BK9050('localhost', 11255, terminal_classes, timeout=0.001)

    assert len(terminal_classes) == len(bus_cupler.bus_terminals)
    assert bus_cupler.get_error() == 'connection failed', bus_cupler.get_error()
