
# Copyright (C) 2013-2014 LiuLang <gsushzhsosgsu@gmail.com>
# Use of this source code is governed by GPLv3 license that can be found
# in http://www.gnu.org/licenses/gpl-3.0.html

'''
这个模块主要是用于从百度服务器取得cookie授权.
'''

import json
import os
import random
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
import const
import encoder
from RequestCookie import RequestCookie
import net
import util


def get_ppui_logintime():
    '''ppui_ligintime 这个字段, 是一个随机数.'''
    return str(random.randint(25000, 28535))

def get_BAIDUID():
    '''获取一个cookie - BAIDUID.

    这里, 我们访问百度首页, 返回的response header里面有我们需要的cookie
    '''
    req = net.urlopen(const.BAIDU_URL)
    return req.headers.get_all('Set-Cookie')

def get_token(cookie):
    '''获取一个页面访问的token, 这里需要之前得到的BAIDUID 这个cookie值

    这个token的有效期还不确定.
    '''
    url = ''.join([
        const.PASSPORT_URL,
        '?getapi&tpl=mn&apiver=v3',
        '&tt=', util.timestamp(),
        '&class=login&logintype=dialogLogin',
        #'&callback=bd__cbs__d1ypgy',
        ])
    req = net.urlopen(url, headers={'Cookie': cookie.header_output()})
    content = req.data
    content = content.decode().replace("'", '"')
    content_obj = json.loads(content)
    return content_obj['data']['token']

def get_UBI(cookie, token):
    '''检查登录历史, 可以获得一个Cookie - UBI.'''
    url = ''.join([
        const.PASSPORT_URL,
        '?loginhistory',
        '&token=', token,
        '&tpl=pp&apiver=v3',
        '&tt=', util.timestamp(),
        #'&callback=bd__cbs__7sxvvm',
        ])
    req = net.urlopen(url, headers={'Cookie': cookie.header_output()})
    return req.headers.get_all('Set-Cookie')


def check_login(cookie, token, username):
    '''进行登录验证, 主要是在服务器上验证这个帐户的状态.

    如果帐户不存在, 或者帐户异常, 就不需要再进行最后一步的登录操作了.
    这一步有可能需要输入验证码.
    @return 返回errInfo.no, 如果为0, 表示一切正常, 可以登录.
    '''
    url = ''.join([
        const.PASSPORT_URL,
        '?logincheck',
        '&token=', token,
        '&tpl=mm&apiver=v3',
        '&tt=', util.timestamp(),
        '&username=', username,
        '&isphone=false',
        ])
    req = net.urlopen(url, headers={'Cookie': cookie.header_output()})
    content = req.data
    print('content:', content)
    # TODO: FIXME: 如果返回的codestring非空, 我们就需要解析验证码了.
    content_obj = json.loads(content.decode())
    return int(content_obj['errInfo']['no'])

def get_bduss(cookie, token, username, password):
    '''获取最重要的登录cookie, 拿到这个cookie后, 就得到了最终的访问授权.

    token - 使用get_token()得到的token值.
    cookie - BAIDUID 这个cookie.
    username - 用户名
    password - 明文密码

    @return 最后会返回一个list, 里面包含了登录*.baidu.com需要的授权cookies.
    '''
    url = const.PASSPORT_URL + '?login'
    data = ''.join([
        'staticpage=http%3A%2F%2Fwww.baidu.com%2Fcache%2Fuser%2Fhtml%2Fv3Jump.html',
        '&charset=utf-8',
        '&token=', token,
        '&tpl=mn&apiver=v3',
        '&tt=', util.timestamp(),
        '&codestring=&safeflg=0&u=https%3A%2F%2Fpassport.baidu.com%2F',
        '&isPhone=false&quick_user=0',
        #'&loginmerge=true&logintype=basicLogin',
        '&usernamelogin=1&spligin=rate',
        '&username=', username,
        '&password=', password,
        '&verifycode=&mem_pass=on',
        '&ppui_logintime=', get_ppui_logintime(),
        '&callback=parent.bd__pcbs__cb',
        ])
    req = net.urlopen(url, headers={
        'Cookie': cookie.header_output(),
        'Content-type': const.CONTENT_FORM,
        }, data=data.encode())
    return req.headers.get_all('Set-Cookie')

def parse_bdstoken(content):
    '''从页面中解析出bdstoken等信息.
    
    这些信息都位于页面底部的<script>, 只有在授权后的页面中才出现.
    这里, 为了保证兼容性, 就不再使用cssselect模块解析了.

    @return 返回一个dict, 里面包含bdstoken, cktoken, sysUID这三项.
    '''
    auth = {'bdstoken': '', 'cktoken': '', 'sysUID': ''}
    uid_re = re.compile('sysUID="([^"]+)"')
    uid_match = uid_re.search(content)
    if uid_match:
        auth['sysUID'] = uid_match.group(1)

    bds_re = re.compile('bdstoken="([^"]+)"')
    bds_match = bds_re.search(content)
    if bds_match:
        auth['bdstoken'] = bds_match.group(1)

    ck_re = re.compile('cktoken="([^"]+)"')
    ck_match = ck_re.search(content)
    if ck_match:
        auth['cktoken'] = ck_match.group(1)
    return auth

def get_bdstoken(cookie):
    '''从/disk/home页面获取bdstoken等token信息

    这些token对于之后的请求非常重要.
    '''
    url = 'http://pan.baidu.com/disk/home'
    req = net.urlopen(url, headers={'Cookie': cookie.header_output()})
    return parse_bdstoken(req.data.decode())

def get_auth_info(username, password):
    '''获取授权信息.

    username - 用户名
    password - 明文密码
    '''
    cookie = RequestCookie()
    cookie.load('cflag=65535%3A1; PANWEB=1;')
    cookie.load_list(get_BAIDUID())
    token = get_token(cookie)
    cookie.load_list(get_UBI(cookie, token))
    status = check_login(cookie, token, username)
    if status != 0:
        print('Error: failed to check login!')
        return (None, None)
    cookie.load_list(get_bduss(cookie, token, username, password))
    tokens = get_bdstoken(cookie)
    tokens['token'] = token
    auth_info = [str(cookie), tokens]
    if 'bdstoken' not in tokens or not tokens['bdstoken']:
        return (None, None)
    return (cookie, tokens)

