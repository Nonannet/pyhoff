import inspect
import src.pyhoff.devices as devices
from src.pyhoff.devices import DigitalInputTerminal, DigitalOutputTerminal, AnalogInputTerminal, AnalogOutputTerminal


def test_terminal_plausib():

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
