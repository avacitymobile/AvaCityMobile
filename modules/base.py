import logging
import traceback


class Module:
    def __init__(self):
        self.commands = {}

    async def on_message(self, msg, client):
        subcommand = msg["command"].split(".")[1]
        if subcommand not in self.commands:
            logging.info(f"Command {msg['command']} not found")
            return
        try:
            await self.commands[subcommand](msg, client)
        except:
            logging.error(traceback.format_exc())