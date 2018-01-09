#!/usr/bin/env python

from pushover_complete import PushoverAPI
import flickrapi

import ConfigParser
import datetime
import argparse
import sys
import os
import json

from xml.etree import ElementTree
from collections import defaultdict

def etree_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v
                     for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v)
                        for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
              d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d

def base58encode(num):
    a='123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ'
    bc=len(a)
    enc=''
    while num>=bc: 
        div,mod=divmod(num,bc) 
        enc = a[mod]+enc 
        num = int(div)
    return a[num]+enc 

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config", action="store", help="configuration file")
parser.add_argument("-p", "--prefix", action="store", help="prefix directory where events are stored")
parser.add_argument("directories", nargs='+', help="process the given directories")
args = parser.parse_args()

if not args.config:
    sys.exit(1)
if not args.prefix:
    sys.exit(2)
if not args.directories:
    sys.exit(3)

config = ConfigParser.ConfigParser()
config.read(args.config)

push_app_key = config.get('Pushover', 'app_key')
push_user_key = config.get('Pushover', 'user_key')
flickr_key = config.get('Flickr', 'key')
flickr_secret = config.get('Flickr', 'secret')
flickr_token_cache = config.get('Flickr', 'token-cache')

p = PushoverAPI(push_app_key) 
flickr = flickrapi.FlickrAPI(
    flickr_key, 
    flickr_secret, 
    token_cache_location=flickr_token_cache
)

def upload(file_path, location, time_stamp, event_name, info):
    tags = ['zoneminder', location, info]
    tag_text = ' '.join(map(lambda s: '"'+s+'"', tags))
    response = flickr.upload(
        filename=file_path,
        title=location + ' ' + time_stamp + ' ' + event_name,
        description=location + ' ' + time_stamp + ' ' + event_name,
        tags=tag_text,
        is_public=0,
        is_family=0,
        is_friend=0
    )
    try:
        d = etree_to_dict(response)
        return d['rsp']['photoid']
    except Exception as e:
        p.send_message(
            push_user_key, 
            'upload failed: '+str(e),
            title=info + ': ' + location + ' ' + time_stamp + ' ' + event_name,
            priority=1
        )
        return None


for path in args.directories:
    event_dir = path[len(args.prefix):]
    components = map(int, event_dir.lstrip('/').rstrip('/').split('/'))
    day = map(lambda x: "%02i" % x, components[1:4])
    day_path = os.path.join(args.prefix, str(components[0]), *day)
    time = map(lambda x: "%02i" % x, components[4:])
    time_path = os.path.join(*time)
    links = [x for x in os.listdir(day_path) if os.path.islink(os.path.join(day_path, x))]
    event_name = '?'
    for link in links:
        if time_path == os.readlink(os.path.join(day_path, link)):
            event_name = link[1:]
            break
    components[1] += 2000
    location = config.get('ZoneMinder', str(components.pop(0)))
    time_stamp = datetime.datetime(*components).strftime("%Y-%m-%d_%H:%M:%S")
    files = [x for x in os.listdir(path) if os.path.isfile(os.path.join(path, x))]
    alarms = [x for x in files if "-analyse" in x]
    consider = files
    if alarms:
        consider = alarms
    to_send = consider[len(consider)/3]
    messages = list()
    if os.path.isfile(os.path.join(path,'event.mp4')):
        video_id = upload(os.path.join(path,'event.mp4'), location, time_stamp, event_name, 'video')
        if video_id:
            messages.append('<a href="https://flic.kr/p/%s">video</a>' % (base58encode(int(video_id))))
    photo_id = upload(os.path.join(path,to_send), location, time_stamp, event_name, 'image')
    if photo_id:
        messages.append('<a href="https://flic.kr/p/%s">image</a>' % (base58encode(int(photo_id))))
    p.send_message(
        push_user_key, 
        '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'.join(messages),
        title=location + ' ' + time_stamp + ' ' + event_name,
        html=1,
        priority=0,
    )
