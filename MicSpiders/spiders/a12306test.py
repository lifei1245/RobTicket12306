# -*- coding: utf-8 -*-
import scrapy
import random
import json
import re

from PIL import Image
from tabulate import tabulate

from MicSpiders.spiders.city_info import station
import datetime
import time


class A12306testSpider(scrapy.Spider):
    name = '12306test'
    allowed_domains = ['kyfw.12306.cn']
    start_urls = ['https://kyfw.12306.cn/otn/login/init']
    header = {
        'HOST': 'kyfw.12306.cn',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\
         (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
    }
    login_url = 'https://kyfw.12306.cn/passport/web/login'
    captcha_url = 'https://kyfw.12306.cn/passport/captcha/captcha-image?\
        login_site=E&module=login&rand=sjrand&0.5351560963978581'
    check_url = 'https://kyfw.12306.cn/passport/captcha/captcha-check'
    position = {
        1: {'x': [0, 73], 'y': [0, 77]},
        2: {'x': [74, 73 * 2], 'y': [0, 77]},
        3: {'x': [73 * 2 + 1, 73 * 3], 'y': [0, 77]},
        4: {'x': [73 * 3 + 1, 73 * 4], 'y': [0, 77]},
        5: {'x': [0, 73], 'y': [78, 77 * 2]},
        6: {'x': [74, 73 * 2], 'y': [78, 77 * 2]},
        7: {'x': [73 * 2 + 1, 73 * 3], 'y': [78, 77 * 2]},
        8: {'x': [73 * 3 + 1, 73 * 4], 'y': [78, 77 * 2]},
    }
    query_url = 'https://kyfw.12306.cn/otn/leftTicket/query?\
        leftTicketDTO.train_date={start_date}&leftTicketDTO.from_station=\
        {start_station}&leftTicketDTO.to_station={end_station}&purpose_codes={isadult}'

    def start_requests(self):
        while True:
            try:
                start_date = input('乘车时间(格式2010-11-11):')
                start_station = input('乘车起点(城市名字):')
                end_station = input('乘车终点(城市名字):')
                isadult = input('儿童?(输入Y和N):')
                l = start_date.split('-')
                year = int(l[0])
                month = int(l[1])
                day = int(l[2])
                set_time = time.mktime(time.strptime(str(datetime.date(year=year, month=month, day=day)), '%Y-%m-%d'))
                current_time = time.mktime(time.strptime(str(datetime.date.today()), '%Y-%m-%d'))
                if current_time > set_time:
                    raise BaseException('时间必须在当天之后')
                query_url = query_url = 'https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date={start_date}&leftTicketDTO.from_station={start_station}&leftTicketDTO.to_station={end_station}&purpose_codes={isadult}'.format(
                    start_date=start_date,
                    start_station=station[start_station],
                    end_station=station[end_station],
                    isadult='STUDENT' if isadult == 'Y' or isadult == 'y' else 'ADULT')
                return [scrapy.Request(url=query_url, callback=self.parser_query_result, headers=self.header)]
            except:
                print('输入查询信息不正确')

    def parser_query_result(self, response):
        result = json.loads(response.text)
        if result['status'] == True and result['validateMessagesShowId'] == '_validatorMessage':
            car_list = result['data']['result']
            table = []
            for i in car_list:
                l = i.split('|')
                table.append(
                    [l[3], '%s->%s' % (l[8], l[9]), l[10], l[13], l[23], l[24], l[26], l[28], l[29], l[30], l[31],
                     l[32], l[33], '是' if l[11] == 'Y' else '否'])
            header = ['车次', '时间', '历时', '日期', '软卧', '软座', '无座', '硬卧', '硬座', '二等座', '一等座', '商务座', '动卧', '是否可预定']
            print(tabulate(table, header, tablefmt='orgtbl'))
            check_user = 'https://kyfw.12306.cn/otn/login/checkUser'
            return [scrapy.FormRequest(url=check_user, headers=self.header, callback=self.check_user)]

    def check_user(self, response):
        result = json.loads(response.text)
        if result['data']['flag'] == False:#status
            for url in self.start_urls:
                yield scrapy.Request(url=url, callback=self.parse, headers=self.header)
        else:
            # 下单
            print('已经是登录状态,下单方法')

    def parse(self, response):
        return [scrapy.Request(url=self.captcha_url, callback=self.parser_captcha, headers=self.header)]

    def gen_pass(self, num):
        result = []
        l = num.strip().split(',')
        for n in l:
            try:
                value_range = self.position[int(n)]
                x = random.randint(value_range['x'][0], value_range['x'][1])
                y = random.randint(value_range['y'][0], value_range['y'][1])
                result.append(x)
                result.append(y)
            except ValueError as e:
                print('请输入正确的格式')
                return None
        return ','.join(map(str, result))

    def parser_captcha(self, response):
        with open('capthca.png', 'wb') as f:
            f.write(response.body)
        im = Image.open('capthca.png')
        im.show()
        number = input('验证码位置,第一排1-4,第二排5-8,多个以英文逗号隔开如1,2,3:')
        data = {
            'answer': self.gen_pass(number),
            'login_site': 'E',
            'rand': 'sjrand'
        }
        return [scrapy.FormRequest(url=self.check_url, formdata=data, headers=self.header, callback=self.check_result)]

    def check_result(self, response):
        msg = re.match(r'.*<result_message>(.*)</result_message>', response.text).group(1)
        if msg == '验证码校验成功':
            login_data = {
                'username': 'xxx',#帐号
                'password': 'XXX',#密码
                'appid': 'otn'
            }
            return [scrapy.FormRequest(url=self.login_url, formdata=login_data, callback=self.login_result,
                                       headers=self.header)]
        else:
            return [scrapy.Request(url=self.start_urls[0], callback=self.parse, headers=self.header)]

    def login_result(self, response):
        # 下单
        print(response.text)
