from pyhoff.modbus import _get_bits, _get_words, _from_bits, _from_words


def test_get_bits():
    data = bytes([0b11101010, 0b11010101])
    bit_number = 16
    expected = [False, True, False, True, False, True, True, True,
                True, False, True, False, True, False, True, True]
    result = _get_bits(data, bit_number)
    assert result == expected


def test_get_words():
    data = bytes([0x12, 0x34, 0x56, 0x78])
    expected = [0x1234, 0x5678]
    result = _get_words(data)
    assert result == expected


def test_from_bits():
    values = [False, True, False, True, False, True, True, True,
              True, False, True, False, True, False, True, True]
    expected = bytes([0b11101010, 0b11010101])
    result = _from_bits(values)
    assert result == expected


def test_from_words():
    values = [0x1234, 0x5678]
    expected = bytes([0x12, 0x34, 0x56, 0x78])
    result = _from_words(values)
    assert result == expected
