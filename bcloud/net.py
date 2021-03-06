
# Copyright (C) 2013-2014 LiuLang <gsushzhsosgsu@gmail.com>
# Use of this source code is governed by GPLv3 license that can be found
# in http://www.gnu.org/licenses/gpl-3.0.html

import copy
import gzip
import http
import os
import sys
import urllib.parse
import urllib.request
import zlib

sys.path.insert(0, os.path.dirname(__file__))
import const

RETRIES = 1

default_headers = {
    'User-agent': const.USER_AGENT,
    'Referer': const.PAN_REFERER,
    'x-requested-with': 'XMLHttpRequest',
    'Accept': const.ACCEPT_JSON,
    'Accept-language': 'zh-cn, zh',
    'Accept-encoding': 'gzip, deflate',
    'Pragma': 'no-cache',
    'Cache-control': 'no-cache',
    }

class ForbiddenHandler(urllib.request.HTTPErrorProcessor):

    def http_error_403(self, req, fp, code, msg, headers):
        return fp
    http_error_400 = http_error_403
    http_error_500 = http_error_403


def urlopen(url, headers={}, data=None, retries=RETRIES):
    '''打开一个http连接, 并返回Request.

    headers 是一个dict. 默认提供了一些项目, 比如User-Agent, Referer等, 就
    不需要重复加入了.

    这个函数只能用于http请求, 不可以用于下载大文件.
    如果服务器支持gzip压缩的话, 就会使用gzip对数据进行压缩, 然后在本地自动
    解压.
    req.data 里面放着的是最终的http数据内容, 通常都是UTF-8编码的文本.
    '''
    headers_merged = copy.copy(default_headers)
    for key in headers.keys():
        headers_merged[key] = headers[key]
    opener = urllib.request.build_opener(ForbiddenHandler)
    opener.addheaders = [(k, v) for k,v in headers_merged.items()]

    for _ in range(retries):
        try:
            req = opener.open(url, data=data)
            encoding = req.headers.get('Content-encoding')
            req.data = req.read()
            if encoding == 'gzip':
                req.data = gzip.decompress(req.data)
            elif encoding == 'deflate':
                req.data = zlib.decompress(req.data, -zlib.MAX_WBITS)
            return req
        except OSError as e:
            print('Error in net.urlopen :', e, ', with url:', url)
        return None

def urlopen_without_redirect(url, headers={}, data=None, retries=RETRIES):
    '''请求一个URL, 并返回一个Response对象. 不处理重定向.

    使用这个函数可以返回URL重定向(Error 301/302)后的地址, 也可以重到URL中请
    求的文件的大小, 或者Header中的其它认证信息.
    '''
    headers_merged = copy.copy(default_headers)
    for key in headers.keys():
        headers_merged[key] = headers[key]

    parse_result = urllib.parse.urlparse(url)
    for _ in range(retries):
        try:
            conn = http.client.HTTPConnection(parse_result.netloc)
            #conn.request('HEAD', url, body=data, headers=headers_merged)
            conn.request('GET', url, body=data, headers=headers_merged)
            return conn.getresponse()
        except OSError as e:
            print(e)
        return None
