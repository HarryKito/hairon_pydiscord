# pip install -U yt-dlp

# To read Key
from tools import *
from gtts import gTTS

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
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("음악 다시 재생할게용")


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

@bot.command()
async def play(ctx, url):
    try:
        await ctx.message.delete()  # 사용자 입력 령명어 삭제
    except discord.Forbidden:
        pass
    except discord.HTTPException:
        pass

    if not ctx.voice_client:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
            msg = await ctx.send("음성 채널로 이동!")
            await asyncio.sleep(3)
            await msg.delete()
        else:
            msg = await ctx.send("음성 채널에 먼저 접속하셈..")
            await asyncio.sleep(3)
            await msg.delete()
            return

    if is_url(url):
        await queue.put(url)
        await ctx.send("URL 대기열에 추가!")

        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            await play_next(ctx)
    else:
        await show_search_results(ctx, url)
        return

    msg = await ctx.send("대기열에 추가함.")
    await asyncio.sleep(3)
    await msg.delete()

    if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        await play_next(ctx)


@bot.command()
async def tts(ctx, *, text: str):
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass
    except discord.HTTPException:
        pass

    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if not ctx.voice_client:
            await channel.connect()
        elif ctx.voice_client.channel != channel:
            await ctx.voice_client.move_to(channel)
    else:
        await ctx.send("음성 채널에 먼저 접속하셈.")
        return

    # Create the TTS and save
    # FIXME: 흐음... 이 방법이 최선인가?
    tts = gTTS(text=text, lang='ko')
    filename = "tts.mp3"
    tts.save(filename)

    # Stop the music
    vc = ctx.voice_client
    if vc.is_playing():
        vc.stop()

    source = discord.FFmpegPCMAudio(filename)
    volume_source = discord.PCMVolumeTransformer(source, volume=5)
    # done = False

    # FIXME: Stop the music when the tts played, after then play music again...
    vc.play(volume_source, after=lambda e: vc.resume())
    await ctx.send(f"TTS 재생: `{text}`")


@bot.command()
async def skip(ctx):
    try:
        await ctx.message.delete()
    except (discord.Forbidden, discord.HTTPException):
        pass
    """ Skip the music """
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("노래 스킵함 ㅇㅇ")


@bot.command()
async def pause(ctx):
    """ Stop the music """
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("STOP to playing")

@bot.command()
async def todo(ctx, *, task: str):
    with open("todo.txt", "a", encoding="utf-8") as f:
        f.write(task + "\n")
    await ctx.send(f"TODO 추가!: `{task}`")

@bot.command()
async def dokie(ctx):
    for i in range(10):
        await ctx.send("핳핳 나는야 김도끼. 세상을 지배하지 핳핳")

@bot.command()
async def trends(ctx):
    """
    Trends music list
    """
    await ctx.send(" YouTube 실시간 음악 트렌드")
    trending_list = fetch_music_trending(10)
    for entry in trending_list:
        await ctx.send(entry)

@bot.command()
async def list(ctx):
    try:
        with open("todo.txt", "r", encoding="utf-8") as f:
            tasks = f.readlines()

        if not tasks:
            await ctx.send(" 할 일이 없어!")
        else:
            header = f"{'번호':<4} | {'할 일':<30}\n"
            separator = "-" * 40 + "\n"
            rows = [f"{i+1:<4} | {task.strip():<30}\n" for i, task in enumerate(tasks)]
            table = "```" + header + separator + "".join(rows) + "```"
            await ctx.send(table)
    except FileNotFoundError:
        await ctx.send("TODO 파일없음....")

bot.run(get_discord_token())