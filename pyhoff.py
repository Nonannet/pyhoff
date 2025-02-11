from pyModbusTCP.client import ModbusClient
from typing import Type
 
class BusTerminal():
    output_bit_width = 0
    input_bit_width = 0
    output_word_width = 0
    input_word_width = 0

    def __init__(self, bus_coupler: 'BusCoupler'):
        self.output_bit_offset = 0
        self.input_bit_offset = 0
        self.output_word_offset = 0
        self.output_word_offset = 0
        self.input_word_offset = 0
        self.bus_coupler = bus_coupler

class DigitalInputTerminal(BusTerminal):
    def read_input(self, channel: int):
        print(self.input_bit_width, channel)
        if channel < 1 or channel > self.input_bit_width:
            raise Exception("address out of range")
        return self.bus_coupler.read_discrete_input(self.input_bit_offset + channel - 1)

class DigitalOutputTerminal(BusTerminal):
    def write_coil(self, channel: int, value: int):
        if channel < 1 or channel > self.output_bit_width:
            raise Exception("address out of range")
        return self.bus_coupler.write_single_coil(self.output_bit_offset + channel - 1, value)

    def read_coil(self, channel: int):
        if channel < 1 or channel > self.output_bit_width:
            raise Exception("address out of range")
        return self.bus_coupler.read_coil(self.output_bit_offset + channel - 1)
    
class AnalogInputTerminal(BusTerminal):
    def read_words(self, word_offset: int, word_count: int):
        if word_offset < 0 or word_offset + word_count > self.input_word_width:
            raise Exception("address out of range")
        return self.bus_coupler.read_input_registers(self.input_word_offset + word_offset, word_count)
    
    def read_words_nocheck(self, word_offset: int, word_count: int):
        return self.bus_coupler.read_input_registers(self.input_word_offset + word_offset, word_count)
    
    def read_word(self, word_offset: int):
        val = self.read_words(word_offset, 1)
        if val is None:
            return -999
        else:
            return val[0]
            
    
class AnalogOutputTerminal(BusTerminal):
    def read_words(self, word_offset: int, word_count: int):
        if word_offset < 0 or word_offset + word_count > self.output_word_width:
            raise Exception("address out of range")
        return self.bus_coupler.read_holding_registers(self.output_word_offset + word_offset, word_count)
    
    def read_words_nocheck(self, word_offset: int, word_count: int):
        return self.bus_coupler.read_holding_registers(self.output_word_offset*0 + word_offset, word_count)
    
    def read_word(self, word_offset: int):
        val = self.read_words(word_offset, 1)
        if val is None:
            return -999
        else:
            return val[0]
    
    def write_word(self, word_offset: int, data: int):
        if word_offset < 0 or word_offset + 1 > self.output_word_width:
            raise Exception("address out of range")
        return self.bus_coupler.write_single_register(self.output_word_offset + word_offset, data)
    
    def write_word_nocheck(self, word_offset: int, data: int):
        return self.bus_coupler.write_single_register(self.output_word_offset*0 + word_offset, data)
    
class KL1104(DigitalInputTerminal):
    """KL1104: 4x digital input 24 V"""
    input_bit_width = 4

class KL1408(DigitalInputTerminal):
    """KL1104: 8x digital input 24 V galvanic isolated"""
    input_bit_width = 8

class WAGO_750_1405(DigitalInputTerminal):
    """750-1405: 16x digital input 24 V"""
    input_bit_width = 16

class KL2404(DigitalOutputTerminal):
    """KL2404: 4x digital output with 500 mA"""
    output_bit_width = 4

class KL2424(DigitalOutputTerminal):
    """KL2424: 4x digital output with 2000 mA"""
    output_bit_width = 4

class KL2634(DigitalOutputTerminal):
    """KL2634: 4x digital output 250 V AC, 30 V DC, 4 A"""
    output_bit_width = 4
    
