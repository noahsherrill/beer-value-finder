#!/usr/bin/env python3

import json
import operator
import os
import pprint
import ratebeer
import statistics
import string

def get_volume_in_ounces(beer_size_description):
    volume_in_ounces = 0
    size_description_parts = beer_size_description.split('-')
    if len(size_description_parts) > 1:
        quantity_text = ''
        for char in size_description_parts[0]:
            if char in string.digits or char == '.':
                quantity_text += char

        container_size_text = ''
        for char in size_description_parts[1]:
            if char in string.digits or char == '.':
                container_size_text += char

        quantity = int(quantity_text)
        container_size = float(container_size_text)
        volume_in_ounces = quantity*container_size

    return volume_in_ounces


def process_beer(beer_item, beer, beer_scores):
    try:
        volume_in_ounces = get_volume_in_ounces(beer_item['size'])
        price = float(beer_item['price'].strip())
        if price > 0 and beer.style_rating is not None:
            volume_style = volume_in_ounces*beer.style_rating
            volume_style_per_price = volume_style/price
            print('%s, %s: %f' % (beer.name, beer_item['size'], volume_style_per_price))
            beer_scores['%s, %s' % (beer.name, beer_item['size'])] = volume_style_per_price

        for (beer_attribute_name, beer_attribute_value) in beer.__dict__.items():
            if not beer_attribute_name == 'brewery' and not beer_attribute_name == 'brewed_at':
                beer_item[beer_attribute_name] = beer_attribute_value

    except ratebeer.rb_exceptions.AliasedBeer:
        pass


def get_ratings(beer_file_contents):
    try:
        beer_scores = {}
        rate_beer = ratebeer.RateBeer()
        beer_json = json.loads(beer_file_contents)
        for beer_item in beer_json:
            if 'id' in beer_item:
                continue

            results = rate_beer.search(beer_item['name'])

            for beer in results['beers']:
                if beer.name == beer_item['name']:
                    process_beer(beer_item, beer, beer_scores)

    finally:
        with open(os.path.join('..', 'output', 'rated_beer.json'), 'w') as rated_beer_file:
            json.dump(beer_json, rated_beer_file)

        #with open(os.path.join('..', 'output', 'computed_ratings.txt'), 'w') as computed_ratings_file:
        #    computed_ratings_file.write(pprint.pformat(beer_scores))


def get_volume_per_price(beer_item):
    volume_per_price = 0
    volume_in_ounces = get_volume_in_ounces(beer_item['size'])
    if volume_in_ounces > 0:
        price = float(beer_item['price'])
        volume_per_price = volume_in_ounces/price

    return volume_per_price


def get_style_values(beer_file_contents, style):
    beer_scores = {}
    beer_json = json.loads(beer_file_contents)
    beers_of_style = []
    style_scores = []
    volumes_per_price = []
    for beer_item in beer_json:
        if 'style' in beer_item and beer_item['style_rating'] is not None:
            if beer_item['style'] == style:
                volume_per_price = get_volume_per_price(beer_item)
                if volume_per_price > 0:
                    style_scores.append(beer_item['style_rating'])
                    volumes_per_price.append(volume_per_price)
                    beers_of_style.append(beer_item)

    style_score_mean = statistics.mean(style_scores)
    style_score_stdev = statistics.stdev(style_scores)
    volume_per_price_mean = statistics.mean(volumes_per_price)
    volume_per_price_stdev = statistics.stdev(volumes_per_price)

    imperial_stout_scores = {}
    for beer_item in beers_of_style:
        volume_per_price = get_volume_per_price(beer_item)
        style_score = beer_item['style_rating']
        volume_per_price_z_score = ((volume_per_price - volume_per_price_mean)/volume_per_price_stdev)
        style_score_z_score = ((style_score - style_score_mean)/style_score_stdev)
        score = volume_per_price_z_score + style_score_z_score
        imperial_stout_scores = {}
        beer_scores['%s, %s' % (beer_item['name'], beer_item['size'])] = score

    pprint.pprint(sorted(beer_scores.items(), key=operator.itemgetter(1)))

if __name__ == '__main__':
    with open(os.path.join('..', 'output', 'rated_beer.json')) as beer_file:
        beer_file_contents = beer_file.read()

    #get_ratings(beer_file_contents)
    get_style_values(beer_file_contents, 'Imperial IPA')
