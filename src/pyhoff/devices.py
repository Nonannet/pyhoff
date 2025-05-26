from . import DigitalInputTerminal, DigitalOutputTerminal
from . import AnalogInputTerminal, AnalogOutputTerminal
from . import BusTerminal, BusCoupler


class BK9000(BusCoupler):
    """
    BK9000 ModBus TCP bus coupler
    """
    def _init_hardware(self, watchdog: float) -> None:
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
    def _init_hardware(self, watchdog: float) -> None:
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
            The current value in mA.
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
            The current value in mA.
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
            value: The voltage value to set in V.

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
            value: The voltage value to set in V.

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
            value: The voltage value to set in V.

        Returns:
            True if the write operation succeeded.
        """
        return self.set_normalized(channel, value / 10.0)


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


# Automatic generated terminal classes:

class KL1002(DigitalInputTerminal):
    """
    KL1002: 2-channel digital input, 24 V DC, 3 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 2}


class KL1012(DigitalInputTerminal):
    """
    KL1012: 2-channel digital input, 24 V DC, 0.2 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 2}


class KL1032(DigitalInputTerminal):
    """
    KL1032: 2-channel digital input, 48 V DC, 3 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 2}


class KL1052(DigitalInputTerminal):
    """
    KL1052: 2-channel digital input, 24 V DC, 3 ms, positive/ground
    switching
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 2}


class KL1114(DigitalInputTerminal):
    """
    KL1114: 4-channel digital input, 24 V DC, 0.2 ms, 2-/3-wire connection
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 4}


class KL1124(DigitalInputTerminal):
    """
    KL1124: 4-channel digital input, 5 V DC, 0.2 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 4}


class KL1154(DigitalInputTerminal):
    """
    KL1154: 4-channel digital input, 24 V DC, 3 ms, positive/ground
    switching
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 4}


class KL1164(DigitalInputTerminal):
    """
    KL1164: 4-channel digital input, 24 V DC, 0.2 ms, positive/ground
    switching
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 4}


class KL1184(DigitalInputTerminal):
    """
    KL1184: 4-channel digital input, 24 V DC, 3 ms, ground switching
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 4}


class KL1194(DigitalInputTerminal):
    """
    KL1194: 4-channel digital input, 24 V DC, 0.2 ms, ground switching
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 4}


class KL1212(DigitalOutputTerminal):
    """
    KL1212: 2-channel digital input, 24 V DC, 3 ms, with diagnostics
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 2, 'input_bit_width': 4}


class KL1232(DigitalInputTerminal):
    """
    KL1232: 2-channel digital input, 24 V DC, 0.2 ms, pulse extension
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 2}


class KL1302(DigitalInputTerminal):
    """
    KL1302: 2-channel digital input, 24 V DC, 3 ms, type 2
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 2}


class KL1304(DigitalInputTerminal):
    """
    KL1304: 4-channel digital input, 24 V DC, 3 ms, type 2
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 4}


class KL1312(DigitalInputTerminal):
    """
    KL1312: 2-channel digital input, 24 V DC, 0.2 ms, type 2
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 2}


class KL1314(DigitalInputTerminal):
    """
    KL1314: 4-channel digital input, 24 V DC, 0.2 ms, type 2
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 4}


class KL1352(DigitalInputTerminal):
    """
    KL1352: 2-channel digital input, NAMUR
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 4}


class KL1362(DigitalInputTerminal):
    """
    KL1362: 2-channel digital input, break-in alarm, 24 V DC, 3 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 4}


class KL1382(DigitalInputTerminal):
    """
    KL1382: 2-channel digital input, thermistor, 24 V DC, 30 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 4}


class KL1402(DigitalInputTerminal):
    """
    KL1402: 2-channel digital input, 24 V DC, 3 ms, 2-wire connection
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 2}


class KL1404(DigitalInputTerminal):
    """
    KL1404: 4-channel digital input, 24 V DC, 3 ms, 2-wire connection
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 4}


class KL1412(DigitalInputTerminal):
    """
    KL1412: 2-channel digital input, 24 V DC, 0.2 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 2}


class KL1414(DigitalInputTerminal):
    """
    KL1414: 4-channel digital input, 24 V DC, 0.2 ms, 2-wire connection
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 4}


