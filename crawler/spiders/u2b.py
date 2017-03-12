import os
import string
import scrapy
import pafy


class ExampleSpider(scrapy.Spider):
    name = "u2b"
    qty = 10

    def start_requests(self):
        if hasattr(self, 'channel'):
            url = 'https://www.youtube.com/channel/{}/videos'.format(self.channel)
            yield scrapy.Request(url)

        if hasattr(self, 'user'):
            url = 'https://www.youtube.com/user/{}/videos'.format(self.user)
            yield scrapy.Request(url)

    def parse(self, response):
        selstr = '#browse-items-primary > li a.yt-uix-tile-link::attr(href)'
        for href in response.css(selstr)[:self.qty or None]:
            url = response.urljoin(href.extract())
            if not url:
                raise Exception('No URL from href ({}) in {}'.format(href, response))
            if 'watch' not in url:
                self.log('Bad href parsed ({})'.format(url))
                continue
            try:
                video = pafy.new(url)
            except (OSError, TypeError) as e:
                self.logger.error(e)
                continue

            audio = video.getbestaudio(preftype="m4a")
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
