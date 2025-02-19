from .modbus import SimpleModbusClient
from typing import Type


class BusTerminal():
    """
    Base class for all bus terminals.

    Args:
        bus_coupler: The bus coupler to which this terminal is connected.
        output_bit_addresses: List of addresses of the output bits.
        input_bit_addresses: List of addresses of input bits.
        output_word_addresses: List of addresses of output words.
        input_word_addresses: List of addresses of input words.

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

        self.bus_coupler = bus_coupler
        self._output_bit_addresses = output_bit_addresses
        self._input_bit_addresses = input_bit_addresses
        self._output_word_addresses = output_word_addresses
        self._input_word_addresses = input_word_addresses
        self._mixed_mapping = mixed_mapping


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
            The read word value.

        Raises:
            Exception: If the word offset or count is out of range.
        """
        assert not self._mixed_mapping, 'Reading of output state is not supported with this Bus Coupler.'
        assert 1 <= channel <= self.parameters['output_word_width'], \
            f"channel out of range, must be between {1} and {self.parameters['output_word_width']}"

        value = self.bus_coupler.modbus.read_holding_registers(self._output_word_addresses[channel - 1], 1)

        return value[0] if value else error_value

    def write_channel_word(self, channel: int, value: int) -> int:
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

    def set_normalized(self, channel: int, value: float):
        """
        Set a normalized value between 0 and 1 to a specific channel.

        Args:
            channel: The channel number to set.
            value: The normalized value to set.
        """
        self.write_channel_word(channel, int(value * 0x7FFF))


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

    Examples:
        >>> from pyhoff.devices import *
        >>> bk = BK9000('192.168.0.23', bus_terminals=[KL3202, KL9010])
        >>> t1 = bk.terminals[0].read_temperature(1)
        >>> t2 = bk.terminals[0].read_temperature(2)
        >>> print(f"Temperature ch1: {t1:.1f} °C, Temperature ch2: {t2:.1f} °C")
        Temperature ch1: 23.2 °C, Temperature ch2: 22.1 °C
    """

    def __init__(self, host: str, port: int = 502, bus_terminals: list[Type[BusTerminal]] = [],
                 timeout: float = 5, watchdog: float = 0, debug: bool = False):

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

    def _init_hardware(self, watchdog: float):
        pass

    def add_bus_terminals(self, bus_terminals: list[Type[BusTerminal]]) -> list[BusTerminal]:
        """
        Add bus terminals to the bus coupler.

        Args:
            bus_terminals: A list of bus terminal classes to add.

        Returns:
            The corresponding list of bus terminal objects.
        """

        for terminal_class in bus_terminals:
            assert issubclass(terminal_class, BusTerminal), f'{terminal_class} is not a bus terminal'

            def get_para(key: str):
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

    def get_error(self) -> str:
        """
        Get the last error message.

        Returns:
            The last error message.
        """
        return self.modbus.last_error