class KL2408(DigitalOutputTerminal):
    """750-530: 8x digital output with 24 V / 500 mA"""
    #contact order for DO1 to DO8 is: 1, 5, 2, 6, 3, 7, 4, 8
    output_bit_width = 8

class WAGO_750_530(DigitalOutputTerminal):
    """750-530: 8x digital output with 24 V / 500 mA"""
    #contact order for DO1 to DO8 is: 1, 5, 2, 6, 3, 7, 4, 8
    output_bit_width = 8   
    
class KL3054(AnalogInputTerminal):
    """KL3054: 4x analog input 4...20 mA 12 Bit single-ended"""
    #Input: 4 x 16 Bit Daten (optional 4x 8 Bit Control/Status)
    input_word_width = 8
    output_word_width = 8
    
    def read_normalized(self, channel: int):
        return self.read_word(channel * 2 - 1) / 0x7FFF
    
    def read_current(self, channel: int):
        return self.read_normalized(channel * 2 - 1) * 16.0 + 4.0
    
class KL3042(AnalogInputTerminal):
    """KL3042: 2x analog input 0...20 mA 12 Bit single-ended"""
    #Input: 2 x 16 Bit Daten (optional 2x 8 Bit Control/Status)
    input_word_width = 4
    output_word_width = 4
    
    def read_normalized(self, channel: int):
        return self.read_word(channel*2-1) / 0x7FFF
    
    def read_current(self, channel: int):
        return self.read_normalized(channel*2-1) * 20.0

class KL3202(AnalogInputTerminal):
    """KL3202: 2x analog input PT100 16 Bit 3-wire"""
    #Input: 2 x 16 Bit Daten (2 x 8 Bit Control/Status optional)
    input_word_width = 4
    output_word_width = 4
    
    def read_temperature(self, channel: int):
        val = self.read_word(channel*2-1)
        if val > 0x7FFF:
            return (val - 0x10000) / 10.0
        else:
            return  val / 10.0
    
class KL3214(AnalogInputTerminal):
    """KL3214: 4x analog input PT100 16 Bit 3-wire"""
    #inp: 4 x 16 Bit Daten, 4 x 8 Bit Status (optional)
    #out: 4 x 8 Bit Control (optional)
    input_word_width = 8
    output_word_width = 8
    
    def read_temperature(self, channel: int):
        val = self.read_word(channel*2-1)
        if val > 0x7FFF:
            return (val - 0x10000) / 10.0
        else:
            return  val / 10.0
        
class KL4002(AnalogOutputTerminal):
    """KL4002: 2x analog output 0...10 V 12 Bit differentiell"""
    #Output: 2 x 16 Bit Daten (optional 2 x 8 Bit Control/Status)
    input_word_width = 4
    output_word_width = 4
    
    def set_normalized(self, channel: int, value: float):
        self.write_word(channel*2-1, int(value * 0x7FFF))
    
    def set_voltage(self, channel: int, value: float):
        self.set_normalized(channel, value / 10.0)

class KL4132(AnalogOutputTerminal):
    """KL4002: 2x analog output ±10 V 16 bit differential"""
    #Output: 2 x 16 Bit Daten (optional 2 x 8 Bit Control/Status)
    input_word_width = 4
    output_word_width = 4
    
    def set_normalized(self, channel: int, value: float):
        if value >= 0:
            self.write_word(channel-1, int(value * 0x7FFF))
        else:
            self.write_word(channel-1, int(0x10000 + value * 0x7FFF ))
    
    def set_voltage(self, channel: int, value: float):
        self.set_normalized(channel, value / 10.0)

class KL4004(AnalogOutputTerminal):
    """KL4004: 4x analog output 0...10 V 12 Bit differentiell"""
    #Output: 4 x 16 Bit Daten (optional 4 x 8 Bit Control/Status)
    input_word_width = 8
    output_word_width = 8
    
    def set_normalized(self, channel: int, value: float):
        self.write_word(channel*2-1, int(value * 0x7FFF))
    
    def set_voltage(self, channel: int, value: float):
        self.set_normalized(channel, value / 10.0)
    
