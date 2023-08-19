import struct
import logging


class Cursor:
    def __init__(self, data):
        self.pos: int = 9
        self.raw_data: bytes = data

    def read(self, amount: int):
        if self.pos + amount > len(self.raw_data):
            raise ValueError("I can't read what there")
        old_pos = self.pos
        self.pos += amount
        return self.raw_data[old_pos:self.pos]
    
    def read_i8(self):
        return struct.unpack(">b", self.read(1))[0]
    
    def read_u8(self):
        return struct.unpack(">B", self.read(1))[0]
    
    def read_i32(self):
        return struct.unpack(">i", self.read(4))[0]
    
    def read_i64(self):
        return struct.unpack(">q", self.read(8))[0]
    
    def read_f64(self):
        return struct.unpack(">d", self.read(8))[0]
    
    def debug(self):
        logging.debug(self.raw_data[self.pos:])


def process(raw_data: bytes):
    cur = Cursor(raw_data)
    
    message_type: int = cur.read_i8()
    message: dict = decode_dictionary(cur)

    return {"msg": message, "type": message_type}

def decode_value(cur: Cursor):
    match cur.read_i8():
        case 0: return None
        case 1: return bool(cur.read_i8())
        case 2: return cur.read_i32()
        case 3: return cur.read_i64()
        case 4: return cur.read_f64()
        case 5: return decode_string(cur)
        case 6: return decode_dictionary(cur)
        case 7: return decode_list(cur)
    raise ValueError("Wrong data type...")
        
def decode_string(cur: Cursor):
    length: int = struct.unpack(">h", cur.read(2))[0]
    return cur.read(length).decode()

def decode_dictionary(cur: Cursor):
    result: dict = {}
    count: int = cur.read_i32()
    for _ in range(count):
        key = decode_string(cur)
        result[key] = decode_value(cur)
    return result

def decode_list(cur: Cursor):
    result: list = []
    count: int = cur.read_i32()
    for _ in range(count):
        result.append(decode_value(cur))
    return result
