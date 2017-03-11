import scrapy
import pafy


class ExampleSpider(scrapy.Spider):
    name = "u2b-channel"

    def start_requests(self):
        url = 'https://www.youtube.com/channel/{}'.format(self.channel)
        yield scrapy.Request(url)

    def parse(self, response):
        selstr = '#browse-items-primary>li a.yt-uix-tile-link::attr(href)'
        for href in response.css(selstr):
            url = response.urljoin(href.extract())
            if not url:
                raise Exception('No URL from href ({}) in {}'.format(href, response))

            video = pafy.new(url)
            audio = video.getbestaudio()
            audio.download(filepath='audio/{}'.format(audio.filename))

            yield dict(
                channel=self.channel,
                author=video.author,
                title=video.title,
            )
