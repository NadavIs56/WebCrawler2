# tests/test_crawler.py

from unittest.mock import patch, Mock
from crawler import WebCrawler
import unittest
import requests


class TestWebCrawler(unittest.TestCase):
    def setUp(self):
        """Set up common variables and initialize the WebCrawler instance."""
        self.root_url = 'http://www.example.com'
        self.max_depth = 2
        self.crawler = WebCrawler(self.root_url, self.max_depth)

    @patch('crawler.crawler.requests.Session.get')
    def test_link_extraction_with_various_schemes(self, mock_get):
        """
        Test that get_links correctly filters out links with unsupported schemes.
        """
        html_content = '''
            <html>
                <body>
                    <a href="http://www.example.com/page1">HTTP Link</a>
                    <a href="https://www.example.com/page2">HTTPS Link</a>
                    <a href="javascript:void(0);">JavaScript Link</a>
                    <a href="mailto:someone@example.com">Mailto Link</a>
                    <a href="tel:+1234567890">Tel Link</a>
                    <a href="ftp://ftp.example.com/file.txt">FTP Link</a>
                </body>
            </html>
        '''
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.text = html_content
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_get.return_value = mock_response

        links = self.crawler.get_links(html_content, self.root_url)
        expected_links = [
            'http://www.example.com/page1',
            'https://www.example.com/page2'
        ]
        self.assertEqual(links, expected_links)

    def test_handling_of_relative_and_absolute_urls(self):
        """
        Test that the crawler correctly resolves relative and absolute URLs.
        """
        html_content = '''
            <html>
                <body>
                    <a href="/relative/path">Relative Link</a>
                    <a href="subdir/page.html">Relative Link Without Leading Slash</a>
                    <a href="http://www.example.com/absolute/page">Absolute Link</a>
                </body>
            </html>
        '''
        base_url = 'http://www.example.com/dir/page.html'
        expected_links = [
            'http://www.example.com/relative/path',
            'http://www.example.com/dir/subdir/page.html',
            'http://www.example.com/absolute/page'
        ]
        links = self.crawler.get_links(html_content, base_url)
        self.assertEqual(links, expected_links)

    @patch('crawler.crawler.requests.Session.get')
    def test_duplicate_content_handling(self, mock_get):
        """
        Test that the crawler avoids processing pages with duplicate content.
        """
        html_content = '<html><body><p>Same Content</p></body></html>'
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.text = html_content
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.url = 'http://www.example.com'  # Set the URL attribute
        mock_get.return_value = mock_response

        self.crawler.crawl()
        # Since both URLs return the same content, only one should be processed
        self.assertEqual(len(self.crawler.results), 1)

    @patch('crawler.crawler.requests.Session.get')
    def test_redirect_handling(self, mock_get):
        """
        Test that the crawler correctly handles HTTP redirects.
        """

        def side_effect(url, timeout):
            if url == 'http://www.example.com':
                # Simulate a redirect to another URL
                mock_response = Mock()
                mock_response.headers = {'Content-Type': 'text/html'}
                mock_response.text = '<a href="http://www.example.com/page">Page</a>'
                mock_response.url = 'http://www.example.com/home'
                return mock_response
            else:
                mock_response = Mock()
                mock_response.headers = {'Content-Type': 'text/html'}
                mock_response.text = ''
                mock_response.url = url
                return mock_response

        mock_get.side_effect = side_effect

        self.crawler.crawl()  # The crawler makes a request to 'http://www.example.com' and redirected to 'http://www.example.com/home'
                              # which contains a link to 'http://www.example.com/page'

        crawled_urls = [result['url'] for result in self.crawler.results]
        expected_urls = ['http://www.example.com/home', 'http://www.example.com/page']
        self.assertEqual(crawled_urls, expected_urls)

    def test_fragment_identifier_handling(self):
        """
        Test that the crawler handles URLs with fragment identifiers appropriately.
        """
        html_content = '''
            <html>
                <body>
                    <a href="http://www.example.com/page#section1">Section 1</a>
                    <a href="http://www.example.com/page#section2">Section 2</a>
                    <a href="http://www.example.com/page">No Fragment</a>
                </body>
            </html>
        '''
        base_url = 'http://www.example.com'
        links = self.crawler.get_links(html_content, base_url)
        expected_links = [
            'http://www.example.com/page',
            'http://www.example.com/page',
            'http://www.example.com/page'
        ]
        self.assertEqual(links, expected_links)

    @patch('crawler.crawler.requests.Session.get')
    def test_non_html_content_handling(self, mock_get):
        """
        Test that the crawler skips non-HTML resources.
        """

        def side_effect(url, timeout):
            mock_response = Mock()
            if url == self.root_url:
                # Return the initial HTML content with links
                mock_response.headers = {'Content-Type': 'text/html'}
                mock_response.text = html_content
                mock_response.url = url
            elif url.endswith('.html'):
                mock_response.headers = {'Content-Type': 'text/html'}
                mock_response.text = ''
                mock_response.url = url
            else:
                mock_response.headers = {'Content-Type': 'application/pdf'}
                mock_response.text = ''
                mock_response.url = url
            return mock_response

        mock_get.side_effect = side_effect

        html_content = '''
            <html>
                <body>
                    <a href="document.pdf">PDF Document</a>
                    <a href="image.jpg">Image File</a>
                    <a href="video.mp4">Video File</a>
                    <a href="page.html">HTML Page</a>
                </body>
            </html>
        '''
        mock_response = Mock()
        mock_response.text = html_content
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_get.return_value = mock_response

        self.crawler.crawl()
        # Only the HTML page should be processed
        crawled_urls = [result['url'] for result in self.crawler.results]
        expected_urls = ['http://www.example.com', 'http://www.example.com/page.html']
        self.assertEqual(crawled_urls, expected_urls)

    @patch('crawler.crawler.requests.Session.get')
    def test_error_handling_and_timeouts(self, mock_get):
        """
        Test that the crawler handles exceptions and timeouts gracefully.
        """

        def side_effect(url, timeout):
            if url == 'http://www.example.com':
                raise requests.RequestException("Connection error")
            else:
                mock_response = Mock()
                mock_response.headers = {'Content-Type': 'text/html'}
                mock_response.text = ''
                return mock_response

        mock_get.side_effect = side_effect

        self.crawler.crawl()
        # The crawler should not crash and should handle the exception
        self.assertEqual(len(self.crawler.results), 0)

    def test_calculate_ratio(self):
        """
        Test that calculate_ratio computes the correct same-domain link ratio.
        """
        page_hostname = 'www.example.com'
        links = [
            'http://www.example.com/page1',
            'http://www.example.com/page2',
            'http://otherdomain.com/page',
            'http://anotherdomain.com/page'
        ]
        ratio = self.crawler.calculate_ratio(links, page_hostname)
        expected_ratio = 0.5
        self.assertEqual(ratio, expected_ratio)

    def test_fix_url(self):
        """
        Test that fix_url correctly handles URLs missing the scheme.
        """
        with patch('crawler.crawler.requests.head') as mock_head:
            # Simulate that http:// works
            mock_response = Mock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response

            url = 'www.example.com'
            fixed_url = self.crawler.fix_url(url)
            expected_url = 'http://www.example.com'
            self.assertEqual(fixed_url, expected_url)

    @patch('crawler.crawler.requests.Session.get')
    def test_invalid_url_handling(self, mock_get):
        """
        Test that the crawler handles invalid or malformed URLs gracefully.
        """
        html_content = '''
            <html>
                <body>
                    <a href="http://">Invalid URL 1</a>
                    <a href="://invalid-url">Invalid URL 2</a>
                    <a href="http:///example.com">Invalid URL 3</a>
                    <a href="http://www.example.com/valid">Valid URL</a>
                </body>
            </html>
        '''

        def side_effect(url, timeout):
            mock_response = Mock()
            if url == self.crawler.root_url:
                # Return the initial HTML content with links
                mock_response.headers = {'Content-Type': 'text/html'}
                mock_response.text = html_content
                mock_response.url = url
            elif url == 'http://www.example.com/valid':
                # Return a valid page
                mock_response.headers = {'Content-Type': 'text/html'}
                mock_response.text = '<html><body>Valid Page Content</body></html>'
                mock_response.url = url
            else:
                # Simulate an invalid URL by raising an exception
                raise requests.RequestException("Invalid URL")

            return mock_response

        mock_get.side_effect = side_effect

        self.crawler.crawl()
        # Only the valid URL should be processed
        crawled_urls = [result['url'] for result in self.crawler.results]
        expected_urls = ['http://www.example.com', 'http://www.example.com/valid']
        self.assertEqual(crawled_urls, expected_urls)

    def test_unit_fix_url(self):
        """
        Unit test for fix_url function with various inputs.
        """
        with patch('crawler.crawler.requests.head') as mock_head:
            # Case where http works
            mock_response_http = Mock()
            mock_response_http.status_code = 200
            # Case where https works
            mock_response_https = Mock()
            mock_response_https.status_code = 200
            # Case where neither works
            mock_response_fail = requests.RequestException()

            # Test with http working
            mock_head.side_effect = [mock_response_http, mock_response_fail]
            fixed_url = self.crawler.fix_url('example.com')
            self.assertEqual(fixed_url, 'http://example.com')

            # Test with https working
            mock_head.side_effect = [mock_response_fail, mock_response_https]
            fixed_url = self.crawler.fix_url('example.com')
            self.assertEqual(fixed_url, 'https://example.com')

    def test_unit_calculate_ratio(self):
        """
        Unit test for calculate_ratio function with predefined links.
        """
        links = [
            'http://www.example.com/page1',
            'http://www.example.com/page2',
            'http://otherdomain.com/page',
        ]
        page_hostname = 'www.example.com'
        ratio = self.crawler.calculate_ratio(links, page_hostname)
        self.assertEqual(ratio, 0.67)  # Rounded to two decimal places

    def test_unit_get_links(self):
        """
        Unit test for get_links function with different HTML content.
        """
        html_content = '''
            <html>
                <body>
                    <a href="/page1">Page 1</a>
                    <a href="http://www.example.com/page2">Page 2</a>
                    <a href="#section">Anchor Link</a>
                    <a href="javascript:void(0);">JavaScript Link</a>
                </body>
            </html>
        '''
        base_url = 'http://www.example.com'
        links = self.crawler.get_links(html_content, base_url)
        expected_links = [
            'http://www.example.com/page1',
            'http://www.example.com/page2',
            'http://www.example.com'  # Anchor link should resolve to base URL without fragment
        ]
        self.assertEqual(links, expected_links)


if __name__ == '__main__':
    unittest.main()