class KL1418(DigitalInputTerminal):
    """
    KL1418: 8-channel digital input, 24 V DC, 0.2 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 8}


class KL1434(DigitalInputTerminal):
    """
    KL1434: 4-channel digital input, 24 V DC, 0.2 ms, type 2, 2-wire
    connection
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 4}


class KL1488(DigitalInputTerminal):
    """
    KL1488: 8-channel digital input, 24 V DC, 3 ms, ground switching
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 8}


class KL1498(DigitalInputTerminal):
    """
    KL1498: 8-channel digital input, 24 V DC, 0.2 ms, ground switching
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 8}


class KL1501(DigitalInputTerminal):
    """
    KL1501: 1-channel digital input, counter, 24 V DC, 100 kHz
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 40}


class KL1702(DigitalInputTerminal):
    """
    KL1702: 2-channel digital input, 120…230 V AC, 10 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 2}


class KL1704(DigitalInputTerminal):
    """
    KL1704: 4-channel digital input, 120…230 V AC, 10 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 4}


class KL1712(DigitalInputTerminal):
    """
    KL1712: 2-channel digital input, 120 V AC/DC, 10 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 2}


class KL1722(DigitalInputTerminal):
    """
    KL1722: 2-channel digital input, 120…230 V AC, 10 ms, without power
    contacts
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 2}


class KL1804(DigitalInputTerminal):
    """
    KL1804: 4-channel digital input, 24 V DC, 3 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 4}


class KL1808(DigitalInputTerminal):
    """
    KL1808: 8-channel digital input, 24 V DC, 3 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 8}


class KL1809(DigitalInputTerminal):
    """
    KL1809: 16-channel digital input, 24 V DC, 3 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 16}


class KL1814(DigitalInputTerminal):
    """
    KL1814: 4-channel digital input, 24 V DC, 0.2 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 4}


class KL1819(DigitalInputTerminal):
    """
    KL1819: 16-channel digital input, 24 V DC, 0.2 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 16}


class KL1859(DigitalOutputTerminal):
    """
    KL1859: 8-channel digital input + 8-channel digital output, 24 V DC, 3
    ms, 0.5 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 8, 'input_bit_width': 8}


class KL1862(DigitalInputTerminal):
    """
    KL1862: 16-channel digital input, 24 V DC, 3 ms, flat-ribbon cable
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 16}


class KL1872(DigitalInputTerminal):
    """
    KL1872: 16-channel digital input, 24 V DC, 0.2 ms, flat-ribbon cable
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 16}


class KL1889(DigitalInputTerminal):
    """
    KL1889: 16-channel digital input, 24 V DC, 3 ms, ground switching
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 16}


class KL2012(DigitalOutputTerminal):
    """
    KL2012: 2-channel digital output, 24 V DC, 0.5 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 2, 'input_bit_width': 0}


class KL2022(DigitalOutputTerminal):
    """
    KL2022: 2-channel digital output, 24 V DC, 2 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 2, 'input_bit_width': 0}


class KL2032(DigitalOutputTerminal):
    """
    KL2032: 2-channel digital output, 24 V DC, 0.5 A, reverse voltage
    protection
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 2, 'input_bit_width': 0}


class KL2114(DigitalOutputTerminal):
    """
    KL2114: 4-channel digital output, 24 V DC, 0.5 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 4, 'input_bit_width': 0}


class KL2124(DigitalOutputTerminal):
    """
    KL2124: 4-channel digital output, 5 V DC, 20 mA
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 4, 'input_bit_width': 0}


class KL2134(DigitalOutputTerminal):
    """
    KL2134: 4-channel digital output, 24 V DC, 0.5 A, reverse voltage
    protection
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 4, 'input_bit_width': 0}


class KL2184(DigitalOutputTerminal):
    """
    KL2184: 4-channel digital output, 24 V DC, 0.5 A, ground switching
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 4, 'input_bit_width': 0}


class KL2212(DigitalOutputTerminal):
    """
    KL2212: 2-channel digital output, 24 V DC, 0.5 A, with diagnostics
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 4, 'input_bit_width': 4}


class KL2284(DigitalOutputTerminal):
    """
    KL2284: 4-channel digital output, reverse switching, 24 V DC, 2 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 8, 'input_bit_width': 0}


class KL2442(DigitalOutputTerminal):
    """
    KL2442: 2-channel digital output, 24 V DC, 2 x 4 A/1 x 8 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 2, 'input_bit_width': 0}


