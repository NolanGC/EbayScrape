from django.shortcuts import render
import requests
from bs4 import BeautifulSoup
# unit price, number units, total


def submit_advanced_search(keyword, seller_id):
    payload = {
        '_nkw': keyword,
        '_in_kw': 1,  # All Words, any order
        '_ex_kw': "",
        '_sacat': 0,  # All Categories
        'LH_Sold': 1,  # Sold listings only
        '_salic': 1,  # United States only
        '_fss': 1,  # Only show items from
        '_saslop': 1,  # Include following seller name
        '_sasl': seller_id,
        'LH_Complete': 1
    }
    with requests.Session() as s:
        url = 'https://www.ebay.com/sch/ebayadvsearch/i.html '
        r = s.get(url, params=payload)
        return r.text


def get_item_name(item):
    return item['title'].split(' access ')[1]


def is_valid_name(name, kwds):
    valid = False
    for kwd in kwds:
        if kwd in name:
            valid = True
    return valid


def calculate_sales(item_url):
    item_data_text = requests.get(item_url).text
    item_soup = BeautifulSoup(item_data_text, features='lxml')
    sales_url = item_soup.find('a', attrs={'class', 'vi-txt-underline'})

    amt = 0.0

    price = float(item_data_text.split(
        'US $')[1].split('</span>')[0])

    # multiple items
    if(sales_url):
        sales_data_text = requests.get(sales_url['href']).text
        sales_soup = BeautifulSoup(sales_data_text, features='lxml')

        # sales alternate background colors
        white_bg_sales = sales_soup.findAll('tr', attrs={'bgcolor': '#ffffff'})
        gray_bg_sales = sales_soup.findAll('tr', attrs={'bgcolor': '#f2f2f2'})
        sales = white_bg_sales + gray_bg_sales

        for sale in sales:
            if 'Accepted' in str(sale):
                amt += float(price)
            elif 'Declined' in str(sale):
                amt += 0.0
            else:
                # TODO test this
                try:
                    price = str(sale).split('US $')[1].split('</td>')[0]
                    quantity = str(sale).split(
                        'contentValueFont" valign="top">')[1].split('</td>')[0]
                    amt += float(price) * float(quantity)
                except:
                    amt += float(price)

        return round(amt, 2)
    else:
        return round(price, 2)


def audit(seller_name, search_kwd, kwd_variations):
    out = ''
    txt = submit_advanced_search(search_kwd, seller_name)
    soup = BeautifulSoup(txt, features='lxml')
    items = soup.findAll('a', attrs={'class': 'vip'})
    total = 0
    for item in items:
        name = get_item_name(item)
        if(is_valid_name(name, kwd_variations)):
            item_total = calculate_sales(item['href'])
            total += item_total
            out += str(name) + ' -> $' + str(item_total) + '\n'
    out += str(seller_name) + "'s earning from " + str(len(items)) + ' ' +\
        str(search_kwd) + " listing(s) totals $ " + str(total)
    return out


def index(request):
    return render(request, 'ebayscrape/index.html')


def results(request):
    seller_name = request.GET.get('seller_id')
    kwd = request.GET.get('kwd')
    kwd_vars = request.GET.get('kwd_vars').split(',')
    # OtterBox, Otter Box, otterbox, otter box, Otterbox, otterBox, Otter box, otter Box
    output = audit(seller_name, kwd, kwd_vars)
    return render(request, 'ebayscrape/results.html', {'output': output})
