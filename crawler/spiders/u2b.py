import os
import scrapy
import pafy


class ExampleSpider(scrapy.Spider):
    name = "u2b"

    def start_requests(self):
        if hasattr(self, 'channel'):
            url = 'https://www.youtube.com/channel/{}'.format(self.channel)
            yield scrapy.Request(url)

        if hasattr(self, 'user'):
            url = 'https://www.youtube.com/user/{}'.format(self.user)
            yield scrapy.Request(url)

    def parse(self, response):
        selstr = '#browse-items-primary > li a.yt-uix-tile-link::attr(href)'
        for href in response.css(selstr):
            url = response.urljoin(href.extract())
            if not url:
                raise Exception('No URL from href ({}) in {}'.format(href, response))
            try:
                video = pafy.new(url)

            except (OSError, TypeError) as e:
                self.logger.error(e)
            else:
                audio = video.getbestaudio(preftype="m4a")
                filepath = 'audio/{}'.format(audio.filename)
                if os.path.exists(filepath):
                    self.logger.warning('File already exists ({})'.format(filepath))
                else:
                    audio.download(filepath=filepath)
                    yield dict(
                        author=video.author,
                        channel=getattr(self, 'channel', None),
                        title=video.title,
                        user=getattr(self, 'user', None),
                    )
