import pathlib
import random
import re
from multiprocessing.dummy import Pool
from os import linesep

import pyquery
import requests

from conf import *

DOWNLOAD_URL = f'http://{DOMAIN}/view_video.php?viewkey='
KEY_URL_PREFIX = f'http://{DOMAIN}/v.php?next=watch&category=rp&page='

_path = pathlib.Path(f'./{STORAGE}')
_path.mkdir(exist_ok=True)


def download_mp4(title, url, mp4, detail, txt, referer):
    print('starting: ' + title)
    headers = {'Accept-Language': 'zh-CN,zh;q=0.9',
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)'
                             'AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/51.0.2704.106 Safari/537.36',
               'X-Forwarded-For': random_ip(),
               'referer': referer,
               'Content-Type': 'video/mp4; session_language=cn_CN'}
    req = requests.get(url=url, headers=headers, timeout=300)
    if req.status_code == 200:
        with mp4.open(mode='wb') as mp4_f, txt.open(mode='w') as txt_f:
            mp4_f.write(req.content)
            txt_f.write(detail)
            print(f'complete: {title}')
    else:
        print(f'failed: {title}')


def random_ip():
    return '.'.join([str(random.randint(1, 255)) for _ in range(4)])


def gen_view_keys(max_page=10000):
    page = 1
    while page < max_page:
        headers = {'Accept-Language': 'zh-CN,zh;q=0.9',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)'
                                 'AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/51.0.2704.106 Safari/537.36',
                   'X-Forwarded-For': random_ip(),
                   'referer': f'{KEY_URL_PREFIX}{page}',
                   'Content-Type': 'multipart/form-data; session_language=cn_CN'}

        resp = requests.get(url=f'{KEY_URL_PREFIX}{page}', headers=headers)
        page_content = str(resp.content, 'utf-8', errors='ignore')
        if page_content:
            view_keys = re.findall(
                fr'href="http://{DOMAIN}/view_video.php' r'\?viewkey=(.*)&page=', page_content)
            for key in set(view_keys):
                yield key, page

        page += 1


def decode_download_url(arg1, arg2):
    try:
        resp = requests.get(DECODESERVER, params={'a1': arg1, 'a2': arg2})
        query = pyquery.PyQuery(resp.text)
        return query('source').attr('src')
    except:
        return ''


def do(args):
    key, page = args
    try:
        headers = {'Accept-Language': 'zh-CN,zh;q=0.9',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) '
                                 'AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/51.0.2704.106 Safari/537.36',
                   'X-Forwarded-For': random_ip(),
                   'referer': f'{KEY_URL_PREFIX}{page}',
                   'Content-Type': 'multipart/form-data; session_language=cn_CN'}
        download_resp = requests.get(url=DOWNLOAD_URL + key, headers=headers)
        html = str(download_resp.content, 'utf-8', errors='ignore')
        query = pyquery.PyQuery(html)

        title = query('#viewvideo-title').text()
        detail = query('#videodetails').find('.more').text().strip().replace('<br>', linesep)
        date = re.findall(r'(\d\d\d\d-\d\d-\d\d)', query('#videodetails').text())[0]

        video_url = query('#vid').find('script').text()
        video_url_args = re.findall(r'.*strencode\(\"(.*)\",.*\"(.*)\",.*\)', video_url)[0]
        download_url = decode_download_url(*video_url_args)
        length_of_time = re.search(r'\d\d:\d\d', query('#useraction').text()).group()
        length_of_minute = int(length_of_time.split(':')[0])

        if length_of_minute in range(0, 20):
            path = pathlib.Path(f'{STORAGE}{date}')
            path.mkdir(exist_ok=True)
            mp4 = path / (title + '.mp4')
            txt = path / (title + '.txt')
            if not mp4.exists():
                download_mp4(title, download_url, mp4, detail, txt, referer=DOWNLOAD_URL + key)
            else:
                print(f'exist: {title}')

    except Exception as e:
        print(e)
        print(download_url)


def main():
    pool = Pool(CONCURRENCE)
    pool.imap(do, gen_view_keys())
    pool.close()
    pool.join()


if __name__ == '__main__':
    main()
