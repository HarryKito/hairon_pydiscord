# To read Key
import json
import re

import discord
from discord.ext import commands
from discord.ui import View, Button
import asyncio
import yt_dlp

intents = discord.Intents.default()
intents.message_content = True

# 대기열
queue = asyncio.Queue()
now_playing = None


# JSON :: Discord Bot Token
def get_discord_token():
    with open("key.json", "r") as f:
        return json.load(f)["discord"]

def is_url(string):
    # 정규 URL 패턴
    url_pattern = re.compile(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$')
    return bool(url_pattern.match(string))

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
        await ctx.send(f"재생 중 오류 발생: {e}\n 자동으로 다음 곡 재생합니다.")
        await play_next(ctx)
        # return

# 검색 결과 보여주기
async def show_search_results(ctx, search_term):
    search_query = f"ytsearch5:{search_term}"
    info = ytdl.extract_info(search_query, download=False)
    results = info.get("entries", [])

    if not results:
        await ctx.send("검색 결과 없음..")
        return

    # 버튼 뷰! 사용자가 직접 선택 가능하도록
    view = View()
    for index, entry in enumerate(results):
        button = Button(label=entry["title"][:80], style=discord.ButtonStyle.primary)
        async def button_callback(interaction, url=entry["webpage_url"], title=entry["title"]):
            await interaction.response.defer()
            await queue.put(url)
            await interaction.followup.send(f"선택: {title}")
            if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
                await play_next(ctx)

        button.callback = button_callback
        view.add_item(button)

    await ctx.send("원하는 곡을 선택하세요:", view=view)

@bot.command()
async def play(ctx, url):
    if not ctx.voice_client:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
            await ctx.send("음성 채널로 이동!")
        else:
            await ctx.send("음성 채널에 먼저 접속하셈..")
            return

    if is_url(url):
        await queue.put(url)
        await ctx.send("URL 대기열에 추가!")
        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            await play_next(ctx)
    else:
        await show_search_results(ctx, url)

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

bot.run(get_discord_token())