import requests
import urllib
from time import sleep
import argparse
from notify_run import Notify

def get_float(asset_id, d_id, listing_id):
    url = 'https://api.csgofloat.com'
    res = requests.get(
        url,
        params={
            'a': asset_id,
            'd': d_id,
            'm': listing_id
        }
    )
    return res.json()['iteminfo']['floatvalue']

def get_listings(item_name, exterior, stattrak):
    full_name = ''
    if stattrak:
        full_name += 'StatTrak™ '
    full_name += item_name + ' ' + exterior_converter(exterior)
    item_parsed = urllib.parse.quote(full_name)
    url = fr'https://steamcommunity.com/market/listings/730/{item_parsed}/render/'
    print("Listings: " + url.split('render')[0])
    listings = []
    start = 0
    count = 100

    limit = 500 / count
    counter = 0
    # Cannot make too many request as code 429 is thrown, limited to 500 items for now
    while counter < limit:
        counter += 1
        try:
            res = requests.get(
                url, 
                params={
                    'start': start,
                    'count': count,
                    'country': 'EUR',
                    'language': 'english',
                    'currency': 3
                })

            res.raise_for_status()
        except Exception as err:
            print(f'Request failed with error code {err}')

        to_dict = res.json()
        if not to_dict:
            raise SystemExit("Request data failed (null)")

        ids = to_dict['listinginfo']
        if not ids:
            break
        for k, v in ids.items():
            listings.append(v)

        start += count

    return listings

def index_to_page_count(index):
    return index // 10 + 1, index % 10 + 1

def get_inspect_id(item):
    listing_id = item['listingid']
    asset_id = item['asset']['id']
    d_id = item['asset']['market_actions'][0]['link'].split('D')[1]
    
    return asset_id, d_id, listing_id

def get_price(item):
    try: 
        return (int(item['converted_price']) + int(item['converted_fee'])) / 100
    except KeyError:
        return 0

def exterior_converter(exterior):
    if exterior == 'bs':
        return '(Battle-Scarred)'
    elif exterior == 'ww':
        return '(Well-Worn)'
    elif exterior == 'ft':
        return '(Field-Tested)'
    elif exterior == 'mw':
        return '(Minimal Wear)'
    elif exterior == 'fn':
        return '(Factory New)'
    raise SystemExit("Valid exterior formats are: bs, ww, ft, ww, fn")

def run(item_name, exterior, stattrak):
    min_float = 1
    listings = get_listings(item_name, exterior, stattrak)
    print(f'Found {len(listings)} listings')
    for ind, item in enumerate(listings):
        # print(item)
        a_id, d_id, l_id = get_inspect_id(item)
        float_val = get_float(a_id, d_id, l_id)
        price = get_price(item)

        # page_count, item_count = index_to_page_count(ind)
        # print(f"Found min float {float_val} at page: {page_count}, index {item_count}")
        if float_val < min_float:
            page_count, item_count = index_to_page_count(ind)
            print(f"Found min float {float_val} at page: {page_count} index {item_count}, price: {price}€")
            min_float = float_val

def run_notify(item_name, exterior, stattrak, max_price, max_float):
    notify = Notify()
    print(notify.info())

    listings = get_listings(item_name, exterior, stattrak)

    while True:
        findings = []
        for ind, item in enumerate(listings):
            a_id, d_id, l_id = get_inspect_id(item)
            float_val = get_float(a_id, d_id, l_id)
            price = get_price(item)

            if float_val <= max_float and price <= max_price:
                findings.append((price, float_val))
                page_count, item_count = index_to_page_count(ind)
            
        if findings:
            for price, float_val in findings:
                print(f"Found item, float: {float_val}, price: {price}€")

            notify.send("Found new items!")
            print("----------------------------------------------------------------------")
        sleep(30)
            

    

    

parser = argparse.ArgumentParser(description='CSGO skin float checker!')
parser.add_argument('--item_name', help='Item name of item to search, example: AK-47 | Frontside Misty', required=True, type=str)
parser.add_argument('--exterior', help='Exterior of item, allowed args: bs, ww, ft, mw, fn', required=True, type=str)
parser.add_argument('--stattrak', help='Whether item is StatTrak or not, omit arg for false', default=False, action='store_true')
parser.add_argument('--notify', help='Shares QR code where user can be notified of good items', default=False, action='store_true')
parser.add_argument('--price_max', help='Sends notification below given price (given that float is below --float_max aswell)', type=float)
parser.add_argument('--float_max', help='Sends notification below given float (given that price is below --price_max aswell)', type=float)
args = parser.parse_args()

if args.notify and not (args.price_max and args.float_max):
    print("--price_max and --float_max are required when passing --notify flag")
    raise SystemExit

if args.notify:
    run_notify(args.item_name, args.exterior, args.stattrak, args.price_max, args.float_max)
else:
    run(args.item_name, args.exterior, args.stattrak)