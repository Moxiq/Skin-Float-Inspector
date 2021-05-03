import requests
import urllib
import argparse

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

def get_listings(item_name, exterior):
    item_parsed = urllib.parse.quote(item_name + ' ' + exterior_converter(exterior))
    listings = []
    start = 0
    count = 100
    while True:
        try:
            url = fr'https://steamcommunity.com/market/listings/730/{item_parsed}/render/'
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

def get_inspect_id(item):
    listing_id = item['listingid']
    asset_id = item['asset']['id']
    d_id = item['asset']['market_actions'][0]['link'].split('D')[1]
    
    return asset_id, d_id, listing_id

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
    return None

def run(item_name, exterior):
    min_float = 1
    min_ind = 1
    listings = get_listings(item_name, exterior)
    print(f'Found {len(listings)} listings')
    for ind, item in enumerate(listings):
        a_id, d_id, l_id = get_inspect_id(item)
        float_val = get_float(a_id, d_id, l_id)

        if float_val < min_float:
            print("Found new low: " + str(float_val) + " at index: " + str(ind + 1))
            min_float = float_val
            min_ind = ind + 1

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--item_name', help='Item name of item to search, example: AK-47 | Frontside Misty', required=True, type=str)
parser.add_argument('--exterior', help='Exterior of item, allowed args: bs, ww, ft, mw, fn', required=True, type=str)
args = parser.parse_args()
run(args.item_name, args.exterior)