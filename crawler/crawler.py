# crawler/crawler.py

from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests
import logging
import hashlib
import csv
import sys

class WebCrawler:
    def __init__(self, root_url, max_depth):
        """
        Initialize the WebCrawler with the root URL and maximum depth.
        :param root_url: The root URL to start crawling from.
        :param max_depth: The maximum depth to crawl.
        """
        self.setup_logging()
        self.root_url = self.fix_url(root_url)
        self.max_depth = max_depth
        self.visited_urls = set()
        self.visited_hashes = set()
        self.results = []
        # self.setup_logging()

    def setup_logging(self):
        """
        Set up the logging configuration for the crawler.
        """
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )

    def fix_url(self, url):
        """
        Ensure the URL has a scheme (http:// or https://). If missing, try adding 'http://' and 'https://' and check which one is reachable.
        and check which one is reachable.
        :param url: The URL to fix.
        :return: The URL with the correct scheme.
        """
        parsed = urlparse(url)          # Parse the URL into 6 components <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        if not parsed.scheme:
            url_variants = [
                'http://' + url,
                'https://' + url,
                'http://' + url.lstrip('www.'),
                'https://' + url.lstrip('www.')
            ]
            for full_url in url_variants:
                try:
                    response = requests.head(full_url, timeout=3)
                    if response.status_code < 400:
                        logging.info(f"No scheme provided. Using URL: {full_url}")
                        return full_url
                except requests.RequestException:
                    continue
            return None  # Return None instead of exiting
        return url

    def is_html(self, headers):
        """
        Check if the response content type is HTML.
        :param headers: The HTTP response headers.
        :return: True if the content type is HTML, False otherwise.
        """
        content_type = headers.get('Content-Type', '')
        return 'text/html' in content_type

    def get_links(self, html_content, base_url):
        """
        Extract all valid links from the HTML content, stripping fragment identifiers.
        :param html_content: The HTML content of the page.
        :param base_url: The base URL to resolve relative links.
        :return: A list of absolute URLs extracted from the page.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        for link_tag in soup.find_all('a', href=True):          # Iterate over all <a> tags with 'href' attributes
            href = link_tag['href'].strip()
            if not href or href.startswith(('javascript:', 'mailto:', 'tel:', 'ftp:')):
                continue
            try:
                full_url = urljoin(base_url, href)      # Resolve relative links - (only path without the domain)
                fixed_url = self.fix_url(full_url)      # Use fix_url to validate and fix the URL
                if not fixed_url:
                    continue    # Skip invalid URLs
                # Remove fragment identifiers
                parsed_url = urlparse(fixed_url)
                parsed_url = parsed_url._replace(fragment='')
                full_url = parsed_url.geturl()      # Reconstruct the URL without the fragment
                links.append(full_url)
            except Exception as e:
                logging.error(f"Invalid URL '{href}' found on page '{base_url}': {e}")
                continue
        return links

    def calculate_ratio(self, links, page_hostname):
        """
        Calculate the ratio of same-domain links on a page.
        :param links: A list of URLs extracted from the page.
        :param page_hostname: The hostname of the current page.
        :return: The ratio of same-domain links (between 0 and 1).
        """
        total_links = len(links)
        if total_links == 0:
            return 0.0
        same_domain_links = sum(1 for link in links if urlparse(link).hostname == page_hostname)
        ratio = same_domain_links / total_links
        return round(ratio, 2)

    def crawl(self):
        """
        Start the crawling process after fixing the root URL.
        """
        # Remove fragment identifiers from the root URL
        parsed_url = urlparse(self.root_url)
        self.root_url = parsed_url._replace(fragment='').geturl()

        with requests.Session() as self.session:        # Create a session for HTTP requests
            self._crawl(self.root_url, 1)

        self.save_results()

    def _crawl(self, current_url, depth):
        """
        Recursively crawl web pages starting from the current URL.
        :param current_url: The URL of the page to crawl.
        :param depth: The current depth level in the crawling process.
        """
        if depth > self.max_depth or current_url in self.visited_urls:
            return

        logging.info(f"Crawling URL: {current_url} at depth {depth}")

        try:
            response = self.session.get(current_url, timeout=10)
            response.raise_for_status()
            current_url = response.url      # Update URL in case of redirects
        except requests.RequestException as e:
            logging.error(f"Failed to fetch {current_url}: {e}")
            return

        # Check if the final current_url has been visited
        if current_url in self.visited_urls:
            return
        self.visited_urls.add(current_url)

        if not self.is_html(response.headers):
            logging.info(f"Non-HTML content at {current_url}, skipping.")
            return

        # Compute the hash of the page content
        content_hash = hashlib.sha256(response.text.encode('utf-8')).hexdigest()

        # Check if the content has been processed before
        if content_hash in self.visited_hashes:
            logging.info(f"Duplicate content at {current_url}, skipping processing.")
            return

        self.visited_hashes.add(content_hash)

        page_hostname = urlparse(current_url).hostname
        links = self.get_links(response.text, current_url)
        ratio = self.calculate_ratio(links, page_hostname)

        self.results.append({'url': current_url, 'depth': depth, 'ratio': ratio})

        for link in links:
            self._crawl(link, depth + 1)

    def save_results(self):
        """
        Save the crawling results to a TSV file named 'output.tsv'.
        """
        filename = 'output.tsv'
        if len(self.results) > 0:
            logging.info(f"Saving results to {filename}")
            # Ensure each URL appears exactly once in the output
            unique_results = {result['url']: result for result in self.results}     # {url: {'url':url, 'depth':depth, 'ratio':ratio}}
            with open(filename, 'w', newline='', encoding='utf-8') as tsvfile:
                fieldnames = ['url', 'depth', 'ratio']
                writer = csv.DictWriter(tsvfile, fieldnames=fieldnames, delimiter='\t')
                writer.writeheader()
                for result in unique_results.values():
                    writer.writerow(result)