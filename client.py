
import logging
import conf
import struct
import binascii
import asyncio
from protocol import decoder, encoder
from avatar import Avatar

class Client(Avatar):
    def __init__(self, serv):
        super().__init__(self)
        self.serv = serv
        self.ip_adr = None
        self.reader = None
        self.writer = None

    async def handle(self, reader, writer):
        self.ip_adr = writer.get_extra_info("peername")[0]
        logging.info(f"Соединение с {self.ip_adr}")

        self.reader = reader
        self.writer = writer

        try:
            while True:
                raw_bytes = await reader.read(conf.BUFFER)
                if not raw_bytes:
                    break

                try:
                    final_data = decoder.process(raw_bytes)
                except Exception as e:
                    logging.error(f"Ошибка декодирования данных: {e}")
                    continue

                if self.serv.debug:
                    logging.debug(f"От сервера: {final_data}")

                await self.serv.process(final_data, self)

        except Exception as e:
            logging.error(f"Ошибка в обработке: {e}")

        finally:
            await self.close()

    async def send(self, raw_data, m_type):
        try:
            if self.serv.debug:
                logging.debug(f"От клиента: {raw_data}, {m_type}")
            final_data = struct.pack(">b", m_type) + encoder.encode_dict(raw_data)

            header = struct.pack(">iB", len(final_data) + conf.HEADER_LENGTH, conf.MASK)
            header += struct.pack(">I", binascii.crc32(final_data))

            final_data = header + final_data
            
            self.writer.write(final_data)
            await self.writer.drain()
        except (BrokenPipeError, ConnectionResetError, AssertionError,
                TimeoutError, OSError, AttributeError) as e:
            logging.error(f"Ошибка отправки данных: {e}")
            self.writer.close()

    async def close(self):
        if self.writer:
            self.writer.close()

        if self.uid in self.serv.onl:
            del self.serv.onl[self.uid]

            if self.room:
                await self.rm.leave()

        logging.info(f"Соединение закрыто с {self.ip_adr}")