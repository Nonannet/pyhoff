from . import DigitalInputTerminal, DigitalOutputTerminal
from . import AnalogInputTerminal, AnalogOutputTerminal
from . import BusTerminal, BusCoupler


class BK9000(BusCoupler):
    """
    BK9000 ModBus TCP bus coupler
    """
    def _init_hardware(self, watchdog: float):
        # https://download.beckhoff.com/download/document/io/bus-terminals/bk9000_bk9050_bk9100de.pdf
        # config watchdog on page 58

        # set time-out/deactivate watchdog timer (deactivate: timeout = 0):
        self.modbus.write_single_register(0x1120, int(watchdog * 1000))  # ms

        # reset watchdog timer:
        self.modbus.write_single_register(0x1121, 0xBECF)
        self.modbus.write_single_register(0x1121, 0xAFFE)

        # set process image offset
        self._next_output_word_offset = 0x0800

        # set channel placement for terminal mapping
        self._channel_spacing = 2
        self._channel_offset = 1


class BK9050(BK9000):
    """
    BK9050 ModBus TCP bus coupler
    """
    pass


class BK9100(BK9000):
    """
    BK9100 ModBus TCP bus coupler
    """
    pass


class WAGO_750_352(BusCoupler):
    """
    Wago 750-352 ModBus TCP bus coupler
    """
    def _init_hardware(self, watchdog: float):
        # deactivate/reset watchdog timer:
        self.modbus.write_single_register(0x1005, 0xAAAA)
        self.modbus.write_single_register(0x1005, 0x5555)

        # set time-out/deactivate watchdog timer (deactivate: timeout = 0):
        self.modbus.write_single_register(0x1000, int(watchdog * 10))

        if watchdog:
            # configure watchdog to reset on all functions codes
            self.modbus.write_single_register(0x1001, 0xFFFF)

        # set process image offset
        self._next_output_word_offset = 0x0000
        self._next_output_bit_offset = 512

        # set separated input output mapping
        self._mixed_mapping = False


class DigitalInputTerminal4Bit(DigitalInputTerminal):
    """
    Generic 4 bit input terminal
    """
    parameters = {'input_bit_width': 4}


class DigitalInputTerminal8Bit(DigitalInputTerminal):
    """
    Generic 8 bit input terminal
    """
    parameters = {'input_bit_width': 8}


class DigitalInputTerminal16Bit(DigitalInputTerminal):
    """
    Generic 16 bit input terminal
    """
    parameters = {'input_bit_width': 16}


class DigitalOutputTerminal4Bit(DigitalOutputTerminal):
    """
    Generic 4 bit output terminal
    """
    parameters = {'output_bit_width': 4}


class DigitalOutputTerminal8Bit(DigitalOutputTerminal):
    """
    Generic 8 bit output terminal
    """
    parameters = {'output_bit_width': 8}


class DigitalOutputTerminal16Bit(DigitalOutputTerminal):
    """
    Generic 16 bit output terminal
    """
    parameters = {'output_bit_width': 16}


class KL1104(DigitalInputTerminal4Bit):
    """
    KL1104: 4x digital input 24 V
    """
    pass


class KL1408(DigitalInputTerminal8Bit):
    """
    KL1104: 8x digital input 24 V galvanic isolated
    """
    pass


class WAGO_750_1405(DigitalInputTerminal16Bit):
    """
    750-1405: 16x digital input 24 V
    """
    pass


class KL2404(DigitalOutputTerminal4Bit):
    """
    KL2404: 4x digital output with 500 mA
    """
    pass


class KL2424(DigitalOutputTerminal4Bit):
    """
    KL2424: 4x digital output with 2000 mA
    """
    pass


class KL2634(DigitalOutputTerminal4Bit):
    """
    KL2634: 4x digital output 250 V AC, 30 V DC, 4 A
    """
    pass


class KL2408(DigitalOutputTerminal8Bit):
    """
    750-530: 8x digital output with 24 V / 500 mA

    Contact order for DO1 to DO8 is: 1, 5, 2, 6, 3, 7, 4, 8.
    """
    pass


class WAGO_750_530(DigitalOutputTerminal8Bit):
    """
    750-530: 8x digital output with 24 V / 500 mA

    Contact order for DO1 to DO8 is: 1, 5, 2, 6, 3, 7, 4, 8.
    """
    pass


class KL1512(AnalogInputTerminal):
    """
    KL1512: 2x 16 bit counter, 24 V DC, 1 kHz
    """
    # Input: 2 x 16 Bit Daten (optional 4x 8 Bit Control/Status)
    parameters = {'input_word_width': 2}

    def __init__(self, bus_coupler: BusCoupler, o_b_addr: list[int], i_b_addr: list[int], o_w_addr: list[int], i_w_addr: list[int], mixed_mapping: bool):
        super().__init__(bus_coupler, o_b_addr, i_b_addr, o_w_addr, i_w_addr, mixed_mapping)
        self._last_counter_values = [self.read_channel_word(1), self.read_channel_word(2)]

    def read_counter(self, channel: int) -> int:
        """
        Read the absolut counter value of a specific channel.

        Args:
            channel: The channel number to read from.

        Returns:
            The counter value.
        """

        return self.read_channel_word(channel)

    def read_delta(self, channel: int) -> int:
        """
        Read the counter change since last read of a specific channel.

        Args:
            channel: The channel number to read from.

        Returns:
            The counter value.
        """
        new_count = self.read_channel_word(channel)
        delta = new_count - self._last_counter_values[channel - 1]
        if delta > 0x8000:
            delta = delta - 0x10000
        elif delta < -0x8000:
            delta = delta + 0x10000
        return delta


