#!/usr/bin/env python3

import json
import operator
import os
import pprint
import ratebeer
import statistics
import string
import sys

class BeerProduct:

    def __init__(self, name, quantity, container_size_ounces, price, style, style_rating):
        self._name = name
        self._quantity = quantity
        self._container_size_ounces = container_size_ounces
        self._price = price
        self._style = style
        self._style_rating = style_rating

    @property
    def name(self):
        return self._name

    @property
    def quantity(self):
        return self._quantity

    @property
    def container_size_ounces(self):
        return self._container_size_ounces

    @property
    def price(self):
        return self._price

    @property
    def style(self):
        return self._style

    @property
    def style_rating(self):
        return self._style_rating

    @property
    def volume_per_price(self):
        volume_per_price = 0
        total_volume_ounces = self._get_total_volume_ounces()
        if total_volume_ounces > 0:
            volume_per_price = total_volume_ounces/self._price

        return volume_per_price

    def _get_total_volume_ounces(self):
        return self._quantity*self._container_size_ounces


class BeerProductFactory:

    def create_beer_product(self, beer_json_entry):
        name = self.get_field_value_with_default(beer_json_entry, 'name', 'Unknown')
        quantity_description = self.get_field_value_with_default(beer_json_entry, 'size', '0-0')
        quantity = self.parse_container_quantity(quantity_description)
        container_size_ounces = self.parse_container_size_ounces(quantity_description)
        price = float(self.get_field_value_with_default(beer_json_entry, 'price', '0.0'))
        style = self.get_field_value_with_default(beer_json_entry, 'style', 'Unknown')
        style_rating = self.get_field_value_with_default(beer_json_entry, 'style_rating', 0.0)

        return BeerProduct(name, quantity, container_size_ounces, price, style, style_rating)

    def parse_container_quantity(self, quantity_description):
        container_quantity = 0
        quantity_description_parts = quantity_description.split('-')
        if len(quantity_description_parts) > 1:
            container_quantity_text = ''
            for char in quantity_description_parts[0]:
                if char in string.digits:
                    container_quantity_text += char

            container_quantity = int(container_quantity_text)

        return container_quantity

    def parse_container_size_ounces(self, quantity_description):
        container_size_ounces = 0.0
        quantity_description_parts = quantity_description.split('-')
        if len(quantity_description_parts) > 1:
            container_size_text = ''
            for char in quantity_description_parts[1]:
                if char in string.digits or char == '.':
                    container_size_text += char

            container_size_ounces = float(container_size_text)

        return container_size_ounces

    def get_field_value_with_default(self, json_entry, field_name, default_value):
        field_value = json_entry.get(field_name, default_value)
        if field_value is None:
            field_value = default_value

        return field_value


def execute():
    command = sys.argv[1]
    command_parameters = []
    if len(sys.argv) > 2:
        command_parameters = sys.argv[2:]

    execute_command(command, command_parameters)


def execute_command(command, command_parameters):
    if command == 'best':
        print_best_values()
    elif command == 'style':
        print_best_style_values(command_parameters[0])
    elif command == 'update-pricing':
        update_beer_pricing()
    elif command == 'update-ratings':
        update_beer_ratings()


def print_best_values():
    pass


def print_best_style_values(style):
    beer_json = get_beer_json()
    beer_products = parse_beer_json(beer_json)
    beer_products_of_style = list(filter(lambda beer_product: beer_product.style == style, beer_products))

    (volume_per_price_mean, volume_per_price_stdev) = compute_attribute_stats(beer_products_of_style, lambda beer_product: beer_product.volume_per_price)
    (style_rating_mean, style_rating_stdev)  = compute_attribute_stats(beer_products_of_style, lambda beer_product: beer_product.style_rating)

    beer_product_scores = {}
    for beer_product in beer_products_of_style:
        volume_per_price_z_score = compute_z_score(beer_product.volume_per_price, volume_per_price_mean, volume_per_price_stdev)
        style_rating_z_score = compute_z_score(beer_product.style_rating, style_rating_mean, style_rating_stdev)
        total_score = volume_per_price_z_score + style_rating_z_score
        beer_product_score_key = '{}, {} x {:.1f}, ${}'.format(beer_product.name, beer_product.quantity, beer_product.container_size_ounces, beer_product.price)
        beer_product_scores[beer_product_score_key] = total_score

    pprint.pprint(sorted(beer_product_scores.items(), key=operator.itemgetter(1)))


def update_beer_pricing():
    pass


def update_beer_ratings():
    pass


def get_beer_json():
    beer_file_contents = []
    with open(os.path.join('..', 'output', 'rated_beer.json')) as beer_file:
        beer_file_contents = beer_file.read()

    return json.loads(beer_file_contents)


def parse_beer_json(beer_json):
    beer_products = []
    beer_product_factory = BeerProductFactory()
    for beer_json_entry in beer_json:
        beer_product = beer_product_factory.create_beer_product(beer_json_entry)
        beer_products.append(beer_product)

    return beer_products


def compute_attribute_stats(beer_products, attribute_getter):
    attribute_values = []
    for beer_product in beer_products:
        if attribute_getter(beer_product) is None:
            print(beer_product.name)
        attribute_values.append(attribute_getter(beer_product))

    mean = statistics.mean(attribute_values)
    stdev = statistics.stdev(attribute_values)
    return (mean, stdev)


def compute_z_score(value, mean, stdev):
    return ((value - mean)/stdev)


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


if __name__ == '__main__':
    execute()
