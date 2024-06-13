import aiohttp
import asyncio
import ssl
import certifi
import argparse

async def send_request(url, session, request_id):
    try:
        async with session.get(url) as response:
            result = await response.text()
            print(f"{request_id}; {url}; {response.status}")
            return result
    except Exception as e:
        print(f"{request_id}; {url}; {str(e)}")
        return None

async def main(url, num_requests, ssl_context):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        tasks = []
        for i in range(num_requests):
            task = send_request(url, session, i + 1)
            tasks.append(task)
            await asyncio.sleep(5)  # Use await to sleep asynchronously
        results = await asyncio.gather(*tasks)
        return results

if _name_ == "_main_":
    parser = argparse.ArgumentParser(description="Test an API using aiohttp with SSL certificates")
    parser.add_argument("url", type=str, help="The URL to test")
    parser.add_argument("num_requests", type=int, help="Number of requests to send to the URL")
    parser.add_argument("ca_cert", type=str, help="Path to CA certificate file")
    parser.add_argument("client_cert", type=str, help="Path to client certificate file")
    parser.add_argument("client_key", type=str, help="Path to client key file")
    
    args = parser.parse_args()

    # SSL context setup
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    ssl_context.load_cert_chain(certfile=args.client_cert, keyfile=args.client_key)
    ssl_context.load_verify_locations(cafile=args.ca_cert)

    # Run the asynchronous tasks
    asyncio.run(main(args.url, args.num_requests, ssl_context))