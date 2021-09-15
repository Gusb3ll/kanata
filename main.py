import os
import discord
import youtube_dl
import asyncio
from ext import config
from discord.ext import commands
from cmyui import log, Ansi
from saucenao_api import SauceNao

sauce = SauceNao(api_key=config.nao_key)

client = commands.Bot(command_prefix='!', help_command=None)

log('Connecting to Discord server', Ansi.GRAY)

@client.command()
async def help(ctx):
    t1 = await ctx.send('```!play [url], !pause, !resume, !stop, !leave```')
    t2 = await ctx.send('```อยากได้วาป พิม "!warp" พร้อมแนบรูป```')
    await asyncio.sleep(15)
    await t2.delete()
    await t1.delete()

@client.command()
async def play(ctx, url: str):
    song_there = os.path.isfile('song.mp3')
    try:
        if song_there:
            os.remove('song.mp3')
    except PermissionError:
        t = await ctx.send('รอเพลงที่กำลังเล่นอยู่จบก่อนไม่ก็พิม !stop ค่ะ')
        await asyncio.sleep(10)
        await t.delete()
        return

    voiceChannel = discord.utils.get(ctx.guild.voice_channels, name='General')
    await voiceChannel.connect()
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    for file in os.listdir('./'):
        if file.endswith('.mp3'):
            os.rename(file, 'song.mp3')
    t = await ctx.send('กำลังเปิดเพลงค่ะ โปรดรอสักครู่')
    voice.play(discord.FFmpegPCMAudio('song.mp3'))
    await asyncio.sleep(10)
    await t.delete()

@client.command()
async def pause(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        t = await ctx.send('กำลังหยุดให้ค่ะ')
        voice.pause()
        await asyncio.sleep(10)
        await t.delete()
    else:
        t = await ctx.send('ตอนนี้ไม่มีเพลงที่กำลังเล่นอยู่ค่ะ')
        await asyncio.sleep(10)
        await t.delete()

@client.command()
async def resume(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_paused():
        t = await ctx.send('กำลังเริ่มเล่นให้ค่ะ')
        voice.resume()
        await asyncio.sleep(10)
        await t.delete()
    else:
        await ctx.send('เพลงกำลังเล่นอยู่แล้วค่ะ')

@client.command()
async def stop(ctx):
    t = await ctx.send('กำลังหยุดให้ค่ะ')
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    voice.stop()
    await asyncio.sleep(10)
    await t.delete()

@client.command()
async def leave(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_connected():
        await voice.disconnect()
    else:
        await ctx.send('ตอนนี้ไม่ได้เข้าห้องไหนอยู่นะคะ คนพิมมั่วแล้วค่ะ')

@client.command()
async def warp(ctx):
    await ctx.send('ส่งรูปด้วยค่ะ')
    
    def check(message):
        attachments = message.attachments
        if len(attachments) == 0:
            return False
        attachment = attachments[0]
        return attachment.filename.endswith(('.jpg', '.png'))
        
    msg = await client.wait_for('message', check=check)
    image = msg.attachments[0]

    if image:
        t = await ctx.send(f'{ctx.author.mention} กำลังหาให้อยู่นะคะ')
        res = sauce.from_url(image.url)
        await t.delete()
        e = []
        for i in res:
            if i.urls and i.similarity > 70:
                e.append(i)
        embed = discord.Embed(title=f'ผลจากการค้นหา | มี {len(e)} วาป', color=0xa5fe9f)
        embed.set_author(name=f'วาปของ {ctx.author}', icon_url=ctx.author.avatar_url)
        for i in res:
            if i.urls and i.similarity > 70:
                embed.add_field(name=f'[{i.author}] {i.title} | ✅ {i.similarity}%', value=f'{i.urls[0]}', inline=False)
        embed.set_footer(text='ได้แล้วก็เก็บไว้ด้วยค่ะ')
        
        if not e:
            return await ctx.send(f'{ctx.author.mention} หาวาปไม่เจอค่ะ สมน้ำหน้าคน horny ค่ะ')
        
        return await ctx.send(embed=embed)
    else: 
        t = await ctx.send(f'{ctx.author.mention} ไหนรูปคะ แนบรูปมาด้วยค่ะ')
        await asyncio.sleep(5)
        await t.delete()

@client.event
async def on_ready():
    activity = discord.Game(name='!help | Modified by Gusbell', type=3)
    await client.change_presence(status=discord.Status.online, activity=activity)
    log('This bot has started ⚡️', Ansi.GREEN)

client.run(config.token)
