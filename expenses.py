# -*- coding: utf-8 -*-

import os
import csv
import time
import json
import argparse
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.support.ui import Select

chromedriver_path = os.path.join(os.getcwd(), 'chromedriver')


def gather_results_list(d, y, s, t, p):
    """
    Get the list of expense transactions for a given time period
    """

    # open the search page on the assembly expenses website
    d.get('http://allowances.assembly.wales/default.aspx?Option=1&clang=1')

    # select the dropdown to enter date information
    button = d.find_element_by_name('ctl00$cphMainContentsArea$btnFinancialYear')
    button.click()

    # add the year
    year_select = Select(d.find_element_by_name('ctl00$cphMainContentsArea$ddlFinancialYear'))
    year_select.select_by_value(y)

    # add the start month
    from_select = Select(d.find_element_by_name('ctl00$cphMainContentsArea$ddlFromMonth'))
    from_select.select_by_value(s)

    # add the end month
    to_select = Select(d.find_element_by_name('ctl00$cphMainContentsArea$ddlToMonth'))
    to_select.select_by_value(t)

    # submit the search
    submit_button = d.find_element_by_name('ctl00$cphMainContentsArea$btnFind')
    submit_button.click()

    # adjust the results to 100 per page
    results_per_page = Select(d.find_element_by_name('ctl00$cphMainContentsArea$ddlPaging'))
    results_per_page.select_by_value('100')

    # find out how many pages we have to extract data from
    number_of_pages = d.find_element_by_id('ctl00_cphMainContentsArea_lblSearchResultsPageHeader').text
    number_start = number_of_pages.find(' of ') + 3
    number_end = number_of_pages.find(' from ')
    number_of_pages = int(number_of_pages[number_start:number_end])
    print("Number of results pages to process: %d" % number_of_pages)
    print("Processing...")

    # go through this page and extract the links to transaction details
    results_pages = []
    results_on_page = d.find_elements_by_link_text('View Details')
    for r in results_on_page:
        results_pages.append(r.get_attribute('href'))

    # go through the remaining search results pages and do the same
    for i in tqdm(range(1, number_of_pages)):
        page_number = i + 1
        if page_number % 10 == 1:
            next_page_text = "»"
        else:
            next_page_text = str(page_number)

        next_page_link = d.find_element_by_link_text(next_page_text)
        next_page_link.click()

        results_on_page = d.find_elements_by_link_text('View Details')
        for r in results_on_page:
            results_pages.append(r.get_attribute('href'))

        # sleep so we're not hurting the server
        time.sleep(p)

    print("Done processing results.")
    # return a list of transaction details
    return results_pages


def extract_details(d, r, p):
    """
    Extract the details for a particular expenses transaction
    """
    # get the page
    d.get(r)

    # extract the info and store in a dict
    eo = {}
    eo['member_name'] = d.find_element_by_id('ctl00_cphMainContentsArea_lblSRTMemberName').text
    eo['financial_year'] = d.find_element_by_id('ctl00_cphMainContentsArea_lblSRTFinancialYear').text
    eo['claim_month'] = d.find_element_by_id('ctl00_cphMainContentsArea_lblSRTClaimMonth').text
    eo['allowance_type'] = d.find_element_by_id('ctl00_cphMainContentsArea_lblSRTAllowanceType').text
    eo['expenditure_type'] = d.find_element_by_id('ctl00_cphMainContentsArea_lblSRTExpenditureType').text
    eo['payee'] = d.find_element_by_id('ctl00_cphMainContentsArea_lblSRTPayee').text
    eo['amount'] = d.find_element_by_id('ctl00_cphMainContentsArea_lblSRTAmount').text.replace('£', '') #remove the unicode £ symbol but preserve any sign
    eo['fees_reference'] = d.find_element_by_id('ctl00_cphMainContentsArea_lblSRTFeesRef').text
    eo['date'] = d.find_element_by_id('ctl00_cphMainContentsArea_lblSRTTransactionDate').text
    eo['invoice_reference'] = d.find_element_by_id('ctl00_cphMainContentsArea_lblSRTInvoiceRef').text
    eo['additional_information'] = d.find_element_by_id('ctl00_cphMainContentsArea_lblSRTComment').text

    # sleep so we're not hurting the server
    time.sleep(p)
    return eo


def write_csv(y, eo):
    with open('naw_expenses_%s.csv' % y, 'w') as output_file:
        writer = csv.DictWriter(output_file, eo[0].keys())
        writer.writeheader()
        writer.writerows(eo)


def write_json(y, eo):
    with open('naw_expenses_%s.json' % y, 'w') as output_file:
        json.dump(eo, output_file)


if __name__ == "__main__":

    # deal with command line arguments
    parser = argparse.ArgumentParser(description='Scraping Welsh Assembly expenses.')
    parser.add_argument('-y', '--years', nargs='*', help='list of years to check', required=True)
    parser.add_argument('-s', '--start', help='month to start scraping from', required=False, default='04')
    parser.add_argument('-t', '--to', help='month to scrape to', required=False, default='03')
    parser.add_argument('-p', '--pause', help='pause to add between requests to server (seconds) - default 1/3 of a second', required=False, default=0.33, type=float)
    parser.add_argument('-d', '--driver', help='path to chromedriver', required=False, default=chromedriver_path)
    args = parser.parse_args()

    # open a webdriver
    years_to_check = args.years
    driver = webdriver.Chrome(chromedriver_path)
    driver.implicitly_wait(5)
    driver.maximize_window()

    # for every year we need to check
    for year in years_to_check:
        # gather the list of transaction details
        results = gather_results_list(driver, year, args.start, args.to, args.pause)
        expense_objects = []

        # extract all the transaction details
        print('Number of transactions to extract: %d' % len(results))
        print('Extracting...')
        for result in tqdm(results):
            expense_objects.append(extract_details(driver, result, args.pause))
        print('Done extracting.')

        # and store all the details
        print('Writing data...')
        write_csv(year, expense_objects)
        write_json(year, expense_objects)
        print('Done writing data.')

    driver.quit()
