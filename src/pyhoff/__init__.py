from .modbus import SimpleModbusClient
from typing import Iterable, TypeVar

_BT = TypeVar('_BT', bound='BusTerminal')


def _is_bus_terminal(bt_type: type['BusTerminal']) -> bool:
    if BusTerminal.__name__ == bt_type.__name__:
        return True

    return any(_is_bus_terminal(b) for b in bt_type.__bases__)


class BusTerminal():
    """
    Base class for all bus terminals.

    Attributes:
        bus_coupler: The bus coupler to which this terminal is connected.
        parameters: The parameters of the terminal.
    """
    parameters: dict[str, int] = {}

    def __init__(self, bus_coupler: 'BusCoupler',
                 output_bit_addresses: list[int],
                 input_bit_addresses: list[int],
                 output_word_addresses: list[int],
                 input_word_addresses: list[int],
                 mixed_mapping: bool):
        """
        Instantiate a new BusTerminal base class.

        Args:
            bus_coupler: The bus coupler to which this terminal is connected.
            output_bit_addresses: List of addresses of the output bits.
            input_bit_addresses: List of addresses of input bits.
            output_word_addresses: List of addresses of output words.
            input_word_addresses: List of addresses of input words.
        """
        self.bus_coupler = bus_coupler
        self._output_bit_addresses = output_bit_addresses
        self._input_bit_addresses = input_bit_addresses
        self._output_word_addresses = output_word_addresses
        self._input_word_addresses = input_word_addresses
        self._mixed_mapping = mixed_mapping

    @classmethod
    def select(cls: type[_BT], bus_coupler: 'BusCoupler', terminal_number: int = 0) -> _BT:
        """
        Returns the n-th bus terminal instance of the parent class
        specified by terminal_number.

        Args:
            bus_coupler: The bus coupler to which the terminal is connected.
            terminal_number: The index of the bus terminal to return. Counted for
                all bus terminals of the same type, not all bus terminals. Started for the
                first terminal with 0

        Returns:
            The selected bus terminal instance.
        """
        terminal_list = [bt for bt in bus_coupler.bus_terminals if isinstance(bt, cls)]
        assert terminal_list, f"No instance of {cls.__name__} configured at this BusCoupler"
        assert 0 <= terminal_number < len(terminal_list), f"Out of range, select in range: 0..{len(terminal_list) - 1}"
        return terminal_list[terminal_number]


class DigitalInputTerminal(BusTerminal):
    """
    Base class for digital input terminals.
    """
    def read_input(self, channel: int) -> bool | None:
        """
        Read the input from a specific channel.

        Args:
            channel: The channel number (start counting from 1) to read from.

        Returns:
            The input value of the specified channel or None if the read operation failed.

        Raises:
            Exception: If the channel number is out of range.
        """
        if channel < 1 or channel > self.parameters['input_bit_width']:
            raise Exception("address out of range")
        return self.bus_coupler.modbus.read_discrete_input(self._input_bit_addresses[channel - 1])


class DigitalOutputTerminal(BusTerminal):
    """
    Base class for digital output terminals.
    """
    def write_coil(self, channel: int, value: bool) -> bool:
        """
        Write a value to a specific channel.

        Args:
            channel: The channel number (start counting from 1) to write to.
            value: The value to write.

        Returns:
            True if the write operation succeeded, otherwise False.

        Raises:
            Exception: If the channel number is out of range.
        """
        if channel < 1 or channel > self.parameters['output_bit_width']:
            raise Exception("address out of range")
        return self.bus_coupler.modbus.write_single_coil(self._output_bit_addresses[channel - 1], value)

    def read_coil(self, channel: int) -> bool | None:
        """
        Read the coil value back from a specific channel.

        Args:
            channel: The channel number (start counting from 1) to read from.

        Returns:
            The coil value of the specified channel or None if the read operation failed.

        Raises:
            Exception: If the channel number is out of range.
        """
        if channel < 1 or channel > self.parameters['output_bit_width']:
            raise Exception("address out of range")
        return self.bus_coupler.modbus.read_coil(self._output_bit_addresses[channel - 1])


