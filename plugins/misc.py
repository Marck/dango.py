import asyncio
import collections
import io
import json
import random
import re

import aiohttp
from dango import dcog
from dango import utils
import discord
from discord.ext.commands import command
from discord.ext.commands import errors
from plugins.common.paginator import PaginatedResponse

FULLWIDTH_OFFSET = 65248

FakeEmoji = collections.namedtuple('FakeEmoji', 'name id')


def idc_emoji_or_just_string(val):
    match = re.match(r'<:([a-zA-Z0-9]+):([0-9]+)>$', val)
    if match:
        return FakeEmoji(match.group(1), match.group(2))
    return FakeEmoji(val.replace(':', ''), None)


@dcog()
class Emoji:
    def __init__(self, config):
        pass

    @command()
    async def guild_emojis(self, ctx):
        """List emojis on this server."""
        emojis = [
            "{0} - \{0}".format(emoji) for emoji in ctx.guild.emojis
        ]

        if emojis:
            await PaginatedResponse(emojis, ctx, "Guild Emojis").send()
        else:
            await ctx.message.add_reaction(":discordok:293495010719170560")

    @command(pass_context=True)
    async def find_emojis(self, ctx, *search_emojis: idc_emoji_or_just_string):
        """Find all emoji sharing the same name and the servers they are from."""
        found_emojis = [
            emoji for emoji in ctx.bot.emojis for search_emoji in search_emojis
            if emoji.name.lower() == search_emoji.name.lower()
        ]
        if found_emojis:
            by_guild = collections.defaultdict(list)
            for e in found_emojis:
                by_guild[e.guild].append(e)

            lines = ("{}: {}".format(g, "".join(map(str,emojis))) for g, emojis in by_guild.items())
            await PaginatedResponse(lines, ctx, "Found Emojis").send()
        else:
            await ctx.message.add_reaction(":discordok:293495010719170560")

    @command(pass_context=True)
    async def search_emojis(self, ctx, *query_strings: str):
        """Find all emoji containing query string."""
        found_emojis = [
            emoji for emoji in ctx.bot.emojis for query_string in query_strings
            if query_string.lower() in emoji.name.lower()
        ]
        if found_emojis:
            by_guild = collections.defaultdict(list)
            for e in found_emojis:
                by_guild[e.guild].append(e)

            lines = ("{}: {}".format(g, "".join(map(str,emojis))) for g, emojis in by_guild.items())
            await PaginatedResponse(lines, ctx, "Found Emojis").send()

        else:
            await ctx.message.add_reaction(":discordok:293495010719170560")

    @command()
    async def nitro(self, ctx, *, rest):
        rest = rest.lower()
        found_emojis = [emoji for emoji in ctx.bot.emojis if emoji.name.lower() == rest]
        if found_emojis:
            await ctx.send(str(random.choice(found_emojis)))
        else:
            await ctx.message.add_reaction(":discordok:293495010719170560")


@dcog()
class Misc:

    def __init__(self, config):
        pass

    @command(aliases=['fw', 'fullwidth', 'ａｅｓｔｈｅｔｉｃ'])
    async def aesthetic(self, ctx, *, msg="aesthetic"):
        """ａｅｓｔｈｅｔｉｃ."""
        await ctx.send("".join(map(
            lambda c: chr(ord(c) + FULLWIDTH_OFFSET) if (ord(c) >= 0x21 and ord(c) <= 0x7E) else c,
            msg)).replace(" ", chr(0x3000)))

    @command()
    async def msgsource(self, ctx, *, msg_id: int):
        try:
            msg = await ctx.get_message(msg_id)
        except discord.NotFound:
            raise errors.BadArgument("Message not found")
        else:
            await ctx.send("```{}```".format(utils.clean_triple_backtick(msg.content)))

    @command()
    async def msgraw(self, ctx, *, msg_id: int):
        raw = await ctx.bot.http.get_message(ctx.channel.id, msg_id)

        await ctx.send("```json\n{}```".format(
            utils.clean_triple_backtick(json.dumps(raw, indent=2))))

    @command()
    async def corrupt(self, ctx, *, user: discord.User=None):
        user = user or ctx.message.author
        async with aiohttp.ClientSession() as sess:
            async with sess.get(user.avatar_url_as(format='jpg')) as resp:
                img_buff = bytearray(await resp.read())
        for i in range(random.randint(5, 25)):
            img_buff[random.randint(0, len(img_buff))] = random.randint(1, 254)
        await ctx.send(file=discord.File(io.BytesIO(img_buff), filename="img.jpg"))
