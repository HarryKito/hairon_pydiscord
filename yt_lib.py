import discord
import asyncio
import yt_dlp

ytdl_format_options = {
    'format': 'bestaudio[ext=m4a]/bestaudio/best',
    'quiet': True,
    'noplaylist': True,
}

# ffmpeg settings
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')

    @classmethod
    async def from_url(cls, url, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url']
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


def fetch_music_trending(limit=10):
    """
        Trends 음악 리스트 출력하기!
    """
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'dump_single_json': True,
    }

    music_trending_url = 'https://www.youtube.com/feed/trending?bp=4gINGgt5dG1hX2NoYXJ0cw%3D%3D'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(music_trending_url, download=False)

    results = []
    for i, entry in enumerate(info['entries'][:limit]):
        results.append(f"{i+1}. {entry['title']} - https://youtube.com{entry['url']}")
    return results


if __name__ == '__main__':
    print(fetch_music_trending())