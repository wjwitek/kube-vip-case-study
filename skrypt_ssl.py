import aiohttp
import asyncio
import ssl
import certifi
import argparse
import time

async def send_request(url, session, request_id):
    try:
        async with session.get(url, ssl=False) as response:
            result = await response.text()
            # print(f"{request_id}; {url}; status {response.status}")
            return response.status
    except Exception as e:
        # print(f"{request_id}; {url}; error {str(e)}")
        return None

async def main(url, num_requests, token):
    headers = {'Authorization': token}
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = []
        results = []
        start = time.time()
        for i in range(num_requests):
            task = send_request(url, session, i + 1)
            tasks.append(task)
            # await asyncio.sleep(1)  # Use await to sleep asynchronously
            # results.append(await task)
            # time.sleep(0.001)
        results = await asyncio.gather(*tasks)
        end = time.time()
        print((end - start) / num_requests)
        # print(f"{results.count(200)} / {num_requests}")
        return (end - start) / num_requests

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test an API using aiohttp with SSL certificates")
    parser.add_argument("url", type=str, help="The URL to test")
    parser.add_argument("num_requests", type=int, help="Number of requests to send to the URL")
    parser.add_argument("token", type=str, help="Bearer token")
    
    args = parser.parse_args()

    # Run the asynchronous tasks
    results = []
    for i in range(2000):
        results.append(asyncio.run(main(args.url, args.num_requests, args.token)))
    print(f"Average: {sum(results) / 2000}")