class KL2488(DigitalOutputTerminal):
    """
    KL2488: 8-channel digital output, 24 V DC, 0.5 A, ground switching
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 8, 'input_bit_width': 0}


class KL2502(DigitalInputTerminal):
    """
    KL2502: 2-channel PWM output, 24 V DC, 0.1 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 48}


class KL2512(DigitalInputTerminal):
    """
    KL2512: 2-channel PWM output, 24 V DC, 1.5 A, ground switching
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 48}


class KL2532(DigitalInputTerminal):
    """
    KL2532: 2-channel motion interface, DC motor, 24 V DC, 1 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 48}


class KL2535(DigitalInputTerminal):
    """
    KL2535: 2-channel PWM output, 24 V DC, 1 A, current-controlled
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 48}


class KL2541(AnalogOutputTerminal):
    """
    KL2541: 1-channel motion interface, stepper motor, 48 V DC, 5 A, with
    incremental encoder
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 2, 'input_word_width': 2}


class KL2542(DigitalInputTerminal):
    """
    KL2542: 2-channel motion interface, DC motor, 48 V DC, 3.5 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 48}


class KL2545(DigitalInputTerminal):
    """
    KL2545: 2-channel PWM output, 8…50 V DC, 3.5 A, current-controlled
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 48}


class KL2552(DigitalInputTerminal):
    """
    KL2552: 2-channel motion interface, DC motor, 48 V DC, 5 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 48}


class KL2602(DigitalOutputTerminal):
    """
    KL2602: 2-channel relay output, 230 V AC, 30 V DC, 5 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 2, 'input_bit_width': 0}


class KL2612(DigitalOutputTerminal):
    """
    KL2612: 2-channel relay output, 125 V AC, 30 V DC, 0.5 A AC, 2 A DC
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 2, 'input_bit_width': 0}


class KL2622(DigitalOutputTerminal):
    """
    KL2622: 2-channel relay output, 230 V AC, 30 V DC, 5 A, without power
    contacts
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 2, 'input_bit_width': 0}


class KL2631(DigitalOutputTerminal):
    """
    KL2631: 1-channel relay output, 400 V AC, 300 V DC, 2 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 2, 'input_bit_width': 0}


class KL2641(DigitalOutputTerminal):
    """
    KL2641: 1-channel relay output, 230 V AC, 16 A, manual operation
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 2, 'input_bit_width': 2}


class KL2652(DigitalOutputTerminal):
    """
    KL2652: 2-channel relay output, 230 V AC, 300 V DC, 5 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 2, 'input_bit_width': 0}


class KL2701(DigitalOutputTerminal):
    """
    KL2701: 1-channel solid-state relay output, 0…230 V AC/DC, 3 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 2, 'input_bit_width': 0}


class KL2712(DigitalOutputTerminal):
    """
    KL2712: 2-channel triac output, 12...230 V AC, 0.5 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 2, 'input_bit_width': 0}


class KL2722(DigitalOutputTerminal):
    """
    KL2722: 2-channel triac output, 12...230 V AC, 1 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 2, 'input_bit_width': 0}


class KL2732(DigitalOutputTerminal):
    """
    KL2732: 2-channel triac output, 12...230 V AC, 1 A, without power
    contacts
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 2, 'input_bit_width': 0}


class KL2751(AnalogOutputTerminal):
    """
    KL2751: 1-channel universal dimmer, 230 V AC, 300 VA
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 1, 'input_word_width': 0}


class KL2761(AnalogOutputTerminal):
    """
    KL2761: 1-channel universal dimmer, 230 V AC, 600 VA
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 1, 'input_word_width': 0}


class KL2784(DigitalOutputTerminal):
    """
    KL2784: 4-channel solid state relay output, 30 V AC, 48 V DC, 2 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 4, 'input_bit_width': 0}


class KL2791(AnalogOutputTerminal):
    """
    KL2791: 1-channel motion interface, AC motor, 230 V AC, 0.9 A
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 1, 'input_word_width': 0}


class KL2794(DigitalOutputTerminal):
    """
    KL2794: 4-channel solid state relay output, 30 V AC, 48 V DC, 2 A,
    potential-free
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 4, 'input_bit_width': 0}


