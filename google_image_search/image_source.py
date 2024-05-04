import os
import asyncio
from dotenv import load_dotenv
from pathlib import Path
import json
from apify_client import ApifyClientAsync


load_dotenv()

apify_key = os.getenv('apify_key')

async_apify_client = ApifyClientAsync(apify_key)


async def async_search_image_source(
    images_url: list[str]
) -> list:
    """Async search of similar images using Google Lens."""
    
    run_input = {
        'startUrls': [{'url': url} for url in images_url],
        'proxyConfiguration': {'userApifyProxy': True}
    }
    
    run = await async_apify_client.actor('useful-tools/google-lens-image-sources').call(run_input=run_input)
    
    return [item async for item in async_apify_client.dataset(run['defaultDatasetId']).iterate_items()]


def search_image_source(
    images_url: list[str]
) -> list:
    return asyncio.run(async_search_image_source(images_url))


if __name__ == '__main__':
    # example
    with open(Path(__file__).parent / 'output.json', 'w') as file:
        file.write(
            json.dumps(
                search_image_source(['https://www.bmbf.de/SharedDocs/Bilder/en/bmbf/bmbfcluster/189.jpg?__blob=poster&v=1']),
                indent=4
            )
        )
