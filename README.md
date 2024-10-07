# Web Crawler

## Overview
The WebCrawler project is a Python-based tool designed to traverse web pages starting from a given root URL, 
recursively crawling pages up to a specified depth. It extracts and processes links from each page, 
calculating the ratio of same-domain links (those with the same hostname as the page) to the total number of links. 
The results are saved in a tab-separated values (TSV) file.


## Features
- **Depth Control**: Specify the maximum depth to control the crawl scope.
- **Link Extraction**: Extracts valid HTTP and HTTPS links from web pages.
- **Duplicate Content Detection**: Avoids processing pages with duplicate content using content hashing.
- **Fragment Handling**: Correctly processes links with fragment identifiers, avoiding redundant crawling.
- **Non-HTML Content Skipping**: Skips non-HTML resources to focus on web pages.
- **Error Handling**: Gracefully handles network errors, invalid URLs, and timeouts.
- **Logging**: Provides informative logging throughout the crawling process.
- **Output Generation**: Produces an output.tsv file with the crawled URLs, their depths, and the ratio of same-domain links.

## Project Structure
project_root/<br>
├── crawler/<br>
│   ├── __init__.py<br>
│   └── crawler.py<br>
├── tests/<br>
│   ├── __init__.py<br>
│   └── test_crawler.py<br>
├── main.py<br>
├── requirements.txt<br>
└── README.md

- **crawler/**: A package containing the crawler logic.
  - **init.py**: Initializes the crawler package.
  - **crawler.py**: Implements the WebCrawler class with all crawling logic and methods required.
- **tests/**: Contains unit tests for the project.
  - **init.py**: Initializes the tests package.
  - **test_crawler.py**: Contains comprehensive tests covering various scenarios and edge cases.
- **main.py**: The entry point of the application. It parses command-line arguments and initiates the crawler.
- **requirements.txt**: Lists all the Python packages required to run the project.
- **README.md**: Provides documentation and instructions for the project.

## Dependencies
The project uses the following Python packages and was developed with **Python 3.9**:
- **requests**: For making HTTP requests.
- **beautifulsoup4**: For parsing HTML content and extracting links.
- **urllib3**: For URL parsing and manipulation.
- **hashlib**: For computing content hashes.
- **logging**: For logging information and errors.
- **csv**: For writing the output TSV file.
- **unittest**: For writing and running tests.
- **unittest.mock**: For mocking in tests.

## Install dependencies:
All dependencies are specified in the `requirements.txt` file and can be installed `pip`:
```bash
pip install -r requirements.txt
```

##Run the crawler using:
```python main.py <root_url> <depth_limit>```
- `<root_url>`: The starting URL for the crawler.
- `<depth_limit>`: The maximum depth to crawl (positive integer). <br>

**Note: If the <root_url> contains special characters like &, make sure to enclose it in single or double quotes to prevent shell interpretation issues. For example:**
```
python main.py 'https://example.com/search?q=test&lang=en' 2
```

##Output
The crawler outputs a TSV file named output.tsv containing:
- `url`: The full URL of the crawled page.
- `depth`: The depth at which the page was found.
- `ratio`: The ratio of same-domain links on the page.


## Testing
The project includes tests for most edge cases to ensure reliability.
### Running the Tests
Execute all tests using:
```
python -m unittest discover tests
```

### Test Coverage
The tests cover a wide range of scenarios, including:
- Valid and Invalid Links
- HTTP Redirects
- Depth Limit Enforcement
- Duplicate Content Handling
- Non-HTML Content Skipping
- Error and Exception Handling
- Other edge Cases


## Design Overview
* **Modularity**: The project is divided into modules (crawler and tests packages and main.py) for easy modification, extension, and better organization.
* **Error Handling**: The crawler handles exceptions and logs errors without crashing.

## Future Improvements
- **Asynchronous Requests**: To improve performance with concurrent crawling.
- **Implement `robots.txt` Parsing**: Adding functionality to parse and respect robots.txt files to adhere to websites' crawling policies.
- **Customization**: Adding command-line options for more control.

<br>

### Asynchronous Version Implementation
To improve performance, I implemented an asynchronous version of the crawler using `asyncio` and `aiohttp` for concurrent HTTP requests. The code was refactored with `async def` functions and `await` for asynchronous operations. Concurrency issues, such as race conditions when accessing shared resources, were handled using `asyncio.Lock`.
However, since the assignment didn’t explicitly require asynchronous implementation, I submitted the synchronous version to ensure full compliance with the given requirements.


## Author
### Nadav Ishai