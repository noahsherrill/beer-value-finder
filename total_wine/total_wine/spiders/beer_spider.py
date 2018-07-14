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
                'price': product.css('span.price::text').extract_first().strip(),
            }

        next_page_link = response.css('a.pager-next')
        if next_page_link is not None:
            self.page_number = str(int(self.page_number) + 1)
            next_page = 'http://www.totalwine.com/beer/c/c0010?viewall=true&page=%s' % self.page_number
            yield scrapy.Request(next_page, callback=self.parse)