class AnalogInputTerminal(BusTerminal):
    """
    Base class for analog input terminals.
    """
    def read_channel_word(self, channel: int, error_value: int = -99999) -> int:
        """
        Read a single word from the terminal.

        Args:
            channel: The channel number (1 based index) to read from.

        Returns:
            The read word value.

        Raises:
            Exception: If the word offset or count is out of range.
        """
        assert 1 <= channel <= self.parameters['input_word_width'], \
            f"channel out of range, must be between {1} and {self.parameters['input_word_width']}"

        value = self.bus_coupler.modbus.read_input_registers(self._input_word_addresses[channel - 1], 1)

        return value[0] if value else error_value

    def read_normalized(self, channel: int) -> float:
        """
        Read a normalized value (0...1) from a specific channel.

        Args:
            channel: The channel number to read from.

        Returns:
            The normalized value.
        """
        return self.read_channel_word(channel) / 0x7FFF


class AnalogOutputTerminal(BusTerminal):
    """
    Base class for analog output terminals.
    """
    def read_channel_word(self, channel: int, error_value: int = -99999) -> int:
        """
        Read a single word from the terminal.

        Args:
            channel: The channel number (1 based index) to read from.

        Returns:
            The read word value or provided error_value if read failed.

        Raises:
            Exception: If the word offset or count is out of range.
        """
        assert not self._mixed_mapping, 'Reading of output state is not supported with this Bus Coupler.'
        assert 1 <= channel <= self.parameters['output_word_width'], \
            f"channel out of range, must be between {1} and {self.parameters['output_word_width']}"

        value = self.bus_coupler.modbus.read_holding_registers(self._output_word_addresses[channel - 1], 1)

        return value[0] if value else error_value

    def write_channel_word(self, channel: int, value: int) -> bool:
        """
        Write a word to the terminal.

        Args:
            channel: The channel number (1 based index) to write to.

        Returns:
            True if the write operation succeeded.

        Raises:
            Exception: If the word offset or count is out of range.
        """
        assert 1 <= channel <= self.parameters['output_word_width'], \
            f"channel out of range, must be between {1} and {self.parameters['output_word_width']}"

        return self.bus_coupler.modbus.write_single_register(self._output_word_addresses[channel - 1], value)

    def set_normalized(self, channel: int, value: float) -> bool:
        """
        Set a normalized value between 0 and 1 to a specific channel.

        Args:
            channel: The channel number to set.
            value: The normalized value to set.

        Returns:
            True if the write operation succeeded.
        """
        return self.write_channel_word(channel, int(value * 0x7FFF))