class KL2798(DigitalOutputTerminal):
    """
    KL2798: 8-channel solid state relay output, 30 V AC, 48 V DC, 2 A,
    potential-free
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 8, 'input_bit_width': 0}


class KL2808(DigitalOutputTerminal):
    """
    KL2808: 8-channel digital output, 24 V DC, 0.5 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 8, 'input_bit_width': 0}


class KL2809(DigitalOutputTerminal):
    """
    KL2809: 16-channel digital output, 24 V DC, 0.5 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 16, 'input_bit_width': 0}


class KL2828(DigitalOutputTerminal):
    """
    KL2828: 8-channel digital output, 24 V DC, 2 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 8, 'input_bit_width': 0}


class KL2872(DigitalOutputTerminal):
    """
    KL2872: 16-channel digital output, 24 V DC, 0.5 A, flat-ribbon cable
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 16, 'input_bit_width': 0}


class KL2889(DigitalOutputTerminal):
    """
    KL2889: 16-channel digital output, 24 V DC, 0.5 A, ground switching
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 16, 'input_bit_width': 0}


class KL3001(AnalogInputTerminal):
    """
    KL3001: 1-channel analog input, voltage, ±10 V, 12 bit, differential
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 1}


class KL3002(AnalogInputTerminal):
    """
    KL3002: 2-channel analog input, voltage, ±10 V, 12 bit, differential
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 2}


class KL3011(AnalogInputTerminal):
    """
    KL3011: 1-channel analog input, current, 0…20 mA, 12 bit, differential
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 1}


class KL3012(AnalogInputTerminal):
    """
    KL3012: 2-channel analog input, current, 0…20 mA, 12 bit, differential
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 2}


class KL3021(AnalogInputTerminal):
    """
    KL3021: 1-channel analog input, current, 4…20 mA, 12 bit, differential
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 1}


class KL3022(AnalogInputTerminal):
    """
    KL3022: 2-channel analog input, current, 4…20 mA, 12 bit, differential
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 2}


class KL3041(AnalogInputTerminal):
    """
    KL3041: 1-channel analog input, current, 0…20 mA, 12 bit, single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 1}


class KL3044(AnalogInputTerminal):
    """
    KL3044: 4-channel analog input, current, 0…20 mA, 12 bit, single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 4}


class KL3051(AnalogInputTerminal):
    """
    KL3051: 1-channel analog input, current, 4…20 mA, 12 bit, single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 1}


class KL3052(AnalogInputTerminal):
    """
    KL3052: 2-channel analog input, current, 4…20 mA, 12 bit, single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 2}


class KL3061(AnalogInputTerminal):
    """
    KL3061: 1-channel analog input, voltage, 0…10 V, 12 bit, single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 1}


class KL3062(AnalogInputTerminal):
    """
    KL3062: 2-channel analog input, voltage, 0…10 V, 12 bit, single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 2}


class KL3064(AnalogInputTerminal):
    """
    KL3064: 4-channel analog input, voltage, 0…10 V, 12 bit, single-ended,
    with shield connector
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 4}


class KL3102(AnalogInputTerminal):
    """
    KL3102: 2-channel analog input, voltage, ±10 V, 16 bit, differential
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 2}


class KL3112(AnalogInputTerminal):
    """
    KL3112: 2-channel analog input, current, 0…20 mA, 16 bit, differential
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 2}


class KL3122(AnalogInputTerminal):
    """
    KL3122: 2-channel analog input, current, 4…20 mA, 16 bit, differential
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 2}


class KL3132(AnalogInputTerminal):
    """
    KL3132: 2-channel analog input, voltage, ±10 V, 16 bit, differential,
    high-precision
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 2}


class KL3142(AnalogInputTerminal):
    """
    KL3142: 2-channel analog input, current, 0…20 mA, 16 bit,
    differential, high-precision
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 2}


class KL3152(AnalogInputTerminal):
    """
    KL3152: 2-channel analog input, current, 4…20 mA, 16 bit,
    differential, high-precision
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 2}


class KL3162(AnalogInputTerminal):
    """
    KL3162: 2-channel analog input, voltage, 0…10 V, 16 bit, differential,
    high-precision
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 2}


class KL3172(AnalogInputTerminal):
    """
    KL3172: 2-channel analog input, voltage, 0…2 V, 16 bit, differential,
    high-precision
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 2}


class KL3182(AnalogInputTerminal):
    """
    KL3182: 2-channel analog input, voltage, ±2 V, 16 bit, differential,
    high-precision
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 2}


