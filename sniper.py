import json
import time
import asyncio
import aiohttp
import websockets

# Load configuration
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

guilds = {}

async def send_message(content):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"https://canary.discord.com/api/v10/channels/{config['infoChannelId']}/messages",
                json={'content': content},
                headers={
                    'Authorization': config['sniperToken'],
                    'Content-Type': 'application/json',
                }
            ) as response:
                if response.status != 200:
                    print(f"Error sending message: {response.status}")
        except Exception as e:
            print(f"Error sending message: {e}")

async def update_vanity_url(guild, guild_id):
    start = time.time()
    async with aiohttp.ClientSession() as session:
        try:
            async with session.patch(
                f"https://canary.discord.com/api/v10/guilds/{config['sniperGuild']}/vanity-url",
                json={'code': guild},
                headers={
                    'Authorization': config['sniperToken'],
                    'Content-Type': 'application/json',
                }
            ) as response:
                elapsed_seconds = (time.time() - start) * 1000
                if response.status == 200:
                    content = f"`{guild}` CODE: `{response.status}` SPEED: <(`{elapsed_seconds}`:MS)> @everyone"
                else:
                    content = f"Error getting vanity: `{guild}` SPEED: (`{elapsed_seconds}`:MS) CODE: `{response.status}` @everyone HOPPİDİKKKKK"
                await send_message(content)
        finally:
            guilds.pop(guild_id, None)

async def handle_message(data):
    if data['t'] == "GUILD_UPDATE":
        guild_id = data['d']['guild_id']
        guild = guilds.get(guild_id)
        if (guild or data['d']['vanity_url_code']) != data['d']['vanity_url_code']:
            await update_vanity_url(guild, guild_id)
    elif data['t'] == "GUILD_DELETE":
        guild_id = data['d']['id']
        guild = guilds.get(guild_id)
        if guild:
            await update_vanity_url(guild, guild_id)
    elif data['t'] == "READY":
        for guild in data['d']['guilds']:
            if 'vanity_url_code' in guild:
                guilds[guild['id']] = guild['vanity_url_code']
        print(guilds)

async def heartbeat(ws, interval):
    while True:
        await asyncio.sleep(interval)
        await ws.send(json.dumps({'op': 1, 'd': None}))

async def connect_websocket():
    async with websockets.connect("wss://gateway.discord.gg/?v=10&encoding=json") as ws:
        async for message in ws:
            data = json.loads(message)
            if data['op'] == 10:
                await ws.send(json.dumps({
                    'op': 2,
                    'd': {
                        'token': config['listenerToken'],
                        'intents': 1 << 0,
                        'properties': {
                            'os': 'macos',
                            'browser': 'Safari',
                            'device': 'MacBook Air',
                        },
                    },
                }))
                heartbeat_interval = data['d']['heartbeat_interval'] / 1000
                asyncio.create_task(heartbeat(ws, heartbeat_interval))
            await handle_message(data)

if __name__ == "__main__":
    asyncio.run(connect_websocket())
