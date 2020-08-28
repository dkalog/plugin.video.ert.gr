# -*- coding: utf-8 -*-

'''
    ERTflix Addon
    Author Twilight0

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
'''

from __future__ import absolute_import

import json, re
from os.path import exists as file_exists
from zlib import decompress
from base64 import b64decode
from tulip import bookmarks, directory, client, cache, control, workers, cleantitle
from tulip.compat import iteritems, range, quote, parse_qsl, urlencode
from tulip.parsers import itertags_wrapper, parseDOM
from youtube_resolver import resolve as yt_resolver
from youtube_registration import register_api_keys
from youtube_plugin.youtube.youtube_exceptions import YouTubeException


def _plot(url):

    load = client.request(url.partition('?')[0], post=url.partition('?')[2], timeout=20)

    description = parseDOM(load, 'div', {'class': 'video-description'})[-1]
    paragraphs = [client.stripTags(p) for p in parseDOM(description, 'p')]
    plot = client.replaceHTMLCodes('[CR]'.join(paragraphs))

    return plot


def meta_viewer(url):

    heading = control.infoLabel('Listitem.Label')

    plot = cache.get(_plot, 96, url)

    control.dialog.textviewer(heading=heading, text=plot)


class Indexer:

    def __init__(self):

        self.list = []; self.data = []

        self.base_link = 'https://www.ertflix.gr'
        self.old_base = 'https://webtv.ert.gr'
        self.search_link = ''.join([self.base_link, '/?s={}'])
        self.category_link = ''.join([self.base_link, '/category'])
        self.ajax_url = ''.join([self.base_link, '/wp-admin/admin-ajax.php'])
        self.load_more = 'action=loadmore_post_by_cat&query={query}&page={page}'
        self.load_search = 'action=load_search_post_info&item_id={data_id}'

        self.index_link = ''.join([self.base_link, '/ekpompes/'])
        self.recent_link = ''.join([self.base_link, '/feed/'])
        self.shows_link = ''.join([self.old_base, '/shows'])

        self.sports_link = ''.join([self.category_link, '/athlitika/'])

        self.news_link = ''.join([self.category_link, '/enimerosi-24/'])
        self.cartoons_link = ''.join([self.category_link, '/pedika/'])
        self.entertainment_link = ''.join([self.category_link, '/psichagogia/'])
        self.interviews_link = ''.join([self.category_link, '/synentefxeis/'])
        self.archive_link = ''.join([self.category_link, '/arxeio/'])

        self.ellinika_docs = ''.join([self.category_link, '/ellhnika-docs/'])
        self.ksena_docs = ''.join([self.category_link, '/ksena-docs/'])

        self.movies_link = ''.join([self.category_link, '/tainies/'])
        self.series_link = ''.join([self.category_link, '/ksenes-seires/'])
        self.web_series_link = ''.join([self.category_link, '/web-series/'])

        self.ert1_link = ''.join([self.base_link, '/ert1-live/'])
        self.ert2_link = ''.join([self.base_link, '/ert2-live/'])
        self.ert3_link = ''.join([self.base_link, '/ert3-live/'])
        self.ertw_link = ''.join([self.base_link, '/ertworld-live/'])
        self.erts_link = ''.join([self.base_link, '/ert-sports-live/'])

        self.radio_link = 'https://webradio.ert.gr'
        self.radio_stream = 'http://radiostreaming.ert.gr'
        self.district_link = ''.join([self.radio_link, '/liveradio/list.html'])
        self.channel_id = 'UC0jVU-mK53vDQZcSZB5mVHg'
        self.scramble = (
            'eJwVzMEOgiAAANBfcZzTZWBBt5xtpmsecqVdGiqQqUGAbdb69+YHvPcFbQO2DkA+XBLsBxjjjdsPiKueYKqGpuHQmuV9Z'
            'YPuIbSs1kYTjyplPCGl6NlomK7l07Kn9Wo5gIUDqGpvHZvmdnf40NMUElLkkGdhl+gUx++xKGl1dbN92kp5hmg3K8Nqze'
            'yMYhQmj/U+jY6V4Jv8hS7S3so4Ar8/Amw3tA=='
        )

        self.keys_registration()
        self.check_inputstream_addon()

    def root(self):

        self.list = [
            {
                'title': control.lang(30001),
                'action': 'channels',
                'icon': 'channels.jpg'
            }
            ,
            {
                'title': control.lang(30002),
                'action': 'recent',
                'icon': 'recent.jpg'
            }
            ,
            {
                'title': control.lang(30015),
                'action': 'youtube',
                'icon': 'youtube.jpg',
                'url': ''.join(
                    ['plugin://plugin.video.youtube/channel/', self.channel_id, '/?addon_id=', control.addonInfo('id')]
                ),
                'isFolder': 'False', 'isPlayable': 'False'
            }
            ,
            {
                'title': control.lang(30011),
                'action': 'index',
                'icon': 'index.jpg'
            }
            ,
            {
                'title': control.lang(30004),
                'action': 'listing',
                'url': self.news_link,
                'icon': 'news.jpg'
            }
            ,
            {
                'title': control.lang(30049),
                'action': 'listing',
                'icon': 'movies.jpg',
                'url': self.movies_link
            }
            ,
            {
                'title': control.lang(30020),
                'action': 'shows',
                'icon': 'shows.jpg'
            }
            ,
            {
                'title': control.lang(30038),
                'action': 'series',
                'icon': 'series.jpg'
            }
            ,
            {
                'title': control.lang(30003),
                'action': 'listing',
                'url': self.sports_link,
                'icon': 'sports.jpg'
            }
            ,
            {
                'title': control.lang(30009),
                'action': 'listing',
                'icon': 'kids.jpg',
                'url': self.cartoons_link
            }
            ,
            {
                'title': control.lang(30055),
                'action': 'listing',
                'url': self.archive_link,
                'icon': 'archive.jpg'
            }
            ,
            {
                'title': control.lang(30013),
                'action': 'search',
                'icon': 'search.jpg',
                'isFolder': 'False', 'isPlayable': 'False'
            }
            ,
            {
                'title': control.lang(30012),
                'action': 'bookmarks',
                'icon': 'bookmarks.jpg'
            }
            ,
            {
                'title': control.lang(30026),
                'action': 'radios',
                'icon': 'radio.jpg'
            }
        ]

        settings_menu = {
                'title': control.lang(30044),
                'action': 'settings',
                'icon': 'settings.jpg',
                'isFolder': 'False', 'isPlayable': 'False'
            }

        if control.setting('settings_boolean') == 'true':
            self.list.append(settings_menu)

        for item in self.list:

            cache_clear = {'title': 30036, 'query': {'action': 'cache_clear'}}
            settings = {'title': 30039, 'query': {'action': 'settings'}}
            item.update({'cm': [cache_clear, settings]})

        directory.add(self.list, content='videos')

    def channels(self):

        self.list = [
            {
                'title': control.lang(30021),
                'url': self.ert1_link,
                'icon': 'EPT1.png'
            }
            ,
            {
                'title': control.lang(30022),
                'url': self.ert2_link,
                'icon': 'EPT2.png'
            }
            ,
            {
                'title': control.lang(30023),
                'url': self.ert3_link,
                'icon': 'EPT3.png'
            }
            ,
            {
                'title': control.lang(30024),
                'url': self.ertw_link,
                'icon': 'EPT WORLD.png'
            }
            ,
            {
                'title': control.lang(30041),
                'url': self.erts_link,
                'icon': 'EPT SPORTS.png'
            }
        ]

        for i in self.list:

            i.update({'action': 'play', 'isFolder': 'False', 'fanart': control.addonmedia('live_fanart.jpg')})

        directory.add(self.list, content='videos')

    def bookmarks(self):

        self.list = bookmarks.get()

        if not self.list:
            na = [{'title': control.lang(30058), 'action': None}]
            directory.add(na)
            return

        for i in self.list:
            bookmark = dict((k, v) for k, v in iteritems(i) if not k == 'next')
            bookmark['delbookmark'] = i['url']
            i.update({'cm': [{'title': 30502, 'query': {'action': 'deleteBookmark', 'url': json.dumps(bookmark)}}]})

        control.sortmethods('title')

        if control.setting('bookmarks_clear_boolean') == 'true':

            clear_menu = {
                'title': control.lang(30059), 'action': 'clear_bookmarks'
            }

            self.list.insert(0, clear_menu)

        directory.add(self.list, content='videos')

    def index_listing(self):

        html = client.request(self.index_link)

        div = parseDOM(html, 'div', attrs={'class': 'wpb_wrapper'})[0]

        li = parseDOM(div, 'li')

        li.extend(parseDOM(div, 'li', attrs={'class': 'hideli'}))

        items = [i for i in li if 'category' in i and 'title' in i]

        for item in items:

            title = client.replaceHTMLCodes(parseDOM(item, 'a')[0])
            url = parseDOM(item, 'a', ret='href')[0]

            self.list.append({'title': title, 'url': url})

        return self.list

    def index(self):

        self.list = cache.get(self.index_listing, 48)

        if self.list is None:
            return

        for i in self.list:
            i.update({'action': 'listing'})

        for i in self.list:
            bookmark = dict((k, v) for k, v in iteritems(i) if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 30006, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        self.list = sorted(self.list, key=lambda k: k['title'].lower())

        directory.add(self.list, content='videos')

    def thread(self, url, post=None):

        result = client.request(url, post=post, timeout=20)
        self.data.append(result)

    def loop(self, item, header, count, next_url=None):

        data_id = item.attributes['data-id']
        img = item.attributes['style']
        image = re.search(r'url\((.+)\)', img).group(1)
        url = [i for i in itertags_wrapper(item.text, 'a', ret='href') if 'https' in i][0]
        meta_url = '?'.join([self.ajax_url, self.load_search.format(data_id=data_id)])

        if 'inside-page-thumb-titles' in item.text and control.setting('metadata') == 'false':

            fanart = None
            plot = None
            title = parseDOM(item.text, 'div', attrs={'class': 'inside-page-thumb-titles'})[0]
            title = client.replaceHTMLCodes(parseDOM(title, 'a')[0])

        else:

            load = client.request(self.ajax_url, post=self.load_search.format(data_id=data_id), timeout=20)
            title = parseDOM(load, 'p', {'class': 'video-title'})[0].strip()
            title = client.replaceHTMLCodes(title)
            description = parseDOM(load, 'div', {'class': 'video-description'})[-1]
            paragraphs = [client.stripTags(p) for p in parseDOM(description, 'p')]
            plot = client.replaceHTMLCodes('[CR]'.join(paragraphs))
            f = parseDOM(load, 'div', attrs={'class': 'cover'}, ret='style')[0]
            fanart = re.search(r'url\((.+)\)', f).group(1)

        data = {'title': title, 'image': image, 'url': url, 'code': count, 'meta_url': meta_url}

        if next_url:

            data.update({'next': next_url})

        if header in [
            u'TV ΣΕΙΡΕΣ', u'ΨΥΧΑΓΩΓΙΑ', u'ΣΥΝΕΝΤΕΥΞΕΙΣ', u'ΕΛΛΗΝΙΚΑ ΝΤΟΚΙΜΑΝΤΕΡ', u'ΞΕΝΑ ΝΤΟΚΙΜΑΝΤΕΡ',
            u'ΠΑΙΔΙΚΑ', u'Η ΕΡΤ ΘΥΜΑΤΑΙ', u'ΑΘΛΗΤΙΚΑ', u'WEB ΣΕΙΡΕΣ'
        ] and not 'archeio' in url and header is not None:
            data.update({'playable': 'false'})

        if fanart:
            data.update({'fanart': fanart})
        if plot:
            data.update({'plot': plot})

        self.list.append(data)

    def _listing(self, url):

        if self.ajax_url in url:
            result = client.request(url.partition('?')[0], post=url.partition('?')[2])
        else:
            result = client.request(url)

        try:
            header = parseDOM(result, 'h2')[0]
        except IndexError:
            header = None

        next_url = None
        override = False

        if self.base_link + '/?s=' in url or control.setting('pagination') == 'true':
            override = True

        # Nest the function to work on either of the two cases
        def _exec(_items, _next_url=None):

            if control.setting('threading') == 'true':

                for count, _item in list(enumerate(_items, start=1)):

                    threads_2.append(workers.Thread(self.loop(_item, header, count, _next_url)))

                [i.start() for i in threads_2]
                [i.join() for i in threads_2]

            else:

                for count, _item in list(enumerate(_items, start=1)):

                    self.loop(_item, header, count, _next_url)

        if 'enimerosi-24' not in url and self.ajax_url not in url:

            ajaxes = [i for i in parseDOM(result, 'script', attrs={'type': 'text/javascript'}) if 'ajaxurl' in i]

            ajax1 = json.loads(re.search(r'var loadmore_params = ({.+})', ajaxes[-1]).group(1))
            ajax2 = json.loads(re.search(r'var cactus = ({.+})', ajaxes[0]).group(1))

            ajax = self._ajax_merge(ajax1, ajax2)
            pages = int(ajax['max_page'])
            posts = ajax['posts']

            try:
                posts = posts.encode('utf-8')
            except Exception:
                pass

            threads_1 = []
            threads_2 = []

            if control.setting('threading') == 'true' and not override:

                for i in range(0, pages + 1):
                    threads_1.append(
                        workers.Thread(
                            self.thread(self.ajax_url, post=self.load_more.format(query=quote(posts), page=str(i)))
                        )
                    )

                [i.start() for i in threads_1]
                [i.join() for i in threads_1]

            else:

                for i in range(0, pages + 1):

                    a = client.request(self.ajax_url, post=self.load_more.format(query=quote(posts), page=str(i)))
                    self.data.append(a)

                    if i == 0 and override:
                        next_url = '?'.join([self.ajax_url, self.load_more.format(query=quote(posts), page='1')])
                        break

            html = '\n'.join(self.data)

            items = itertags_wrapper(html, 'div', attrs={'class': 'item item-\d+'})

            if len(items) < 20:
                next_url = None

            _exec(items, next_url)

        elif self.ajax_url in url:

            items = itertags_wrapper(result, 'div', attrs={'class': 'item item-\d+'})

            parsed = dict(parse_qsl(url.partition('?')[2]))

            next_page = int(parsed['page']) + 1

            parsed['page'] = next_page

            if len(items) >= 20:
                next_url = '?'.join([url.partition('?')[0], urlencode(parsed)])

            _exec(items, next_url)

        else:

            items = itertags_wrapper(result, 'div', attrs={'class': 'item item-\d+'})

            for item in items:

                text = item.text

                img = item.attributes['style']
                image = re.search(r'url\((.+)\)', img).group(1)
                title = client.replaceHTMLCodes(parseDOM(text, 'a')[0].strip())
                url = parseDOM(text, 'a', ret='href')[0]

                self.list.append({'title': title, 'image': image, 'url': url})

        return self.list

    def listing(self, url):

        self.list = cache.get(self._listing, 6, url)

        if self.list is None:
            return

        for i in self.list:

            if i.get('playable') == 'false':
                del i['playable']
                i.update({'action': 'listing'})
            else:
                i.update({'action': 'play', 'isFolder': 'False'})

            bookmark = dict((k, v) for k, v in iteritems(i) if not k == 'next')
            bookmark['bookmark'] = i['url']
            bookmark_cm = {'title': 30501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}

            if 'enimerosi-24' in url or 'meta_url' not in i:
                i.update({'cm': [bookmark_cm]})
            else:
                info_cm = {'title': 30043, 'query': {'action': 'info', 'url': i['meta_url']}}
                i.update({'cm': [bookmark_cm, info_cm]})

        if control.setting('pagination') == 'true':

            for i in self.list:

                i.update({'nextaction': 'listing', 'nextlabel': 30500, 'nexticon': control.addonmedia('next.jpg')})

        if 'tainies' in url or 'seires' in url or 'docs' in url or 'pedika' in url:

            control.sortmethods()
            control.sortmethods('title')
            control.sortmethods('production_code')

        if 'tainies' in url:
            content = 'movies'
        elif 'category' in url or 'arxeio' in url and not 'enimerosi-24' in url:
            content = 'tvshows'
        else:
            content = 'videos'

        directory.add(self.list, content=content)

    def recent_list(self, url):

        try:

            result = client.request(url)
            items = parseDOM(result, 'item')

        except Exception:

            return

        for item in items:

            title = client.replaceHTMLCodes(parseDOM(item, 'title')[0])

            url = parseDOM(item, 'link')[0]

            image = parseDOM(item, 'img', ret='src')[0]

            self.list.append({'title': title, 'url': url, 'image': image})

        return self.list

    def recent(self):

        self.list = cache.get(self.recent_list, 1, self.recent_link)

        if self.list is None:
            return

        for i in self.list:
            i.update({'action': 'play', 'isFolder': 'False'})

        directory.add(self.list, content='videos')

    def play(self, url):

        stream = cache.get(self.resolve, 96, url)

        if stream is None:
            return

        m3u8_dash = 'm3u8' in stream and control.kodi_version() >= 18.0

        directory.resolve(
            stream, dash=any(['.mpd' in stream, m3u8_dash]),
            mimetype='application/vnd.apple.mpegurl' if m3u8_dash else None,
            manifest_type='hls' if m3u8_dash else None
        )

    def series(self):

        self.list = [
            {
                'title': control.lang(30057),
                'url': self.series_link,
                'icon': 'series.jpg'
            }
            ,
            {
                'title': control.lang(30054),
                'url': self.web_series_link,
                'icon': 'series.jpg'
            }
        ]

        for i in self.list:
            i.update({'action': 'listing'})

        directory.add(self.list)

    def shows(self):

        self.list = [
            {
                'title': control.lang(30010),
                'url': self.entertainment_link,
                'icon': 'shows.jpg'
            }
            ,
            {
                'title': control.lang(30016),
                'url': self.interviews_link,
                'icon': 'interviews.jpg'
            }
            ,
            {
                'title': control.lang(30017),
                'url': self.ksena_docs,
                'icon': 'documentaries.jpg'
            }
            ,
            {
                'title': control.lang(30018),
                'url': self.ellinika_docs,
                'icon': 'documentaries.jpg'
            }
        ]

        for i in self.list:
            i.update({'action': 'listing'})

        directory.add(self.list)

    def search(self):

        input_str = control.inputDialog()

        try:
            input_str = cleantitle.strip_accents(input_str.decode('utf-8'))
        except (UnicodeEncodeError, UnicodeDecodeError, AttributeError):
            input_str = cleantitle.strip_accents(input_str)

        input_str = quote(input_str.encode('utf-8'))

        directory.run_builtin(action='listing', url=self.search_link.format(input_str))

    def radios(self):

        images = [
            ''.join([self.radio_link, i]) for i in [
                '/wp-content/uploads/2016/06/proto.jpg', '/wp-content/uploads/2016/06/deytero.jpg',
                '/wp-content/uploads/2016/06/trito.jpg', '/wp-content/uploads/2016/06/kosmos.jpg',
                '/wp-content/uploads/2016/06/VoiceOgGreece.png', '/wp-content/uploads/2016/06/eraSport.jpg',
                '/wp-content/uploads/2016/06/958fm.jpg', '/wp-content/uploads/2016/06/102fm.jpg'
            ]
        ]

        names = [control.lang(n) for n in list(range(30028, 30036))]

        urls = [
            ''.join([self.radio_stream, i]) for i in [
                '/ert-proto', '/ert-deftero', '/ert-trito', '/ert-kosmos', '/ert-voiceofgreece', '/ert-erasport',
                '/ert-958fm', '/ert-102fm'
            ]
        ]

        radios = map(lambda x, y, z: (x, y, z), names, images, urls)

        for title, image, link in radios:

            self.list.append(
                {
                    'title': title, 'url': link, 'image': image, 'action': 'play', 'isFolder': 'False',
                    'fanart': control.addonmedia('radio_fanart.jpg')
                }
            )

        district = {
            'title': control.lang(30027), 'action': 'district', 'icon': 'district.jpg',
            'fanart': control.addonmedia('radio_fanart.jpg')
        }

        self.list.append(district)

        directory.add(self.list)

    def district_list(self):

        try:
            try:
                result = client.request(self.district_link).decode('windows-1253')
            except AttributeError:
                result = client.request(self.district_link)
            radios = parseDOM(result, 'td')
            radios = [r for r in radios if r]

        except Exception:

            return

        for radio in radios:

            title = parseDOM(radio, 'a')[0]
            href = parseDOM(radio, 'a', ret='href')[0]
            html = client.request(href)
            link = parseDOM(html, 'iframe', ret='src')[0]
            embed = client.request(link)
            url = re.search(r'mp3: [\'"](.+?)[\'"]', embed).group(1).replace('https', 'http')
            image = parseDOM(html, 'img', ret='src')[0]

            self.list.append(
                {'title': title, 'image': image, 'url': url}
            )

        return self.list

    def district(self):

        self.list = cache.get(self.district_list, 96)

        if self.list is None:
            return

        for i in self.list:
            i.update({'action': 'play', 'isFolder': 'False', 'fanart': control.addonmedia('radio_fanart.jpg')})

        directory.add(self.list)

    def resolve(self, url):

        _url = url

        if 'radiostreaming' in url:

            return url

        elif 'youtube' in url or len(url) == 11:

            if url.startswith('plugin://'):
                url = url[-11:]

            return self.yt_session(url)

        else:

            html = client.request(url)

            if 'iframe' in html:

                iframe = parseDOM(html, 'iframe', ret='src')[0]

            else:

                availability = parseDOM(html, 'strong')[-1]
                control.okDialog(control.name(), availability)

                return 'https://static.adman.gr/inpage/blank.mp4'

            if 'youtube' in iframe:

                return self.resolve(iframe)

            else:

                result = client.request(iframe)
                urls = re.findall(r'(?:var )?(?:HLSLink|stream)(?:ww)?\s+=\s+[\'"](.+?)[\'"]', result)

                if urls:

                    geo = cache.get(self._geo_detect, 192)

                    if len(urls) >= 2:

                        if _url.endswith('-live/'):

                            if not geo:
                                return urls[-1]
                            else:
                                return urls[0]

                        else:

                            url = [i for i in urls if 'dvrorigingr' in i][0]

                            try:
                                video_ok = client.request(url, timeout=3)
                            except Exception:
                                video_ok = None

                            if video_ok:

                                return url

                            else:

                                url = [i for i in urls if 'dvrorigin' in i][0]

                                return url

                    else:

                        if 'youtube' in urls[0]:
                            return self.resolve(urls[0])
                        else:
                            return urls[0]

                else:

                    iframes = parseDOM(result, 'iframe', ret='src')

                    try:
                        return self.resolve(iframes[-1])
                    except YouTubeException:
                        return self.resolve(iframes[0])

    def keys_registration(self):

        filepath = control.transPath(
            control.join(control.addon('plugin.video.youtube').getAddonInfo('profile'), 'api_keys.json'))

        setting = control.addon('plugin.video.youtube').getSetting('youtube.allow.dev.keys') == 'true'

        if file_exists(filepath):

            f = open(filepath)

            jsonstore = json.load(f)

            no_keys = control.addonInfo('id') not in jsonstore.get('keys', 'developer').get('developer')

            if setting and no_keys:

                keys = json.loads(decompress(b64decode(self.scramble)))
                register_api_keys(control.addonInfo('id'), keys['api_key'], keys['id'], keys['secret'])

            f.close()

    @staticmethod
    def _geo_detect():

        _json = client.request('https://geoip.siliconweb.com/geo.json', output='json')

        if 'GR' in _json['country']:
            return True

    @staticmethod
    def yt_session(yt_id):

        streams = yt_resolver(yt_id)

        try:
            addon_enabled = control.addon_details('inputstream.adaptive').get('enabled')
        except KeyError:
            addon_enabled = False

        if not addon_enabled:

            streams = [s for s in streams if 'mpd' not in s['title'].lower()]

        stream = streams[0]['url']

        return stream

    @staticmethod
    def check_inputstream_addon():

        try:
            addon_enabled = control.addon_details('inputstream.adaptive').get('enabled')
        except KeyError:
            addon_enabled = False

        leia_plus = control.kodi_version() >= 18.0

        first_time_file = control.join(control.dataPath, 'first_time')

        if not addon_enabled and not file_exists(first_time_file) and leia_plus:

            try:

                yes = control.yesnoDialog(control.lang(30003))

                if yes:
                    control.enable_addon('inputstream.adaptive')
                    control.infoDialog(control.lang(30402))

                with open(first_time_file, 'a'):
                    pass

            except Exception:

                pass

    @staticmethod
    def yt(url):

        control.execute('Container.Update({},return)'.format(url))

    @staticmethod
    def _ajax_merge(d1, d2):

        d = d1.copy()
        d.update(d2)

        return d