class KL3201(AnalogInputTerminal):
    """
    KL3201: 1-channel analog input, temperature, RTD (Pt100), 16 bit
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 1}


class KL3204(AnalogInputTerminal):
    """
    KL3204: 4-channel analog input, temperature, RTD (Pt100), 16 bit
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 4}


class KL3222(AnalogInputTerminal):
    """
    KL3222: 2-channel analog input, temperature, RTD (Pt100), 16 bit,
    high-precision
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 2}


class KL3228(AnalogInputTerminal):
    """
    KL3228: 8-channel analog input, temperature, RTD (Pt1000, Ni1000), 16
    bit
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 8}


class KL3311(AnalogInputTerminal):
    """
    KL3311: 1-channel analog input, temperature, thermocouple, 16 bit
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 1}


class KL3312(AnalogInputTerminal):
    """
    KL3312: 2-channel analog input, temperature, thermocouple, 16 bit
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 2}


class KL3314(AnalogInputTerminal):
    """
    KL3314: 4-channel analog input, temperature, thermocouple, 16 bit
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 4}


class KL3351(AnalogInputTerminal):
    """
    KL3351: 1-channel analog input, measuring bridge, full bridge, 16 bit
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 2}


class KL3356(AnalogInputTerminal):
    """
    KL3356: 1-channel analog input, measuring bridge, full bridge, 16 bit,
    high-precision
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 2}


class KL3361(AnalogOutputTerminal):
    """
    KL3361: 1-channel analog input, voltage, ±20 mV, 15 bit, oscilloscope
    function
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 1, 'input_word_width': 1}


class KL3362(AnalogOutputTerminal):
    """
    KL3362: 2-channel analog input, voltage, ±10 V, 15 bit, oscilloscope
    function
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 2, 'input_word_width': 2}


class KL3403(AnalogOutputTerminal):
    """
    KL3403: 3-channel analog input, power measurement, 500 V AC, 1 A, 16
    bit
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 3, 'input_word_width': 3}


class KL3404(AnalogInputTerminal):
    """
    KL3404: 4-channel analog input, voltage, ±10 V, 12 bit, single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 4}


class KL3408(AnalogInputTerminal):
    """
    KL3408: 8-channel analog input, voltage, ±10 V, 12 bit, single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 8}


class KL3444(AnalogInputTerminal):
    """
    KL3444: 4-channel analog input, current, 0…20 mA, 12 bit, single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 4}


class KL3448(AnalogInputTerminal):
    """
    KL3448: 8-channel analog input, current, 0…20 mA, 12 bit, single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 8}


class KL3454(AnalogInputTerminal):
    """
    KL3454: 4-channel analog input, current, 4…20 mA, 12 bit, single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 4}


class KL3458(AnalogInputTerminal):
    """
    KL3458: 8-channel analog input, current, 4…20 mA, 12 bit, single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 8}


class KL3464(AnalogInputTerminal):
    """
    KL3464: 4-channel analog input, voltage, 0…10 V, 12 bit, single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 4}


class KL3468(AnalogInputTerminal):
    """
    KL3468: 8-channel analog input, voltage, 0…10 V, 12 bit, single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 8}


class KL4001(AnalogOutputTerminal):
    """
    KL4001: 1-channel analog output, voltage, 0…10 V, 12 bit, differential
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 1, 'input_word_width': 0}


class KL4011(AnalogOutputTerminal):
    """
    KL4011: 1-channel analog output, current, 0…20 mA, 12 bit,
    single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 1, 'input_word_width': 0}


class KL4012(AnalogOutputTerminal):
    """
    KL4012: 2-channel analog output, current, 0…20 mA, 12 bit,
    single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 2, 'input_word_width': 0}


class KL4021(AnalogOutputTerminal):
    """
    KL4021: 1-channel analog output, current, 4…20 mA, 12 bit,
    single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 1, 'input_word_width': 0}


class KL4022(AnalogOutputTerminal):
    """
    KL4022: 2-channel analog output, current, 4…20 mA, 12 bit,
    single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 2, 'input_word_width': 0}


class KL4031(AnalogOutputTerminal):
    """
    KL4031: 1-channel analog output, voltage, ±10 V, 12 bit, differential
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 1, 'input_word_width': 0}


