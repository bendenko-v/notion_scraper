# Notion Scraper

This Python script provides a simple yet effective Notion scraper that extracts exercises from a Notion page. It utilizes the Notion API to fetch data and extracts relevant information from the page URL.

## Features

- Fetches data from a Notion page using the Notion API.
- Extracts domain and page ID from a Notion page URL.
- Parses blocks of exercises from the fetched data, handling various block types.
- Outputs exercises in a readable format.

## Usage

1. Replace the 'url' variable with the Notion page link you want to scrape.
2. Run the script to get a list of parsed exercises.

**Note:** In the provided example, tasks in the Notion page are separated by dividers. The parsing results in an array of exercises, with tasks organized based on these dividers.

## Dependencies

- **aiohttp:** Asynchronous HTTP client for making API requests.
- **pydantic:** Data validation and settings management using Python type hints.

**Note:** Ensure you have the required dependencies installed before running the script.


