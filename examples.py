import asyncio
from pyefa.client import EfaClient
from pprint import pprint


async def find_stops(client):
    # find plärrer station
    stops = await client.find_stop("Nürnberg Plärrer")
    pprint(stops)

    stops = await client.find_stop("Plärrer")
    pprint(stops)


async def main():
    async with EfaClient("https://efa.vgn.de/vgnExt_oeffi/") as client:
        result = await asyncio.gather(
            client.system_info(),
            client.find_stop("Nürnberg Plärrer"),
            client.departures("de:09564:704", limit=10, date="20241126 16:30"),
        )

    print("System Info".center(60, "-"))
    pprint(result[0])

    print("Plärrer stops".center(60, "-"))
    pprint(result[1])

    print("Plärrer departures - 26 Nov. 16:30".center(60, "-"))
    pprint(result[2])


if __name__ == "__main__":
    asyncio.run(main())
