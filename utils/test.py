import asyncio

loop = asyncio.get_event_loop()

async def my_script():
    print("Start")
    await asyncio.sleep(1)
    print("End")

loop.run_forever()


