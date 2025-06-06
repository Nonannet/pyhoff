import socket
import struct
import random

_READ_COILS = 0x01
_READ_DISCRETE_INPUTS = 0x02
_READ_HOLDING_REGISTERS = 0x03
_READ_INPUT_REGISTERS = 0x04
_WRITE_SINGLE_COIL = 0x05
_WRITE_SINGLE_REGISTER = 0x06
_WRITE_MULTIPLE_COILS = 0x0F
_WRITE_MULTIPLE_REGISTERS = 0x10

_modbus_exceptions = {
    0x01: 'illegal function',
    0x02: 'illegal data address',
    0x03: 'illegal data value',
    0x04: 'slave device failure',
    0x05: 'acknowledge',
    0x06: 'slave device busy',
    0x07: 'negative acknowledge',
    0x08: 'memory parity error',
    0x0A: 'gateway path unavailable',
    0x0B: 'gateway target device failed to respond'
}


def _get_bits(data: bytes, bit_number: int) -> list[bool]:
    return [bool(data[i // 8] >> (i % 8) & 0x01)
            for i in range(bit_number)]


def _get_words(data: bytes) -> list[int]:
    return [(data[i * 2] << 8) + data[i * 2 + 1]
            for i in range(len(data) // 2)]


def _from_bits(values: list[bool]) -> bytes:
    return bytes(sum(((1 << j) * bool(values[8 * i + j]))
                     for j in range(8)) for i in range(len(values) // 8))


def _from_words(values: list[int]) -> bytes:
    return b''.join(word.to_bytes(2, byteorder='big') for word in values)


class SimpleModbusClient:
    """
    A simple Modbus TCP client

    Attributes:
        host (str): hostname or IP address
        port (int): server port
        unit_id (int): ModBus id
        timeout (float): socket timeout in seconds
        last_error (str): contains last error message or empty string if no error occurred
        debug (bool): if True prints out transmitted and received bytes in hex

    """

    def __init__(self, host: str, port: int = 502, unit_id: int = 1, timeout: float = 5, debug: bool = False):
        """
        Instantiate a Modbus TCP client

        Args:
            host: hostname or IP address
            port: server port
            unit_id: ModBus id
            timeout: socket timeout in seconds
            debug: if True prints out transmitted and received bytes in hex

        Example:
            >>> client = SimpleModbusClient('localhost', port = 502, unit_id = 1)
            >>> print(client.read_coils(0, 10))
            >>> print(client.read_discrete_inputs(0, 10))
            >>> print(client.read_holding_registers(0, 10))
            >>> print(client.read_input_registers(0, 10))
            >>> print(client.write_single_coil(0, True))
            >>> print(client.write_single_register(0, 1234))
            >>> print(client.write_multiple_coils(0, [True, False, True]))
            >>> print(client.write_multiple_registers(0, [1234, 5678]))
            >>> client.close()
        """
        assert 0 <= unit_id < 256

        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self.last_error = ''
        self._transaction_id = random.randint(0, 0xFFFF)
        self._socket: None | socket.socket = None
        self.debug = debug

    def connect(self) -> bool:
        """
        Connect manual to the configured modbus server. Usually there is
        no need to call this function since it is handled automatically.
        """
        for af, st, pr, _, sa in socket.getaddrinfo(self.host, self.port,
                                                    socket.AF_UNSPEC,
                                                    socket.SOCK_STREAM):
            try:
                self._socket = socket.socket(af, st, pr)
            except socket.error:
                self.close()
                continue
            try:
                self._socket.settimeout(self.timeout)
                self._socket.connect(sa)
            except socket.error:
                self.close()
                continue
            break

        if self._socket:
            return True
        else:
            self.last_error = 'connection failed'
            return False

    def close(self) -> bytes:
        """
        Close connection

        Returns:
            empty bytes object
        """
        if self._socket:
            self._socket.close()
            self._socket = None

        return bytes()

    def read_coils(self, bit_address: int, bit_lengths: int = 1) -> list[bool] | None:
        """
        ModBus function for reading coils (0x01)

        Args:
            bit_address: Bit address (0 to 0xffff)
            bit_lengths: Number of bits to read (1 to 2000)

        Returns:
            list of bool or None: Bits list or None if error
        """
        assert 1 <= bit_lengths <= 2000, 'bit_lengths out of range'
        assert bit_address + bit_lengths <= 0xffff, 'read after address 0xffff'

        if not self.send_modbus_data(_READ_COILS, _from_words([bit_address, bit_lengths])):
            return None

        rx_data = self.receive_modbus_data()
        if not rx_data:
            return None

        if len(rx_data) < 2:
            self.last_error = 'received frame under min size'
            return None

        byte_count = rx_data[0]
        bit_data = rx_data[1:]

        if not (byte_count * 8 >= bit_lengths and
                byte_count == len(bit_data)):
            self.last_error = 'received frame size mismatch'
            return None

        return _get_bits(bit_data, bit_lengths)

    def read_discrete_inputs(self, bit_address: int, bit_lengths: int = 1) -> list[bool] | None:
        """
        ModBus function for reading discrete inputs (0x02)

        Args:
            bit_address: Bit address (0 to 0xffff)
            bit_lengths: Number of bits to read (1 to 2000)

        Returns:
            list of bool or None: Bits list or None if error
        """
        assert 1 <= bit_lengths <= 2000, 'bit_lengths out of range'
        assert bit_address + bit_lengths <= 0xffff, 'read after address 0xffff'

        if not self.send_modbus_data(_READ_DISCRETE_INPUTS, _from_words([bit_address, bit_lengths])):
            return None

        rx_data = self.receive_modbus_data()
        if not rx_data:
            return None

        if len(rx_data) < 2:
            self.last_error = 'received frame under minimum size'
            return None

        byte_count = rx_data[0]
        bit_data = rx_data[1:]

        if not (byte_count * 8 >= bit_lengths and
                byte_count == len(bit_data)):
            self.last_error = 'received frame size mismatch'
            return None

        return _get_bits(bit_data, bit_lengths)

    def read_holding_registers(self, register_address: int, word_lengths: int = 1) -> list[int] | None:
        """
        ModBus function for reading holding registers (0x03)

        Args:
            register_address: Register address (0 to 0xffff)
            word_lengths: Number of registers to read (1 to 125)

        Returns:
            list of int or None: Registers list or None if error
        """
        assert 1 <= word_lengths <= 125, 'word_lengths out of range'
        assert register_address + word_lengths <= 0xffff, 'read after address 0xffff'

        if not self.send_modbus_data(_READ_HOLDING_REGISTERS, _from_words([register_address, word_lengths])):
            return None

        rx_data = self.receive_modbus_data()
        if not rx_data:
            return None

        if len(rx_data) < 2:
            self.last_error = 'received frame under minimum size'
            return None

        byte_count = rx_data[0]
        reg_data = rx_data[1:]

        if not (byte_count == 2 * word_lengths and
                byte_count == len(reg_data)):
            self.last_error = 'received frame size mismatch'
            return None

        return _get_words(reg_data)

    def read_input_registers(self, register_address: int, word_lengths: int = 1) -> list[int] | None:
        """
        ModBus function for reading input registers (0x04)

        Args:
            register_address: Register address (0 to 0xffff)
            word_lengths: Number of registers to read (1 to 125)

        Returns:
            list of int or None: Registers list or None if error
        """
        assert 1 <= word_lengths <= 125, 'word_lengths out of range'
        assert register_address + word_lengths <= 0xffff, 'read after address 0xffff'

        if not self.send_modbus_data(_READ_INPUT_REGISTERS, _from_words([register_address, word_lengths])):
            return None

        rx_data = self.receive_modbus_data()
        if not rx_data:
            return None

        if len(rx_data) < 2:
            self.last_error = 'received frame under minimum size'
            return None

        byte_count = rx_data[0]
        reg_data = rx_data[1:]

        if not (byte_count == 2 * word_lengths and
                byte_count == len(reg_data)):
            self.last_error = 'received frame size mismatch'
            return None

        return _get_words(reg_data)

    def write_single_coil(self, bit_address: int, value: bool) -> bool:
        """
        ModBus function for writing a single coil (0x05)

        Args:
            bit_address: Bit address (0 to 0xffff)
            value: Value to write (single bit)

        Returns:
            True if write succeeded or False if failed
        """
        assert 0 <= bit_address <= 0xffff, 'bit_address out of range'

        tx_data = _from_words([bit_address, 0xFF00 * bool(value)])
        if not self.send_modbus_data(_WRITE_SINGLE_COIL, tx_data):
            return False

        data = self.receive_modbus_data()
        if not data:
            return False

        if len(data) != 4:
            self.last_error = 'received frame size mismatch'
            return False

        return data == tx_data

    def read_discrete_input(self, address: int) -> bool | None:
        """
        Read a discrete input from the given register address.

        Args:
            address: The register address to read from.

        Returns:
            The value of the discrete input.
        """
        value = self.read_discrete_inputs(address)
        if value:
            return value[0]
        else:
            return None

    def read_coil(self, address: int) -> bool | None:
        """
        Read a coil from the given register address.

        Args:
            address: The register address to read from.

        Returns:
            The value of the coil or None if error
        """
        value = self.read_coils(address)
        if value:
            return value[0]
        else:
            return None

    def write_single_register(self, register_address: int, value: int) -> bool:
        """
        ModBus function for writing a single register (0x06)

        Args:
            register_address: Register address (0 to 0xffff)
            value: Value to write (0 to 0xffff)

        Returns:
            True if write succeeded or False if failed
        """
        assert 0 <= register_address <= 0xffff, 'register_address out of range'
        assert 0 <= value <= 0xffff, 'value out of range 0 to 0xffff'

        tx_data = _from_words([register_address, value])
        if not self.send_modbus_data(_WRITE_SINGLE_REGISTER, tx_data):
            return False

        data = self.receive_modbus_data()
        if not data:
            return False

        if len(data) != 4:
            self.last_error = 'received frame size mismatch'
            return False

        return data == tx_data

    def write_multiple_coils(self, bit_address: int, values: list[bool]) -> bool:
        """
        ModBus function for writing multiple coils (0x0F)

        Args:
            bit_address: Bit address (0 to 0xffff)
            values: List of bit values to write

        Returns:
            True if write succeeded or False if failed
        """
        assert bit_address + len(values) <= 0xffff, 'bit_address out of range'
        assert 1 <= len(values) <= 2000, 'number values must be from 1 to 2000'

        byte_count = (len(values) + 7) // 8
        tx_data = struct.pack('>HHB', bit_address, len(values), byte_count) + _from_bits(values)
        if not self.send_modbus_data(_WRITE_MULTIPLE_COILS, tx_data):
            return False

        data = self.receive_modbus_data()
        if not data:
            return False

        if len(data) != 4:
            self.last_error = 'received frame size mismatch'
            return False

        return _get_words(data[0:1])[0] == bit_address

    def write_multiple_registers(self, register_address: int, values: list[int]) -> bool:
        """
        ModBus function for writing multiple registers (0x10)

        Args:
            register_address: Register address (0 to 0xffff)
            values: List of 16 bit register values to write

        Returns:
            True if write succeeded or False if failed
        """
        assert register_address + len(values) <= 0xffff, 'register_address out of range'
        assert max(values) <= 0xffff, 'value out of range 0 to 0xffff'
        assert min(values) >= 0, 'value out of range 0 to 0xffff'

        byte_count = len(values) * 2
        tx_data = struct.pack('>HHB', register_address, len(values), byte_count) + _from_words(values)
        if not self.send_modbus_data(_WRITE_MULTIPLE_REGISTERS, tx_data):
            return False

        data = self.receive_modbus_data()
        if not data:
            return False

        if len(data) != 4:
            self.last_error = 'received frame size mismatch'
            return False

        return _get_words(data[0:1])[0] == register_address

    def _recv(self, number_of_bytes: int) -> bytes:
        """
        Receive data over tcp, wait until all specified bytes are received

        Args:
            number_of_bytes: Number of bytes to receive

        Returns:
            returns received bytes or empty an bytes object if an error occurred
        """
        if not self._socket:
            return bytes()

        buffer = bytes()
        while len(buffer) < number_of_bytes:
            try:
                tx_data = self._socket.recv(number_of_bytes - len(buffer))
            except socket.error:
                return bytes()

            if tx_data:
                buffer += tx_data
            else:
                return bytes()

        if self.debug:
            print(f"<- Received: {' '.join(hex(b) for b in buffer)}")

        return buffer

    def _send(self, data: bytes) -> int:
        """
        Send data over tcp

        Args:
            data: data to send

        Returns:
            number of transmitted bytes or 0 if transmission failed
        """

        for _ in range(2):
            if self._socket:
                try:
                    self._socket.sendall(data)
                    if self.debug:
                        print(f"-> Send:     {' '.join(hex(b) for b in data)}")
                    return len(data)
                except socket.error:
                    self.last_error = 'sending data failed'
                    self.close()
                    self.connect()
            else:
                self.connect()

        return 0

    def send_modbus_data(self, function_code: int, body: bytes) -> int:
        """
        Send raw ModBus TCP frame

        Args:
            unction_code: ModBus function code
            body: data

        Returns:
            number of transmitted bytes or 0 if transmission failed
        """
        self._transaction_id = (self._transaction_id + 1) % 0x10000
        protocol_identifier = 0
        length = len(body) + 2
        header = struct.pack('>HHHBB', self._transaction_id,
                             protocol_identifier, length, self.unit_id,
                             function_code)
        frame = header + body

        return self._send(frame)

    def receive_modbus_data(self) -> bytes:
        """
        Receive a ModBus frame

        Returns:
            bytes received or empty bytes object if an error occurred
        """
        header = self._recv(7)
        if not header:
            self.last_error = 'receiving return frame failed'
            return self.close()

        transaction_id, protocol_identifier, length, unit_id =\
            struct.unpack('>HHHB', header)

        if not ((transaction_id == self._transaction_id) and
                (protocol_identifier == 0) and
                (unit_id == self.unit_id) and
                (length <= 0xFF) and
                (transaction_id == self._transaction_id)):
            self.last_error = 'received frame is invalid'
            return self.close()

        data = self._recv(length - 1)
        if not data:
            self.last_error = 'receiving data payload failed'
            return self.close()

        if data[0] > 0x80:
            self.last_error = f"return error: {_modbus_exceptions.get(data[1], '')} ({data[1]})"
            if self.debug:
                print(self.last_error)
            return bytes()

        return data[1:]
