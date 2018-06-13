import scrapy


class BeerSpider(scrapy.Spider):
    name = 'beer'
    start_urls = [
        'http://www.totalwine.com/beer/c/c0010?viewall=true',
    ]
    custom_settings = {
        'AUTOTHROTTLE_ENABLED': True,
    }
    allowed_domains = [
        'totalwine.com'
    ]

    def parse(self, response):
        for product in response.css('div.plp-product-desc-wrap'):
            yield {
                'name': product.css('a.analyticsProductName::text').extract_first(),
                'size': product.css('div.plp-product-qty::text').extract_first(),
                'price': product.css('span.price::text').extract_first(),
            }
