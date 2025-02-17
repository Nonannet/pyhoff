from .modbus import SimpleModbusClient
from typing import Type, Any


class BusTerminal():
    """
    Base class for all bus terminals.

    Args:
        bus_coupler: The bus coupler to which this terminal is connected.
        output_bit_offset: The offset of the output bits.
        input_bit_offset: The offset of the input bits.
        output_word_offset: The offset of the output words.
        input_word_offset: The offset of the input words.

    Attributes:
        bus_coupler: The bus coupler to which this terminal is connected.
        parameters: The parameters of the terminal.
    """
    parameters: dict[str, int] = {}

    def __init__(self, bus_coupler: 'BusCoupler',
                 output_bit_offset: int,
                 input_bit_offset: int,
                 output_word_offset: int,
                 input_word_offset: int):

        self._output_bit_offset = output_bit_offset
        self._input_bit_offset = input_bit_offset
        self._output_word_offset = output_word_offset
        self._input_word_offset = input_word_offset
        self.bus_coupler = bus_coupler


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
        return self.bus_coupler.modbus.read_discrete_input(self._input_bit_offset + channel - 1)


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
        return self.bus_coupler.modbus.write_single_coil(self._output_bit_offset + channel - 1, value)

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
        return self.bus_coupler.modbus.read_coil(self._output_bit_offset + channel - 1)


class AnalogInputTerminal(BusTerminal):
    """
    Base class for analog input terminals.
    """
    def read_words(self, word_offset: int, word_count: int) -> list[int] | None:
        """
        Read a list of words from the terminal.

        Args:
            word_offset: The starting word offset (0 based index).
            word_count: The number of words to read.

        Returns:
            The read words.

        Raises:
            Exception: If the word offset or count is out of range.
        """
        if word_offset < 0 or word_offset + word_count > self.parameters['input_word_width']:
            raise Exception("address out of range")
        return self.bus_coupler.modbus.read_input_registers(self._input_word_offset + word_offset, word_count)

    def read_word(self, word_offset: int) -> int:
        """
        Read a single word from the terminal.

        Args:
            word_offset: The word offset (0 based index) to read from.

        Returns:
            The read word value.
        """
        val = self.read_words(word_offset, 1)
        if val:
            return val[0]
        else:
            return -999

    def read_normalized(self, channel: int) -> float:
        """
        Read a normalized value (0...1) from a specific channel.

        Args:
            channel: The channel number to read from.

        Returns:
            The normalized value.
        """
        return self.read_word(channel * 2 - 1) / 0x7FFF


class AnalogOutputTerminal(BusTerminal):
    """
    Base class for analog output terminals.
    """
    def read_words(self, word_offset: int, word_count: int) -> list[int] | None:
        """
        Read a list of words from the terminal.

        Args:
            word_offset: The starting word offset (0 based index).
            word_count: The number of words to read.

        Returns:
            The read words.

        Raises:
            Exception: If the word offset or count is out of range.
        """
        if word_offset < 0 or word_offset + word_count > self.parameters['output_word_width']:
            raise Exception("address out of range")
        return self.bus_coupler.modbus.read_holding_registers(self._output_word_offset + word_offset, word_count)

    def read_word(self, word_offset: int) -> int:
        """
        Read a single word from the terminal.

        Args:
            word_offset: The word offset (0 based index) to read from.

        Returns:
            The read word value.
        """
        val = self.read_words(word_offset, 1)
        if val:
            return val[0]
        else:
            return -999

    def write_word(self, word_offset: int, data: int) -> bool:
        """
        Write a word to the terminal.

        Args:
            word_offset: The word offset to write to.
            data: The data to write.

        Returns:
            The result of the write operation.

        Raises:
            Exception: If the word offset is out of range.
        """
        if word_offset < 0 or word_offset + 1 > self.parameters['output_word_width']:
            raise Exception("address out of range")
        return self.bus_coupler.modbus.write_single_register(self._output_word_offset + word_offset, data)

    def set_normalized(self, channel: int, value: float):
        """
        Set a normalized value between 0 and 1 to a specific channel.

        Args:
            channel: The channel number to set.
            value: The normalized value to set.
        """
        self.write_word(channel * 2 - 1, int(value * 0x7FFF))


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

        self.bus_terminals: list[Any] = list()
        self._next_output_bit_offset = 0
        self._next_input_bit_offset = 0
        self._next_output_word_offset = 0
        self._next_input_word_offset = 0
        self.modbus = SimpleModbusClient(host, port, timeout=timeout, debug=debug)

        self.add_bus_terminals(bus_terminals)
        self._init_hardware(watchdog)

    def _init_hardware(self, watchdog: float):
        pass

    def add_bus_terminals(self, bus_terminals: list[Type[BusTerminal]]) -> list[Any]:
        """
        Add bus terminals to the bus coupler.

        Args:
            bus_terminals: A list of bus terminal classes to add.

        Returns:
            The corresponding list of bus terminal objects.
        """
        for terminal_class in bus_terminals:
            assert issubclass(terminal_class, BusTerminal), f'{terminal_class} is not a bus terminal'
            new_terminal = terminal_class(self,
                                          self._next_output_bit_offset,
                                          self._next_input_bit_offset,
                                          self._next_output_word_offset,
                                          self._next_input_word_offset)

            self._next_output_bit_offset += terminal_class.parameters.get('output_bit_width', 0)
            self._next_input_bit_offset += terminal_class.parameters.get('input_bit_width', 0)
            self._next_output_word_offset += terminal_class.parameters.get('output_word_width', 0)
            self._next_input_word_offset += terminal_class.parameters.get('input_word_width', 0)

            self.bus_terminals.append(new_terminal)

        return self.bus_terminals

    def get_error(self) -> str:
        """
        Get the last error message.

        Returns:
            The last error message.
        """
        return self.modbus.last_error
