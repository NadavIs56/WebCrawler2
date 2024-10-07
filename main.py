# main.py

from crawler import WebCrawler
import argparse
import sys

def parse_arguments():
    """
    Parse command-line arguments for the web crawler.
    :return: A tuple containing the root URL (str) and depth limit (int).
    """
    parser = argparse.ArgumentParser(description='Web Crawler')
    parser.add_argument('root_url', help='The root URL to start crawling from')
    parser.add_argument('depth_limit', type=int, help='Recursion depth limit (positive integer)')
    args = parser.parse_args()
    if args.depth_limit < 1:
        parser.error("Depth limit must be a positive integer.")
    return args.root_url, args.depth_limit

def main():
    """
    Main function to execute the web crawler.
    :return:
    """
    if len(sys.argv) != 3:
        print("Usage: python main.py <root_url> <max_depth>")
        sys.exit(1)
    root_url, depth_limit = parse_arguments()
    crawler = WebCrawler(root_url, depth_limit)
    if crawler.root_url is None:
        print(f"Invalid root URL: {root_url}")
        sys.exit(1)
    crawler.crawl()

if __name__ == '__main__':
    main()
