import datetime
import json
import re

import requests
import scrapy
from car_integration.items import CarIntegrationItem
from car_integration.mapping import mapping
from scrapy.http import HtmlResponse
from scrapy.utils.project import get_project_settings


class AnycarSpider(scrapy.Spider):
    name = 'anycar'
    allowed_domains = ['anycar.vn']
    base_url = 'https://anycar.vn'
    start_urls = [
        base_url + '/ban-xe-oto',
    ]
    settings = get_project_settings()

    def parse(self, response, *args, **kwargs):
        list_product = response.xpath('//div[contains(@class,"car-image")]/a/@href').getall()

        for product in list_product:
            print("Product: ", product)
            yield scrapy.Request(url=response.urljoin(product), callback=self.parse_product)

        index_next_page = 2
        while True:
            html = requests.get('https://anycar.vn/ajax/xem-them-xe?page=' + str(index_next_page)).content.decode('utf8')
            html = json.loads(html)['content']
            response_next_page = HtmlResponse(url='next page', body=html, encoding='utf-8')

            if response_next_page.xpath('//*[@id="total_post"]/@value').get() == '0':
                break
            index_next_page += 1

            list_product = response_next_page.xpath('//div[contains(@class,"car-image")]/a/@href').getall()
            for product in list_product:
                yield scrapy.Request(url=response_next_page.urljoin(product), callback=self.parse_product)

    def parse_product(self, response):
        data = CarIntegrationItem(
            source=response.request.url,
            name=response.xpath('//h1/text()').get(),
            base_url=self.base_url,
            price=response.xpath('//*[@id="gia_ban"]/text()').get(),
            time_update=datetime.datetime.utcnow(),
            image=[],
            overall_dimension=None,
            cylinder_capacity=None,
            engine='',
            max_wattage=None,
            fuel_consumption='',
            origin='',
            transmission='',
            seat=None,
            manufacturer='',
            type='Mới',
            color='',
            interior_color='',
            mfg=None,
            drive='',
            fuel_tank_capacity=None,
            info_contact={
                'name': response.xpath('//*[@id="car-detail"]/div/div/div[2]/div[1]/div[3]/div/b/text()').get()
            }
        )
        if data.get('price') is None:
            data['price'] = response.xpath('//span[contains(@class,"h1")]/text()').get()
            data['price'] = int(data['price'][0] + '000000')
        details = response.xpath('//div[@class="row"]/div/div/div[@class="line"]')
        for detail in details:
            key = detail.xpath('div[@class="line-label"]/text()').get().strip()
            field = mapping(key)
            if field:
                data[field] = detail.xpath('div[@class="line-value"]/text()').get()

        data['image'] = response.xpath('//*[@id="car-photos"]/div/div/div/center/img/@data-src').getall()
        regex_string = data['name'].split('  ')
        if len(regex_string) < 2:
            reg = re.findall(r'(\w+) (.*) (.*) (\d+)', data['name'])[0]
            data['manufacturer'] = reg[0]
            data['engine'] = reg[2]
        else:
            reg_manufacturer_type = re.findall(r'(\w+) (.*)', regex_string[0])[0]
            reg_engine = re.findall(r'(.*) (\d+)', regex_string[1])[0]
            data['manufacturer'] = reg_manufacturer_type[0]
            data['engine'] = reg_engine[0]

        # try:
        #     if data['manufacturer'].lower() not in self.list_manufacturer['manufacturer'].keys():
        #         print(data['source'], data['manufacturer'])
        #         return
        #     else:
        #         data['manufacturer'] = data['manufacturer'].lower()
        #         data['name'] = data['name'].upper()
        # except Exception as e:
        #     print(e)
        #     return

        yield data
