#!/usr/bin/env python3

import time
from pyModbusTCP.client import ModbusClient

class ModBusBK9050(ModbusClient):
    """BK9050: Busskoppler ModBus TCP"""
    
    def __init__(self, host, port = 502, debug=False, timeout=5, watchdog=0):
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
        
        ModbusClient.__init__(self, host, port, auto_open=True, debug=debug, timeout=timeout, watchdog=watchdog)
        self.bus_terminals = list()
        self.next_output_bit_offset = 0
        self.next_input_bit_offset = 0
        self.next_output_word_offset = 0x800
        self.next_input_word_offset = 0
        
        #https://download.beckhoff.com/download/document/io/bus-terminals/bk9000_bk9050_bk9100de.pdf
        #config watchdog on page 58
        
        #set time-out/deactivate watchdog timer (deactivate: timeout = 0):
        self.write_single_register(0x1120, timeout * 1000) #ms
        
        #reset watchdog timer:
        self.write_single_register(0x1121, 0xBECF)
        self.write_single_register(0x1121, 0xAFFE)
    
    def read_discrete_input(self, address):
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
        
    def add_bus_terminals(self, bus_terminals):
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
    
    
class BusTerminal():
    output_bit_width = 0
    input_bit_width = 0
    output_word_width = 0
    input_word_width = 0

    def __init__(self, bus_coupler):
        self.output_bit_offset = 0
        self.input_bit_offset = 0
        self.output_word_offset = 0x800
        self.input_word_offset = 0
        self.bus_coupler = bus_coupler

class DigitalInputTerminal(BusTerminal):
    def read_input(self, channel):
        if channel < 1 or channel > self.input_bit_width:
            raise Exception("address out of range")
        return self.bus_coupler.read_discrete_input(self.input_bit_offset + channel - 1)

class DigitalOutputTerminal(BusTerminal):
    def write_coil(self, channel, value):
        if channel < 1 or channel > self.output_bit_width:
            raise Exception("address out of range")
        return self.bus_coupler.write_single_coil(self.output_bit_offset + channel - 1, value)

    def read_coil(self, channel):
        if channel < 1 or channel > self.output_bit_width:
            raise Exception("address out of range")
        return self.bus_coupler.read_coil(self.output_bit_offset + channel - 1)
    
class AnalogInputTerminal(BusTerminal):
    def read_words(self, word_offset, word_count):
        if word_offset < 0 or word_offset + word_count > self.input_word_width:
            raise Exception("address out of range")
        return self.bus_coupler.read_input_registers(self.input_word_offset + word_offset, word_count)
    
    def read_words_nocheck(self, word_offset, word_count):
        return self.bus_coupler.read_input_registers(self.input_word_offset + word_offset, word_count)
    
    def read_word(self, word_offset):
        val = self.read_words(word_offset, 1)
        if val is None:
            return -999
        else:
            return val[0]
            
    
class AnalogOutputTerminal(BusTerminal):
    def read_words(self, word_offset, word_count):
        if word_offset < 0 or word_offset + word_count > self.output_word_width:
            raise Exception("address out of range")
        return self.bus_coupler.read_holding_registers(self.output_word_offset + word_offset, word_count)
    
    def read_words_nocheck(self, word_offset, word_count):
        return self.bus_coupler.read_holding_registers(self.output_word_offset*0 + word_offset, word_count)
    
    def read_word(self, word_offset):
        val = self.read_words(word_offset, 1)
        if val is None:
            return -999
        else:
            return val[0]
    
    def write_word(self, word_offset, data):
        if word_offset < 0 or word_offset + 1 > self.output_word_width:
            raise Exception("address out of range")
        return self.bus_coupler.write_single_register(self.output_word_offset + word_offset, data)
    
    def write_word_nocheck(self, word_offset, data):
        return self.bus_coupler.write_single_register(self.output_word_offset*0 + word_offset, data)
    
class KL1104(DigitalInputTerminal):
    """KL1104: 4x digital input 24 V"""
    input_bit_width = 4

class KL2404(DigitalOutputTerminal):
    """KL2404: 4x digital output with 500 mA"""
    output_bit_width = 4
    
class KL2424(DigitalOutputTerminal):
    """KL2424: 4x digital output with 2000 mA"""
    output_bit_width = 4
    
class KL3054(AnalogInputTerminal):
    """KL3054: 4x analog input 4...20 mA 12 Bit single-ended"""
    #Input: 4 x 16 Bit Daten (optional 4x 8 Bit Control/Status)
    input_word_width = 8
    output_word_width = 8
    
    def read_normalized(self, channel):
        return self.read_word(channel*2-1) / 0x7FFF
    
    def read_current(self, channel):
        return self.read_normalized(channel) * 16.0 + 4.0
    
class KL3202(AnalogInputTerminal):
    """KL3202: 2x analog input PT100 16 Bit 3-wire"""
    #Input: 2 x 16 Bit Daten (2 x 8 Bit Control/Status optional)
    input_word_width = 4
    output_word_width = 4
    
    def read_temperature(self, channel):
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
    
    def read_temperature(self, channel):
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
    
    def set_normalized(self, channel, value):
        self.write_word(channel*2-1, int(value * 0x7FFF))
    
    def set_voltage(self, channel, value):
        self.set_normalized(value / 10.0)
        
class KL4004(AnalogOutputTerminal):
    """KL4004: 4x analog output 0...10 V 12 Bit differentiell"""
    #Output: 4 x 16 Bit Daten (optional 4 x 8 Bit Control/Status)
    input_word_width = 8
    output_word_width = 8
    
    def set_normalized(self, channel, value):
        self.write_word(channel*2-1, int(value * 0x7FFF))
    
    def set_voltage(self, channel, value):
        self.set_normalized(value / 10.0)
    
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