class BusCoupler():
    """
    Base class for ModBus TCP bus coupler

    Args:
        host: ip or hostname of the bus coupler
        port: port of the modbus host
        debug: outputs modbus debug information
        timeout: timeout for waiting for the device response
        watchdog: time in seconds after the device sets all outputs to
            default state. A value of 0 deactivates the watchdog.
        debug: If True, debug information is printed.

    Attributes:
        bus_terminals: A list of bus terminal classes according to the
            connected terminals.
        modbus: The underlying modbus client used for the connection.
    """

    def __init__(self, host: str, port: int = 502, bus_terminals: Iterable[type[BusTerminal]] = [],
                 timeout: float = 5, watchdog: float = 0, debug: bool = False):
        """
        Instantiate a new bus coupler base class.

        Args:
            host: ip or hostname of the bus coupler
            port: port of the modbus host
            debug: outputs modbus debug information
            timeout: timeout for waiting for the device response
            watchdog: time in seconds after the device sets all outputs to
                default state. A value of 0 deactivates the watchdog.
            debug: If True, debug information is printed.

        Examples:
            >>> from pyhoff.devices import *
            >>> bk = BK9000('192.168.0.23', bus_terminals=[KL3202, KL9010])
            >>> t1 = bk.terminals[0].read_temperature(1)
            >>> t2 = bk.terminals[0].read_temperature(2)
            >>> print(f"Temperature ch1: {t1:.1f} °C, Temperature ch2: {t2:.1f} °C")
            Temperature ch1: 23.2 °C, Temperature ch2: 22.1 °C
        """
        self.bus_terminals: list[BusTerminal] = list()
        self._next_output_bit_offset = 0
        self._next_input_bit_offset = 0
        self._next_output_word_offset = 0
        self._next_input_word_offset = 0
        self._channel_spacing = 1
        self._channel_offset = 0
        self._mixed_mapping = True
        self.modbus = SimpleModbusClient(host, port, timeout=timeout, debug=debug)

        self.add_bus_terminals(bus_terminals)
        self._init_hardware(watchdog)

    def _init_hardware(self, watchdog: float) -> None:
        pass

    def add_bus_terminals(self, *new_bus_terminals: type[BusTerminal] | Iterable[type[BusTerminal]]) -> list[BusTerminal]:
        """
        Add bus terminals to the bus coupler.

        Args:
            new_bus_terminals: bus terminal classes to add.

        Returns:
            The corresponding list of bus terminal objects.
        """

        terminal_classes: list[type[BusTerminal]] = []
        for element in new_bus_terminals:
            if isinstance(element, Iterable):
                for bt in element:
                    terminal_classes.append(bt)
            else:
                terminal_classes.append(element)

        for terminal_class in terminal_classes:
            assert _is_bus_terminal(terminal_class), f"{terminal_class} is not a bus terminal"

            def get_para(key: str) -> int:
                return terminal_class.parameters.get(key, 0)

            new_terminal = terminal_class(
                self,
                [i + self._next_output_bit_offset for i in range(get_para('output_bit_width'))],
                [i + self._next_input_bit_offset for i in range(get_para('input_bit_width'))],
                [i * self._channel_spacing + self._channel_offset + self._next_output_word_offset
                 for i in range(get_para('output_word_width'))],
                [i * self._channel_spacing + self._channel_offset + self._next_input_word_offset
                 for i in range(get_para('input_word_width'))],
                self._mixed_mapping)

            output_word_width = get_para('output_word_width')
            input_word_width = get_para('input_word_width')

            if self._mixed_mapping:
                # Shared mapping for word based inputs and outputs
                word_width = max(output_word_width, input_word_width)
                output_word_width = word_width
                input_word_width = word_width

            self._next_output_bit_offset += get_para('output_bit_width')
            self._next_input_bit_offset += get_para('input_bit_width')
            self._next_output_word_offset += output_word_width * self._channel_spacing
            self._next_input_word_offset += input_word_width * self._channel_spacing

            self.bus_terminals.append(new_terminal)

        return self.bus_terminals

    def select(self, bus_terminal_type: type[_BT], terminal_number: int = 0) -> _BT:
        """
        Returns the n-th bus terminal instance of the given bus terminal type and
        terminal index.

        Args:
            bus_terminals_type: The bus terminal class to select from.
            terminal_number: The index of the bus terminal to return. Counted for
                all bus terminals of the same type, not all bus terminals. Started for the
                first terminal with 0

        Returns:
            The selected bus terminal instance.

        Example:
            >>> from pyhoff.devices import *
            >>> bk = BK9050("172.16.17.1", bus_terminals=[KL2404, KL2424])
            >>> # Select the first KL2425 terminal:
            >>> kl2404 = bk.select(KL2424, 0)
        """
        return bus_terminal_type.select(self, terminal_number)

    def get_error(self) -> str:
        """
        Get the last error message.

        Returns:
            The last error message.
        """
        return self.modbus.last_error