class KL4032(AnalogOutputTerminal):
    """
    KL4032: 2-channel analog output, voltage, ±10 V, 12 bit, differential
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 2, 'input_word_width': 0}


class KL4034(AnalogOutputTerminal):
    """
    KL4034: 4-channel analog output, voltage, ±10 V, 12 bit, differential
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 4, 'input_word_width': 0}


class KL4112(AnalogOutputTerminal):
    """
    KL4112: 2-channel analog output, current, 0…20 mA, 16 bit,
    single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 2, 'input_word_width': 0}


class KL4404(AnalogOutputTerminal):
    """
    KL4404: 4-channel analog output, voltage, 0…10 V, 12 bit, single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 4, 'input_word_width': 0}


class KL4408(AnalogOutputTerminal):
    """
    KL4408: 8-channel analog output, voltage, 0…10 V, 12 bit, single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 8, 'input_word_width': 0}


class KL4414(AnalogOutputTerminal):
    """
    KL4414: 4-channel analog output, current, 0…20 mA, 12 bit,
    single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 4, 'input_word_width': 0}


class KL4418(AnalogOutputTerminal):
    """
    KL4418: 8-channel analog output, current, 0…20 mA, 12 bit,
    single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 8, 'input_word_width': 0}


class KL4424(AnalogOutputTerminal):
    """
    KL4424: 4-channel analog output, current, 4…20 mA, 12 bit,
    single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 4, 'input_word_width': 0}


class KL4428(AnalogOutputTerminal):
    """
    KL4428: 8-channel analog output, current, 4…20 mA, 12 bit,
    single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 8, 'input_word_width': 0}


class KL4434(AnalogOutputTerminal):
    """
    KL4434: 4-channel analog output, voltage, ±10 V, 12 bit, single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 4, 'input_word_width': 0}


class KL4438(AnalogOutputTerminal):
    """
    KL4438: 8-channel analog output, voltage, ±10 V, 12 bit, single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 8, 'input_word_width': 0}


class KL4494(AnalogOutputTerminal):
    """
    KL4494: 2-channel analog input + 2-channel analog output, voltage, ±10
    V, 12 bit, single-ended
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 2, 'input_word_width': 2}


class KL5051(AnalogOutputTerminal):
    """
    KL5051: 1-channel encoder interface, SSI, bidirectional
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 2, 'input_word_width': 2}


class KL5101(AnalogInputTerminal):
    """
    KL5101: 1-channel encoder interface, incremental, 5 V DC (DIFF RS422,
    TTL), 1 MHz
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 0, 'input_word_width': 1}


class KL5111(AnalogOutputTerminal):
    """
    KL5111: 1-channel encoder interface, incremental, 24 V DC HTL, 250 kHz
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 2, 'input_word_width': 2}


class KL5121(AnalogOutputTerminal):
    """
    KL5121: 1-channel encoder interface, incremental, 24 V DC HTL, 250
    kHz, with 4 x digital output 24 V DC, linear path control
    (Automatic generated stub)
    """
    parameters = {'output_word_width': 2, 'input_word_width': 2}


class KL9010(BusTerminal):
    """
    KL9010: End terminal
    (no I/O function)
    """
    pass


class KL9070(BusTerminal):
    """
    KL9070: Shield terminal
    (no I/O function)
    """
    pass


class KL9080(BusTerminal):
    """
    KL9080: Separation terminal
    (no I/O function)
    """
    pass


class KL9100(BusTerminal):
    """
    KL9100: Potential supply terminal, 24 V DC
    (no I/O function)
    """
    pass


class KL9150(BusTerminal):
    """
    KL9150: Potential supply terminal, 120…230 V AC
    (no I/O function)
    """
    pass


class KL9180(BusTerminal):
    """
    KL9180: Potential distribution terminal, 2 x 24 V DC; 2 x 0 V DC, 2 x
    PE
    (no I/O function)
    """
    pass


class KL9184(BusTerminal):
    """
    KL9184: potential distribution terminal, 8 x 24 V DC, 8 x 0 V DC
    (no I/O function)
    """
    pass


class KL9185(BusTerminal):
    """
    KL9185: potential distribution terminal, 4 x 24 V DC, 4 x 0 V DC
    (no I/O function)
    """
    pass


class KL9186(BusTerminal):
    """
    KL9186: Potential distribution terminal, 8 x 24 V DC
    (no I/O function)
    """
    pass


class KL9187(BusTerminal):
    """
    KL9187: Potential distribution terminal, 8 x 0 V DC
    (no I/O function)
    """
    pass


class KL9188(BusTerminal):
    """
    KL9188: Potential distribution terminal, 16 x 24 V DC
    (no I/O function)
    """
    pass


class KL9189(BusTerminal):
    """
    KL9189: Potential distribution terminal, 16 x 0 V DC
    (no I/O function)
    """
    pass


class KL9190(BusTerminal):
    """
    KL9190: Potential supply terminal, any voltage up to 230 V AC
    (no I/O function)
    """
    pass


class KL9195(BusTerminal):
    """
    KL9195: Shield terminal
    (no I/O function)
    """
    pass


class KL9200(BusTerminal):
    """
    KL9200: Potential supply terminal, 24 V DC, with fuse
    (no I/O function)
    """
    pass


class KL9250(BusTerminal):
    """
    KL9250: Potential supply terminal, 120…230 V AC, with fuse
    (no I/O function)
    """
    pass


class KL9290(BusTerminal):
    """
    KL9290: Potential supply terminal, any voltage up to 230 V AC, with
    fuse
    (no I/O function)
    """
    pass


class KL9380(BusTerminal):
    """
    KL9380: Mains filter terminal for dimmers
    (no I/O function)
    """
    pass


class KM1002(DigitalInputTerminal):
    """
    KM1002: Bus Terminal module, 16-channel digital input, 24 V DC, 3 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 16}


