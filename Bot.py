# To read Key
import json


import discord
from discord.ext import commands
import asyncio
import yt_dlp

intents = discord.Intents.default()
intents.message_content = True

# 대기열
queue = asyncio.Queue()
now_playing = None


# JSON :: Discord Bot Token
def discord_token():
    with open("key.json", "r") as f:
        return json.load(f)["discord"]

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

ytdl_format_options = {
    'format': 'bestaudio[ext=m4a]/bestaudio/best',
    'quiet': True,
    'noplaylist': True,
}

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

async def play_next(ctx):
    global now_playing
    if queue.empty():
        now_playing = None
        return

    url = await queue.get()
    try:
        player = await YTDLSource.from_url(url, loop=bot.loop)
        now_playing = player
        ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        await ctx.send(f'재생 중: {player.title}')
    except Exception as e:
        await ctx.send(f"재생 중 오류 발생: {e}")
        return

@bot.command()
async def play(ctx, url):
    if not ctx.voice_client:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
            await ctx.send("음성 채널로 이동!")
        else:
            await ctx.send("음성 채널에 먼저 접속해주세요.")
            return

    await queue.put(url)
    await ctx.send("대기열에 추가함. ")

    # 재생중? --> 아니면 바로 재생
    if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        await play_next(ctx)

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("노래 스킵함 ㅇㅇ")

@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("일시정지")

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("다시 재생할게 ㅋ")

bot.run(discord_token())