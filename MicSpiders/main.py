# coding=utf-8
# @Time : 2017/11/15 11:26
# @Author : 李飞

import os

from scrapy.cmdline import execute

s = 'scrapy crawl 12306test'
execute(s.split())
