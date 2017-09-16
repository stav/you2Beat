import os
import string
import scrapy
import pafy


class U2bSpider(scrapy.Spider):
    name = "u2b"

    def __init__(self, **kwargs):
        self.qty = 10
        self.audio = True
        self.video = False
        self.length = 60 * 50  # 50 minute maximum, 0 for no limit
        super().__init__(**kwargs)

    @property
    def _qty(self):
        return int(self.qty)

    @property
    def _length(self):
        return int(self.length)

    @property
    def _audio(self):
        return bool(int(self.audio))

    @property
    def _video(self):
        return bool(int(self.video))

    def start_requests(self):
        if hasattr(self, 'channel'):
            url = 'https://www.youtube.com/channel/{}/videos'.format(self.channel)
            yield scrapy.Request(url)

        if hasattr(self, 'user'):
            url = 'https://www.youtube.com/user/{}/videos'.format(self.user)
            yield scrapy.Request(url)

    def parse(self, response):
        selstr = '#browse-items-primary > li a.yt-uix-tile-link::attr(href)'
        # selstr = 'div.yt-lockup-content a::attr(href)'
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

            paths = []

            if self._audio:
                path = self.download_audio(video)
                paths.append(path)

            if self._video:
                path = self.download_video(video)
                paths.append(path)

            yield dict(
                channel=getattr(self, 'channel', None),
                author=video.author,
                title=video.title,
                date=video.published,
                path=paths,
                user=getattr(self, 'user', None),
                url=url,
            )

    def download_audio(self, video):
        audio = video.getbestaudio(preftype="m4a")
        filepath = _get_filepath_audio(video, audio.filename)
        if os.path.exists(filepath):
            self.logger.warning('File already exists ({})'.format(filepath))
        else:
            audio.download(filepath=filepath)

        return filepath

    def download_video(self, video):
        stream = video.getbest(preftype="mp4")
        filepath = _get_filepath_video(video, stream.filename)
        if os.path.exists(filepath):
            self.logger.warning('File already exists ({})'.format(filepath))
        else:
            stream.download(filepath=filepath)

        return filepath


def _get_filename(video, filename):
    date = video.published.partition(' ')[0]
    white_chars = string.ascii_letters + string.digits + ' ' + '_' + '-' + '.'
    blackname = '{}_{}_{}'.format(video.author, date, filename)
    whitename = ''.join(c for c in blackname if c in (white_chars)).replace(' ', '_')

    return whitename


def _get_filepath_audio(video, filename):
    filename = _get_filename(video, filename)
    filepath = os.path.join('audio', filename)

    return filepath


def _get_filepath_video(video, filename):
    filename = _get_filename(video, filename)
    filepath = os.path.join('video', filename)

    return filepath
