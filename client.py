import asyncio
import logging
import conf
import struct
import binascii

from protocol import decoder, encoder
from avatar import Avatar


class Client(Avatar):
    def __init__(self, serv):
        self.serv = serv
        self.reader = None
        self.writer = None
        self.ip_adr = None

        super().__init__(self)

    async def handle(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self.ip_adr = writer.get_extra_info("peername")[0]
        logging.info(f"Connection from {self.ip_adr}")
        buffer: bytes = b""

        while True:
            try:
                raw_bytes = await reader.read(conf.BUFFER)
                if not raw_bytes: break
            except: break

            try:
                final_data = decoder.process(raw_bytes)
            except:
                buffer += raw_bytes
                continue

            if self.serv.debug:
                logging.debug(f"From server: {final_data}")
            
            buffer = b""

            await self.serv.process(final_data, self)
        
        await self.close()

    async def send(self, raw_data, m_type):
        if self.serv.debug:
            logging.debug(f"From client: {raw_data}, {m_type}")
        final_data: bytes = struct.pack(">b", m_type)
        final_data += encoder.encode_dict(raw_data)

        header: bytes = struct.pack(">i", len(final_data) + conf.HEADER_LENGTH)
        header += struct.pack(">B", conf.MASK)
        header += struct.pack(">I", binascii.crc32(final_data))

        final_data = header + final_data
        try:
            self.writer.write(final_data)
            await self.writer.drain()
        except (BrokenPipeError, ConnectionResetError, AssertionError,
                TimeoutError, OSError, AttributeError):
            self.writer.close()
        
    async def close(self):
        self.writer.close()
        
        if self.uid in self.serv.onl:

            del self.serv.onl[self.uid]

            if self.room:
                await self.rm.leave()

        logging.info(f"Connection close with {self.ip_adr}")

        del self
