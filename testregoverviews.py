#!/usr/bin/env python

#-----------------------------------------------------------------------
# testregoverviews.py
# Author: Ranajoy Gupta
#-----------------------------------------------------------------------

import sys
import time
import argparse
import playwright.sync_api

MAX_LINE_LENGTH = 72
UNDERLINE = '-' * MAX_LINE_LENGTH

def get_args():

    parser = argparse.ArgumentParser(
        description='Test the ability of the reg application to '
            + 'handle "primary" (class overviews) queries')

    parser.add_argument(
        'serverURL', metavar='serverURL', type=str,
        help='the URL of the reg application')

    parser.add_argument(
        'browser', metavar='browser', type=str,
        choices=['firefox', 'chrome'],
        help='the browser (firefox or chrome) that you want to use')

    args = parser.parse_args()

    return (args.serverURL, args.browser)

def print_flush(message):

    print(message)
    sys.stdout.flush()

def run_test(server_url, browser_process, input_values):

    print_flush(UNDERLINE)
    print_flush('dept: |' + input_values.get('dept', '') + '|')
    print_flush('coursenum: |' + input_values.get('coursenum', '') +'|')
    print_flush('area: |' + input_values.get('area', '') + '|')
    print_flush('title: |' + input_values.get('title', '') + '|')
    print_flush(UNDERLINE)

    try:
        page = browser_process.new_page()
        page.goto(server_url)

        dept_input = page.locator('#dept')
        coursenum_input = page.locator('#coursenum')
        area_input = page.locator('#area')
        title_input = page.locator('#title')

        dept_input.fill(input_values.get('dept', ''))
        coursenum_input.fill(input_values.get('coursenum', ''))
        area_input.fill(input_values.get('area', ''))
        title_input.fill(input_values.get('title', ''))

        button = page.locator('#submitButton')
        overviews_table = page.locator('#overviewsTable')
        old_rand = overviews_table.get_attribute('rand')
        button.click()
        new_rand = overviews_table.get_attribute('rand')
        
        while new_rand == old_rand:
            time.sleep(0.1)
            new_rand = overviews_table.get_attribute('rand')

        overviews_table = page.locator('#overviewsTable')
        print_flush(overviews_table.inner_text())

    except Exception as ex:
        print(str(ex), file=sys.stderr)

def main():

    server_url, browser = get_args()

    with playwright.sync_api.sync_playwright() as pw:

        if browser == 'chrome':
            browser_process = pw.chromium.launch()
        else:
            browser_process = pw.firefox.launch()

        run_test(server_url, browser_process,
            {'dept':'COS'})

        run_test(server_url, browser_process,
            {'dept':'COS', 'coursenum':'2', 'area':'qr',
            'title':'intro'})
            
        run_test(server_url, browser_process, 
            {'dept':'cOs', 'area':'qR', 'title':'InTrO'})
            
        run_test(server_url, browser_process, 
            {'title':' programming '})
            
        run_test(server_url, browser_process, 
            {'coursenum':'3'})
            
        run_test(server_url, browser_process, 
            {'dept':'NOTADEPARTMENT'})
            
        run_test(server_url, browser_process, 
            {'coursenum':'999'})
            
        run_test(server_url, browser_process, 
            {'title':'%'})
            
        run_test(server_url, browser_process, 
            {'title':'_'})
            
        run_test(server_url, browser_process, 
            {'title':'\\'})
            
        run_test(server_url, browser_process, 
            {'title':"'"})
            
        run_test(server_url, browser_process, 
            {'title':'"'})

if __name__ == '__main__':
    main()
