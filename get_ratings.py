#!/usr/bin/env python3

import ratebeer

rate_beer = ratebeer.RateBeer()
results = rate_beer.search('Great Divide Yeti')
for beer in results['beers']:
    print('%s: %d' % (beer.name, beer.style_rating))
