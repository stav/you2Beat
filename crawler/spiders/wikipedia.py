import scrapy
import pafy


class WikipediaSpider(scrapy.Spider):
    name = "wikipedia"
    byear = 1965
    eyear = 1970
    no = 1

    def start_requests(self):
        for year in range(self.byear, self.eyear):
            yield scrapy.Request(
                'https://en.wikipedia.org/wiki/'
                'Billboard_Year-End_Hot_100_singles_of_{}'.format(year),
                meta=dict(year=year)
            )

    def parse(self, response):
        xpath = (
            'id("mw-content-text")/table'
            '//tr['
            'normalize-space(td|th/text())="{}"'
            ']'.format(self.no, self.no))
        tr = response.xpath(xpath)
        title = tr.xpath('*[2]/a/text()').extract_first()
        artist = tr.xpath('*[3]/a/text()').extract_first()
        item = dict(
            year=response.meta['year'],
            no=self.no,
            title=title,
            artist=artist,
        )
        query = title + ' ' + artist
        url = 'https://www.youtube.com/results?search_query={}'.format(query)
        return scrapy.Request(
            url,
            meta=dict(item=item),
            callback=self.parse_youtube,
        )

    def parse_youtube(self, response):
        item = response.meta['item']
        year = item['year']
        xpath = 'id("results")/ol/li[2]/ol/li[1]/div/@data-context-item-id'
        id = response.xpath(xpath).extract_first()
        url = 'https://www.youtube.com/watch?v={}'.format(id)
        video = pafy.new(url)
        audio = video.getbestaudio()
        audio.download(filepath='audio/{} {}'.format(year, audio.filename))

        return item
