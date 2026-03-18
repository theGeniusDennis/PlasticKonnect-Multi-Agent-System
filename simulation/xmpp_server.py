# simulation/xmpp_server.py
# Starts an embedded pyjabber XMPP server as a background asyncio task.
# Import and call start_xmpp_server() before launching any SPADE agents.

from loguru import logger as _loguru
_loguru.remove()  # strip pyjabber's default loguru handler entirely

import asyncio
import logging
from pyjabber.server import Server
from pyjabber.server_parameters import Parameters

for _noisy in ("pyjabber", "slixmpp", "spade", "aioxmpp", "aioopenssl"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

_server_task = None


async def start_xmpp_server(host: str = "localhost", port: int = 5222) -> asyncio.Task:
    """
    Start pyjabber in the background and wait until it is ready to accept connections.
    Returns the running asyncio Task (cancel it to stop the server).
    """
    global _server_task

    params = Parameters(
        host=host,
        client_port=port,
        database_in_memory=True,   # no .db file written to disk
        database_purge=True,       # start fresh every run
        message_persistence=False,
    )
    server = Server(param=params)

    _server_task = asyncio.create_task(server.start())

    # Give the server a moment to bind its port
    await asyncio.sleep(1.5)
    logger.info(f"[XMPP] pyjabber server ready on {host}:{port}")
    print(f"[XMPP] Server started on {host}:{port}")
    return _server_task


async def stop_xmpp_server():
    global _server_task
    if _server_task and not _server_task.done():
        _server_task.cancel()
        try:
            await _server_task
        except asyncio.CancelledError:
            pass
    print("[XMPP] Server stopped.")
