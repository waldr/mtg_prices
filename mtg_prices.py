from __future__ import division
from bs4 import BeautifulSoup
import urllib
import re
import numpy as np
import sys
import argparse
import pickle


def parse_arguments():
    parser = argparse.ArgumentParser(description='MTG price estimator (BRL)') 
    parser.add_argument('-card', '--card', type=str, help='card name')
    parser.add_argument('-cardlist', '--cardlist', type=str, 
                        help='file listing cards')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='whether to track progress')
    args = parser.parse_args()

    if args.card is None and args.cardlist is None:
        parser.print_help()

    return args


def get_prices(card_name):
    query_url = 'http://www.ligamagic.com.br/?view=cards/card&card='
    query_url = query_url + card_name
    
    r = urllib.urlopen(query_url)
    soup = BeautifulSoup(r, 'lxml')
    
    # Shop prices (check page structure)
    shops_div = soup.find_all('table', id='cotacao-1')

    if len(shops_div) < 1:
        return []
    else:
        shops_div = shops_div[0]

    price_list = [el.get_text() for el in shops_div.find_all(class_='lj b')]
    
    # Do not consider prices over 1k, e.g.: R$ 1.234,56
    money = re.compile('(R\$ \d*,\d*)')
    
    prices = [money.findall(p) for p in price_list]
    prices = [p[0] for p in prices if len(p) > 0]
    prices = [float(str(p)[3:].replace(',', '.')) for p in prices]

    return prices


def get_lowest_prices(prices, num=3):
    prices.sort()
    return prices[:num]


def print_price_summary(card_name, prices):
    print card_name
    print '\tLowest %d:' % (len(prices))
    for p in prices:
        print '\t%.2f' % (p)
    print '\tAverage:\n\t%.2f' % (np.average(prices))


def no_prices_found_error(card_name):
    print '%s\n\tNo prices were found' % (card_name)


def parse_card_list(fname):
    card_list = []
    with open(fname) as f:
        card_list = f.readlines()
        card_list = [c.strip('\n') for c in card_list] # strip \n
    return card_list    


def get_prices_from_card_list(fname, num_avg, verbose=False):
    """
    Process card list contained in file @fname.
    Return an augmented list containing the card name and 2 values:
    the lowest store price for that card, and the average of the @num_avg
    lowest prices. 
    If no card prices are found, the element is set to
    [card_name, -1, -1]
    """
    card_list = parse_card_list(fname)
    augmented_list = []
    for i, card_name in enumerate(card_list):
        if verbose:
            print '%d/%d' % (i + 1, len(card_list))
        card_info = []
        if card_name == '' or card_name.startswith('#'):
            continue
        prices = get_prices(card_name)
        if len(prices) == 0:
            card_info = [card_name, -1, -1]
        else:
            lowest_prices = get_lowest_prices(prices, num_avg)
            card_info = [card_name, 
                         lowest_prices[0], 
                         np.average(lowest_prices)]
        augmented_list.append(card_info)

    return augmented_list


if __name__ == '__main__': 
    num_avg = 3 # number of (lowest) prices to consider
    args = parse_arguments()

    
    if args.card is not None:
        # Single card
        card_name = args.card
        prices = get_prices(card_name)
        if len(prices) > 0:
            lowest_prices = get_lowest_prices(prices, num_avg)
            print_price_summary(card_name, lowest_prices)
        else:
            no_prices_found_error(card_name)
    elif args.cardlist is not None:
        # Card list passed as file
        prices_list = get_prices_from_card_list(args.cardlist, 
                                                num_avg, 
                                                args.verbose)
        txt_summary_file = args.cardlist + '.prices.csv'
        pickled_prices_file = args.cardlist + '.prices.pickle'
        with open(txt_summary_file, 'w') as f:
            lines = [e[0] + ',' +
                     '%.2f,' % (e[1]) +
                     '%.2f,\n' % (e[2]) 
                     for e in prices_list]
            f.writelines(lines)
        with open(pickled_prices_file, 'w') as f:
            pickle.dump(prices_list, f)

