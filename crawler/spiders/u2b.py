import os
import string
import scrapy
import pafy


class ExampleSpider(scrapy.Spider):
    name = "u2b"
    qty = 10
    length = 60 * 50  # 50 min max default, 0 for no limit

    @property
    def _qty(self):
        if self.qty:
            return int(self.qty)

    @property
    def _length(self):
        if self.length:
            return int(self.length)

    def start_requests(self):
        if hasattr(self, 'channel'):
            url = 'https://www.youtube.com/channel/{}/videos'.format(self.channel)
            yield scrapy.Request(url)

        if hasattr(self, 'user'):
            url = 'https://www.youtube.com/user/{}/videos'.format(self.user)
            yield scrapy.Request(url)

    def parse(self, response):
        selstr = '#browse-items-primary > li a.yt-uix-tile-link::attr(href)'
        for href in response.css(selstr)[:self._qty]:
            url = response.urljoin(href.extract())
            if not url:
                raise Exception('No URL from href ({}) in {}'.format(href, response))
            if 'watch' not in url:
                self.logger.error('Bad href parsed ({})'.format(url))
                continue
            try:
                video = pafy.new(url)
            except (OSError, TypeError) as e:
                self.logger.error(e)
                continue

            if self._length and video.length > self._length:
                self.logger.warning(
                    'Video too long ({}), not downloading, {} > {}'.format(
                        video.duration, video.length, self._length))
                continue

            audio = video.getbestaudio(preftype="m4a")
            # print('@@@', href.extract(), video.title, audio.filename)
            filepath = _get_filepath(video, audio)
            if os.path.exists(filepath):
                self.logger.warning('File already exists ({})'.format(filepath))
            else:
                audio.download(filepath=filepath)
                yield dict(
                    channel=getattr(self, 'channel', None),
                    author=video.author,
                    title=video.title,
                    date=video.published,
                    path=filepath,
                    user=getattr(self, 'user', None),
                    url=url,
                )


def _get_filepath(video, audio):
    date = video.published.partition(' ')[0]
    white_chars = string.ascii_letters + string.digits + ' ' + '_' + '-' + '.'
    blackname = '{}_{}_{}'.format(video.author, date, audio.filename)
    whitename = ''.join(c for c in blackname if c in (white_chars)).replace(' ', '_')
    filepath = os.path.join('audio', whitename)

    return filepath
