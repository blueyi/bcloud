
# Copyright (C) 2014 LiuLang <gsushzhsosgsu@gmail.com>
# Use of this source code is governed by GPLv3 license that can be found
# in http://www.gnu.org/licenses/gpl-3.0.html

import gettext
import json
import os

from gi.repository import Gtk

NAME = 'bcloud'
if __file__.startswith('/usr/local/'):
    PREF = '/usr/local/share'
elif __file__.startswith('/usr/'):
    PREF = '/usr/share'
else:
    PREF = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'share')

LOCALEDIR = os.path.join(PREF, 'locale')
gettext.bindtextdomain(NAME, LOCALEDIR)
gettext.textdomain(NAME)
_ = gettext.gettext

APPNAME = _('BCloud')
VERSION = '2.1.3'
HOMEPAGE = 'https://github.com/LiuLang/bcloud'
AUTHORS = ['LiuLang <gsushzhsosgsu@gmail.com>', ]
COPYRIGHT = 'Copyright (c) 2014 LiuLang'
DESCRIPTION = _('Baidu Pan client for GNU/Linux desktop users.')

HOME_DIR = os.path.expanduser('~')
CACHE_DIR = os.path.join(HOME_DIR, '.cache', NAME)

# Check Gtk version <= 3.6
GTK_LE_36 = (Gtk.MAJOR_VERSION == 3) and (Gtk.MINOR_VERSION <= 6)

CONF_DIR = os.path.join(HOME_DIR, '.config', NAME)
_conf_file = os.path.join(CONF_DIR, 'conf.json')

_default_profile = {
    'version': VERSION,
    'window-size': (960, 680),
    'use-status-icon': True,
    'use-notify': False,
    'first-run': True,
    'save-dir': HOME_DIR,
    'concurr-tasks': 2,
    'username': '',
    'password': '',
    'remember-password': False,
    'auto-signin': False,
    }

_base_conf = {
    'default': '',
    'profiles': [],
    }

def check_first():
    '''这里, 要创建基本的目录结构'''
    if not os.path.exists(CONF_DIR):
        os.makedirs(CONF_DIR, exist_ok=True)
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def load_conf():
    '''获取基本设定信息, 里面存放着所有可用的profiles, 以及默认的profile'''
    if os.path.exists(_conf_file):
        with open(_conf_file) as fh:
            return json.load(fh)
    else:
        dump_conf(_base_conf)
        return _base_conf

def dump_conf(conf):
    with open(_conf_file, 'w') as fh:
        json.dump(conf, fh)

def load_profile(profile_name):
    '''读取特定帐户的配置信息'''
    path = os.path.join(CONF_DIR, profile_name)
    if os.path.exists(path):
        with open(path) as fh:
            return json.load(fh)
    else:
        return _default_profile

def dump_profile(profile):
    path = os.path.join(CONF_DIR, profile['username'])
    with open(path, 'w') as fh:
        json.dump(profile, fh)

def get_cache_path(profile_name):
    '''获取这个帐户的缓存目录, 如果不存在, 就创建它'''
    path = os.path.join(CACHE_DIR, profile_name, 'cache')
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return path