class KM1004(DigitalInputTerminal):
    """
    KM1004: Bus Terminal module, 32-channel digital input, 24 V DC, 3 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 32}


class KM1008(DigitalInputTerminal):
    """
    KM1008: Bus Terminal module, 64-channel digital input, 24 V DC, 3 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 64}


class KM1012(DigitalInputTerminal):
    """
    KM1012: Bus Terminal module, 16-channel digital input, 24 V DC, 0.2 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 16}


class KM1014(DigitalInputTerminal):
    """
    KM1014: Bus Terminal module, 32-channel digital input, 24 V DC, 0.2 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 32}


class KM1018(DigitalInputTerminal):
    """
    KM1018: Bus Terminal module, 64-channel digital input, 24 V DC, 0.2 ms
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 0, 'input_bit_width': 64}


class KM1644(DigitalOutputTerminal):
    """
    KM1644: Bus Terminal module, 4-channel digital input, 24 V DC, manual
    operation
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 4, 'input_bit_width': 4}


class KM2002(DigitalOutputTerminal):
    """
    KM2002: Bus Terminal module, 16-channel digital output, 24 V DC, 0.5 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 16, 'input_bit_width': 0}


class KM2004(DigitalOutputTerminal):
    """
    KM2004: Bus Terminal module, 32-channel digital output, 24 V DC, 0.5 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 32, 'input_bit_width': 0}


class KM2008(DigitalOutputTerminal):
    """
    KM2008: Bus Terminal module, 64-channel digital output, 24 V DC, 0.5 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 64, 'input_bit_width': 0}


class KM2042(DigitalOutputTerminal):
    """
    KM2042: Bus Terminal module, 16-channel digital output, 24 V DC, 0.5
    A, D-sub
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 16, 'input_bit_width': 0}


class KM2604(DigitalOutputTerminal):
    """
    KM2604: Bus Terminal module, 4-channel relay output, 230 V AC, 16 A
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 4, 'input_bit_width': 0}


class KM2614(DigitalOutputTerminal):
    """
    KM2614: Bus Terminal module, 4-channel relay output, 230 V AC, 16 A,
    manual/autom. operation
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 4, 'input_bit_width': 0}


class KM2642(DigitalOutputTerminal):
    """
    KM2642: Bus Terminal module, 2-channel digital output, 230 V AC, 6 A,
    manual/automatic operation
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 2, 'input_bit_width': 2}


class KM2652(DigitalOutputTerminal):
    """
    KM2652: Bus Terminal module, 2-channel digital output, 230 V AC, 6 A,
    manual/automatic operation
    (Automatic generated stub)
    """
    parameters = {'output_bit_width': 2, 'input_bit_width': 4}
