#!/usr/bin/env python

#-----------------------------------------------------------------------
# testregdetails.py
# Author: Ranajoy Gupta
#-----------------------------------------------------------------------

"""Tests the Registrar application's handling of details requests."""

import sys
import argparse
import playwright.sync_api

MAX_LINE_LENGTH = 72
UNDERLINE = '-' * MAX_LINE_LENGTH

def parse_args():
    """Parses command-line arguments for testing script."""
    parser = argparse.ArgumentParser(
        description='Test the ability of the reg application to '
            + 'handle "secondary" (class details) queries'
    )
    parser.add_argument('serverURL', metavar='serverURL', type=str,
                        help='the URL of the reg application')
    parser.add_argument('browser', metavar='browser', type=str,
                        choices=['firefox', 'chrome'],
                        help='the browser (firefox or chrome) '
                             'that you want to use')

    args = parser.parse_args()
    return args.serverURL, args.browser

def print_flush(message):
    """Prints a message and flushes stdout."""
    print(message)
    sys.stdout.flush()

def run_test(server_url, browser_process, classid):
    """Tests normal class details retrieval via UI navigation."""
    print_flush(UNDERLINE)
    print_flush(classid)
    print_flush(UNDERLINE)

    try:
        page = browser_process.new_page()
        page.goto(server_url)

        link = page.get_by_text(classid).first
        link.click()

        class_details = page.locator('#classDetails')
        print_flush(class_details.inner_text())

    except Exception as ex:
        print(str(ex), file=sys.stderr)

def run_error_test(server_url, browser_process, route, test_name):
    """Tests error handling by directly fetching URLs."""
    print_flush(UNDERLINE)
    print_flush(test_name)
    print_flush(UNDERLINE)

    try:
        page = browser_process.new_page()
        page.goto(server_url + route)

        body = page.locator('body')
        print_flush(body.inner_text())

    except Exception as ex:
        print(str(ex), file=sys.stderr)

def main():
    """Runs automated tests against details client."""
    server_url, browser = parse_args()

    with playwright.sync_api.sync_playwright() as pw:
        if browser == 'chrome':
            browser_process = pw.chromium.launch()
        else:
            browser_process = pw.firefox.launch()

        run_test(server_url, browser_process, '8321')
        run_test(server_url, browser_process, '9032')

        run_error_test(server_url, browser_process,
                       '/regdetails?classid=99999',
                       'Non-existing classid')
        run_error_test(server_url, browser_process,
                       '/regdetails?classid=abcd',
                       'Non-integer classid')
        run_error_test(server_url, browser_process,
                       '/regdetails?classid=',
                       'Missing classid value')
        run_error_test(server_url, browser_process,
                       '/regdetails',
                       'Missing classid parameter')

if __name__ == '__main__':
    main()
