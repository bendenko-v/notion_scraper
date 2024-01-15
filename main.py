import asyncio
import json
import re
from urllib.parse import urlparse

import aiohttp
from pydantic import BaseModel


class Block(BaseModel):
    type_: list | str | None
    properties: dict | list | None


async def scrape(domain: str, page_id: str) -> dict[str, str]:
    """
    Scrapes data from a Notion page using the Notion API.

    Args:
        domain (str): The domain of the Notion workspace.
        page_id (str): The ID of the page to scrape.
    Returns:
        dict[str, str]: The scraped data if successful, or an error dictionary if unsuccessful.
    """
    url = f'https://{domain}/api/v3/loadPageChunk'
    payload = {
        "page": {
            "id": page_id,
        },
        "limit": 50,
        "cursor": {
            "stack": [],
        },
        "chunkNumber": 0,
        "verticalColumns": False,
    }
    try:
        async with aiohttp.ClientSession() as session:  # noqa SIM117
            async with session.post(
                    url, data=json.dumps(payload), headers={'Content-Type': 'application/json'},
            ) as response:
                if response.status == 200:
                    return await response.json()
                return {
                    "error": f'Could not connect to Notion, status: {response.status}, reason: {response.reason}',
                }
    except Exception as e:
        return {"error": f'Could not connect to Notion to parse tasks with id: {page_id}! Error: {str(e)}'}


def extract_domain_and_page_id_from_url(url: str) -> dict[str, str]:
    """
    Extract the domain and page ID from a given URL.

    Args:
        url (str): The URL from which to extract domain and page ID.

    Returns:
        dict[str, str]: A dictionary with the extracted domain and page ID, or
            a dictionary with an error message if the page_id length is not 32 symbols, or
            a dictionary with an error message if the url is not valid.
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path_parts = url.split("/")[1:]

        if '?' in path_parts[2]:  # noqa SIM108
            page_id = path_parts[2].split('?')[0][-32:]
        else:
            page_id = path_parts[2][-32:]

        pattern = r'^[a-zA-Z0-9]{32}$'
        if not re.match(pattern, page_id):
            return {'message': f'Could not extract page_id from url: {url}, page_id length is not 32 symbols'}

        page_id = page_id[:8] + '-' + page_id[8:12] + '-' + page_id[12:16] + '-' + page_id[16:20] + '-' + page_id[20:]
        return {'domain': domain, 'page_id': page_id}
    except Exception as e:
        return {'message': f'Could not extract domain and page_id from url: {url}. Error: {str(e)}'}


async def parse_exercises(data: dict) -> list[str]:
    """
    Parse the exercises from the given data dictionary.

    Args:
        data (dict): The data dictionary containing exercise blocks.

    Returns:
        list[str]: The parsed exercises as a list of strings.
    """
    filtered_data: list[Block] = [
        Block(type_=item['type'], properties=item.get('properties', {}))
        for item in [
            data['block'][block]['value']
            for block in data['block']
            if (
                    'properties' in data['block'][block]['value'] and
                    data['block'][block]['value'].get('type') != 'page' or
                    data['block'][block]['value'].get('type') == 'divider'
            )
        ]
    ]
    all_tasks = []
    task = []
    for block in filtered_data:
        title = block.properties.get('title')
        if title and 'header' in block.type_:
            task.append('<h3>' + title[0][0] + '</h3>')
        elif title and 'code' in block.type_:
            task.append('<pre class="ql-syntax">' + title[0][0] + '</pre>')
        elif block.type_ == 'divider':
            all_tasks.append(''.join(task))
            task = []
        elif title:
            text = []
            for i in title:
                if isinstance(i, str):
                    text.append(i)
                else:
                    text.append(i[0])
            task.append(''.join(text) + '<br>')

    all_tasks.append(''.join(task))
    return all_tasks


async def get_exercises_from_notion(link: str) -> list[str] | dict[str, str]:
    """
    Get exercises from a Notion page given a link.

    Args:
        link (str): The link to the Notion page.

    Returns:
        A list of exercise strings if successful, or a dictionary with an error message if unsuccessful.
    """
    extracted_data = extract_domain_and_page_id_from_url(link)

    if 'message' in extracted_data:
        return extracted_data

    domain = extracted_data.get('domain')
    page_id = extracted_data.get('page_id')

    data: dict = await scrape(domain, page_id)
    if error := data.get('error'):
        return {'message': error}
    try:
        records = data.get('recordMap')
        return await parse_exercises(records)
    except Exception as e:
        return {'message': f'Could not parse exercises from Notion: {link}. Error: {str(e)}'}


if __name__ == '__main__':
    # Example for getting exercises from a Notion page
    URL = 'https://it-cat.notion.site/0d91ec8678c64230b81f512855125d52?pvs=4'
    notion_data = asyncio.run(get_exercises_from_notion(URL))

    if 'message' not in notion_data:
        [
            print(f'== Block {str(num)} ==\n' + block + '\n== End of block ==\n')  # noqa T201
            for num, block in enumerate(notion_data, start=1)
        ]
    else:
        print(notion_data.get('message'))  # noqa T201
