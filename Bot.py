# pip install -U yt-dlp

# To read Key
from tools import *

from discord.ext import commands
from discord.ui import View, Button

# youtube

# custom libs
from yt_lib import *

intents = discord.Intents.default()
intents.message_content = True

# 대기열
queue = asyncio.Queue()
now_playing = None

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

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
    """ Skip the music """
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("노래 스킵함 ㅇㅇ")

@bot.command()
async def pause(ctx):
    """ Stop the music """
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("일시정지")

@bot.command()
async def todo(ctx, *, task: str):
    with open("todo.txt", "a", encoding="utf-8") as f:
        f.write(task + "\n")
    await ctx.send(f"📝 TODO 추가!: `{task}`")
@bot.command()
async def dokie(ctx):
    await ctx.send("핳핳 나는야 김도끼. 세상을 지배하지 핳핳")
    await ctx.send("핳핳 나는야 김도끼. 세상을 지배하지 핳핳")

@bot.command()
async def trends(ctx):
    """
    Trends music list
    """
    await ctx.send(" YouTube 실시간 음악 트렌드")
    trending_list = yt_lib.fetch_music_trending(10)
    for entry in trending_list:
        await ctx.send(entry)

@bot.command()
async def list(ctx):
    """
    List of my plans!
    """
    try:
        with open("todo.txt", "r", encoding="utf-8") as f:
            tasks = f.readlines()

        if not tasks:
            await ctx.send("할 일이 없슴")
        else:
            message = "**📋 To-Do 목록:**\n"
            for i, task in enumerate(tasks, start=1):
                message += f"{i}. {task.strip()}\n"
            await ctx.send(message)
    except FileNotFoundError:
        await ctx.send("TODO 파일없음....")

bot.run(get_discord_token())