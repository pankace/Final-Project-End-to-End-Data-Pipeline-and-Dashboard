class MT5WebSocketClient:
    def __init__(self, server_url, symbols, storage_handler):
        self.server_url = server_url
        self.symbols = symbols
        self.storage_handler = storage_handler
        self.is_running = False

    async def connect(self):
        self.is_running = True
        while self.is_running:
            try:
                async with websockets.connect(self.server_url) as ws:
                    subscription = {
                        "type": "subscription",
                        "action": "subscribe",
                        "symbols": self.symbols
                    }
                    await ws.send(json.dumps(subscription))

                    while self.is_running:
                        message = await ws.recv()
                        data = json.loads(message)

                        if data.get("type") == "price_update":
                            await self.storage_handler.save_price_data(
                                data.get("symbol"),
                                data.get("bid"),
                                data.get("ask"),
                                data.get("spread"),
                                data.get("timestamp")
                            )
                        elif data.get("type") == "error":
                            logger.error(f"Server error: {data.get('message')}")

            except Exception as e:
                logger.error(f"Error in WebSocket connection: {e}")

    def stop(self):
        self.is_running = False