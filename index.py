import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
import pandas
import sqlite3

commentURL = 'http://comment5.news.sina.com.cn/page/info?version=1&format=js&channel\
=gn&newsid=comos-{}&group=&compress=0&ie=utf-8&oe=utf-8&page=1&page_size=20'

# 获取新闻评论数量
def getCommentCounts(newsurl):
    m = re.search('doc-i(.+).shtml', newsurl)
    newsid = m.group(1)
    comments = requests.get(commentURL.format(newsid))
    jd = json.loads(comments.text.strip('var data='))
    return jd['result']['count']['total']


# 获取新闻详情数据
def getNewsDetail(newsurl):
    result = {}
    res = requests.get(newsurl)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    result['title'] = soup.select('#artibodyTitle')[0].text
    result['newssource'] = soup.select('.time-source span a')[0].text
    timesource = soup.select('.time-source')[0].contents[0].strip()
    result['dt'] = datetime.strptime(timesource, '%Y年%m月%d日%H:%M')
    result['article'] = ' '.join([p.text.strip() for p in soup.select('#artibody p')[:-1]])
    result['editor'] = soup.select('.article-editor')[0].text.strip('责任编辑：')
    result['comments'] = getCommentCounts(newsurl)
    return result

# 获取单条新闻数据
def parseListLinks(url):
    newsdetails = []
    res = requests.get(url)
    jd = json.loads(res.text.lstrip('  newsloadercallback(').rstrip(');'))
    for ent in jd['result']['data']:
        newsdetails.append(getNewsDetail (ent['url']))
    return newsdetails

url = 'http://api.roll.news.sina.com.cn/zt_list?channel=news&cat_1=gnxw&\
cat_2==gdxw1||=gatxw||=zs-pl||=mtjj&level==1||=2&show_ext=1&show_all=1&show_num=22&\
tag=1&format=json&page={}&callback=newsloadercallback&_=1509593568102'
news_total = []
for i in range(1, 3): # 拼接第一页到第二页新闻请求
    newsurl = url.format(i)
    newsarray =parseListLinks(newsurl)
    news_total.extend(newsarray)

df = pandas.DataFrame(news_total)

# 转换数据存入Excel
df.to_excel('news.xlsx')
# 数据存入数据库
with sqlite3.connect('news.sqlite') as db:
    df.to_sql('news', con = db)