class KL3054(AnalogInputTerminal):
    """
    KL3054: 4x analog input 4...20 mA 12 Bit single-ended
    """
    # Input: 4 x 16 Bit Daten (optional 4x 8 Bit Control/Status)
    parameters = {'input_word_width': 4}

    def read_current(self, channel: int) -> float:
        """
        Read the current value from a specific channel.

        Args:
            channel: The channel number to read from.

        Returns:
            The current value.
        """
        return self.read_normalized(channel) * 16.0 + 4.0


class KL3042(AnalogInputTerminal):
    """
    KL3042: 2x analog input 0...20 mA 12 Bit single-ended
    """
    # Input: 2 x 16 Bit Daten (optional 2x 8 Bit Control/Status)
    parameters = {'input_word_width': 2}

    def read_current(self, channel: int) -> float:
        """
        Read the current value from a specific channel.

        Args:
            channel: The channel number to read from.

        Returns:
            The current value.
        """
        return self.read_normalized(channel) * 20.0


class KL3202(AnalogInputTerminal):
    """
    KL3202: 2x analog input PT100 16 Bit 3-wire
    """
    # Input: 2 x 16 Bit Daten (2 x 8 Bit Control/Status optional)
    parameters = {'input_word_width': 2}

    def read_temperature(self, channel: int) -> float:
        """
        Read the temperature value from a specific channel.

        Args:
            channel: The channel number to read from.

        Returns:
            The temperature value in °C.
        """
        val = self.read_channel_word(channel)
        if val > 0x7FFF:
            return (val - 0x10000) / 10.0
        else:
            return val / 10.0


class KL3214(AnalogInputTerminal):
    """
    KL3214: 4x analog input PT100 16 Bit 3-wire
    """
    # inp: 4 x 16 Bit Daten, 4 x 8 Bit Status (optional)
    # out: 4 x 8 Bit Control (optional)
    parameters = {'input_word_width': 4}

    def read_temperature(self, channel: int) -> float:
        """
        Read the temperature value from a specific channel.

        Args:
            channel: The channel number to read from.

        Returns:
            The temperature value.
        """
        val = self.read_channel_word(channel)
        if val > 0x7FFF:
            return (val - 0x10000) / 10.0
        else:
            return val / 10.0


class KL4002(AnalogOutputTerminal):
    """
    KL4002: 2x analog output 0...10 V 12 Bit differentiell
    """
    # Output: 2 x 16 Bit Daten (optional 2 x 8 Bit Control/Status)
    parameters = {'output_word_width': 2}

    def set_voltage(self, channel: int, value: float) -> bool:
        """
        Set a voltage value to a specific channel.

        Args:
            channel: The channel number to set.
            value: The voltage value to set.

        Returns:
            True if the write operation succeeded.
        """
        return self.set_normalized(channel, value / 10.0)


class KL4132(AnalogOutputTerminal):
    """
    KL4002: 2x analog output ±10 V 16 bit differential
    """
    # Output: 2 x 16 Bit Daten (optional 2 x 8 Bit Control/Status)
    parameters = {'output_word_width': 2}

    def set_normalized(self, channel: int, value: float) -> bool:
        """
        Set a normalized value between -1 and +1 to a specific channel.

        Args:
            channel: The channel number to set.
            value: The normalized value to set.

        Returns:
            True if the write operation succeeded.
        """
        if value >= 0:
            return self.write_channel_word(channel, int(value * 0x7FFF))
        else:
            return self.write_channel_word(channel, int(0x10000 + value * 0x7FFF))

    def set_voltage(self, channel: int, value: float) -> bool:
        """
        Set a voltage value between -10 and +10 V to a specific channel.

        Args:
            channel: The channel number to set.
            value: The voltage value to set.

        Returns:
            True if the write operation succeeded.
        """
        return self.set_normalized(channel, value / 10.0)


class KL4004(AnalogOutputTerminal):
    """
    KL4004: 4x analog output 0...10 V 12 Bit differentiell
    """
    # Output: 4 x 16 Bit Daten (optional 4 x 8 Bit Control/Status)
    parameters = {'output_word_width': 4}

    def set_voltage(self, channel: int, value: float) -> bool:
        """
        Set a voltage value to a specific channel.

        Args:
            channel: The channel number to set.
            value: The voltage value to set.

        Returns:
            True if the write operation succeeded.
        """
        return self.set_normalized(channel, value / 10.0)


class KL9010(BusTerminal):
    """
    End terminal, no I/O function
    """
    pass


class KL9100(BusTerminal):
    """
    Potential supply terminal, no I/O function
    """
    pass


class KL9183(BusTerminal):
    """
    Potential distribution terminal, no I/O function
    """
    pass


class KL9188(BusTerminal):
    """
    Potential distribution terminal, no I/O function
    """
    pass


class WAGO_750_600(BusTerminal):
    """
    End terminal, no I/O function
    """
    pass


class WAGO_750_602(BusTerminal):
    """
    Potential supply terminal, no I/O function
    """
    pass