class KL9000(BusTerminal):
    """Dummy, no I/O function"""
    pass

class KL9010(BusTerminal):
    """Dummy, no I/O function"""
    pass

class KL9100(BusTerminal):
    """Dummy, no I/O function"""
    pass

class KL9183(BusTerminal):
    """Dummy, no I/O function"""
    pass

class KL9188(BusTerminal):
    """Dummy, no I/O function"""
    pass

class WAGO_750_600(BusTerminal):
    """Dummy, no I/O function"""
    pass

class WAGO_750_602(BusTerminal):
    """Dummy, no I/O function"""
    pass

class BusCoupler(ModbusClient):
    """BusCoupler: Busskoppler ModBus TCP"""
    
    def __init__(self, host: str, port: int = 502, timeout: int = 5, watchdog: float = 0):
        """
        Constructs all the necessary attributes for the person object.

        Parameters
        ----------
            host : str
                ip or hostname of the BK9050
            port : int
                port of the modbus host
            debug : bool
                outputs modbus debug information
            timeout : float
                timeout for waiting for the device response
            watchdog : float
                time in secounds after the device sets all outputs to
                default state. A value of 0 deactivates the watchdog.
        """
        
        ModbusClient.__init__(self, host, port, auto_open=True, timeout=timeout)
        self.bus_terminals: list[BusTerminal] = list()
        self.next_output_bit_offset = 0
        self.next_input_bit_offset = 0
        self.next_output_word_offset = 0
        self.next_input_word_offset = 0
        self.init_hardware(watchdog)

    def init_hardware(self, watchdog: float):
        pass
    
    def read_discrete_input(self, address: int):
        value = self.read_discrete_inputs(address)
        if value is None:
            return False
        else:
            return value[0]
        
    def read_coil(self, address):
        value = self.read_coils(address)
        if value is None:
            return False
        else:
            return value[0]
        
    def add_bus_terminals(self, bus_terminals: list[Type[BusTerminal]]) -> list[BusTerminal]:
        for terminal_class in bus_terminals:
            nterm = terminal_class(self)
            
            nterm.output_bit_offset = self.next_output_bit_offset
            nterm.input_bit_offset = self.next_input_bit_offset
            nterm.output_word_offset = self.next_output_word_offset
            nterm.input_word_offset = self.next_input_word_offset

            self.next_output_bit_offset += terminal_class.output_bit_width
            self.next_input_bit_offset += terminal_class.input_bit_width
            self.next_output_word_offset += terminal_class.output_word_width
            self.next_input_word_offset += terminal_class.input_word_width

            self.bus_terminals.append(nterm)
        
        return self.bus_terminals
    
class ModBusBK9050(BusCoupler):
    """BK9050: Busskoppler ModBus TCP"""
    
    def init_hardware(self, watchdog: float):
        #https://download.beckhoff.com/download/document/io/bus-terminals/bk9000_bk9050_bk9100de.pdf
        #config watchdog on page 58
        
        #set time-out/deactivate watchdog timer (deactivate: timeout = 0):
        self.write_single_register(0x1120, watchdog * 1000) #ms
        
        #reset watchdog timer:
        self.write_single_register(0x1121, 0xBECF)
        self.write_single_register(0x1121, 0xAFFE)

        #set process image offset
        self.next_output_word_offset = 0x0800

class WAGO750_352(BusCoupler):
    """Wago 750-352: Busskoppler ModBus TCP"""
    
    def init_hardware(self, watchdog: float):
        #deactivate/reset watchdog timer:
        self.write_single_register(0x1005, 0xAAAA)
        self.write_single_register(0x1005, 0x5555)

        #set time-out/deactivate watchdog timer (deactivate: timeout = 0):
        self.write_single_register(0x1000, int(watchdog * 10))

        if watchdog:
            #configure watchdog to reset on all functions codes
            self.write_single_register(0x1001, 0xFFFF)

        #set process image offset
        self.next_output_word_offset = 0x0000
    