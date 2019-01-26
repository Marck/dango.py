"""Tags!

Tag types:
 - Image gallery tags
   - Folder on disk, with images in it. "imgmemes"
 - Image macro tags
   - Image base, font, justifcation, border, maxwidth, etc.
   - Love, hate, etc.
 - Text tags
   - "textmemes"
   - Use creatable.
 - Custom tags
   - Python custom image generation (everything else).
"""
import asyncio
import io
import os
import random
import time

import aiohttp
import yarl
from dango import dcog
import discord
from discord.ext.commands import command, check, errors, group
from PIL import Image, ImageFont, ImageDraw

from .common import converters
from .common import checks

ALLOWED_EXT = {'jpg', 'jpeg', 'png', 'gif', 'webp'}


def _allowed_ext(filename):
    return os.path.splitext(filename)[1][1:] in ALLOWED_EXT


class TagCommand:
    """Base class for server opt-in commands."""


class CommandAlias:
    """Register a command as an alias under a different namespace."""

    async def callback(self, ctx, *args, **kwargs):
        pass


class ImgDirCmd(discord.ext.commands.Command):
    def __init__(self, name, directory):
        super().__init__(name, self.callback)
        self.directory = directory
        self.module = self.__module__

    async def callback(self, ctx, idx: int=None):
        files = [f for f in os.listdir(self.directory)
                 if _allowed_ext(f)]
        if idx is None or 0 > idx >= len(files):
            idx = random.randrange(0, len(files))
        f = os.path.join(self.directory, sorted(files)[idx])
        await ctx.send(file=discord.File(f, filename="{}_{}{}".format(
            self.name, idx, os.path.splitext(f)[1])))


class ImgFileCmd(discord.ext.commands.Command):
    def __init__(self, name, filename):
        super().__init__(name, self.callback)
        self.filename = filename
        self.upload_name = "{}{}".format(
            self.name, os.path.splitext(filename)[1])
        self.module = self.__module__

    async def callback(self, ctx, idx: int=None):
        await ctx.send(file=discord.File(self.filename, filename=self.upload_name))


async def fetch_image(url):
    """Fetch the given image."""
    async with aiohttp.ClientSession() as sess:
        # proxy_url must be passed exactly - encoded=True
        # https://github.com/aio-libs/aiohttp/issues/3424#issuecomment-443760653
        async with sess.get(yarl.URL(url, encoded=True)) as resp:
            try:
                resp.raise_for_status()
                content_length = int(resp.headers.get('Content-Length', 50<<20))
                if content_length > 50<<20:
                    raise errors.BadArgument("File too big")

                blocks = []
                readlen = 0
                tested_image = False
                # Read up to X bytes, raise otherwise
                while True:
                    block = await resp.content.readany()
                    if not block:
                        break
                    blocks.append(block)
                    readlen += len(block)
                    if readlen >= 10<<10 and not tested_image:
                        try:
                            Image.open(io.BytesIO(b''.join(blocks)))
                        except OSError:
                            raise errors.BadArgument("This doesn't look like an image to me")
                        else:
                            tested_image = True
                    if readlen > content_length:
                        raise errors.BadArgument("File too big")
                source_bytes = b''.join(blocks)
            finally:
                # Workaround https://github.com/aio-libs/aiohttp/issues/3426
                if resp.connection:
                    resp.connection.transport.abort()
    return source_bytes


@dcog(["Database"], pass_bot=True)
class Fun:

    def __init__(self, bot, config, database):
        self.db = database
        self.image_galleries_dir = config.register("image_galleries_dir")
        self._init_image_galleries(bot, self.image_galleries_dir())


    @group()
    async def meme(self, ctx):
        pass

    def _init_image_galleries(self, bot, imgdir):
        """Load and register commands based on on-disk image gallery dir."""
        for item in os.listdir(imgdir):
            fullpath = os.path.join(imgdir, item)
            if os.path.isdir(fullpath):
                cmd = ImgDirCmd(item, fullpath)
            elif os.path.isfile(fullpath):
                if not _allowed_ext(item):
                    continue
                cmd = ImgFileCmd(os.path.splitext(item)[0], fullpath)
            cmd.instance = self
            self.meme.add_command(cmd)
            bot.add_command(cmd)

def get_lum(r,g,b,a=1):
    return (0.299*r + 0.587*g + 0.114*b) * a

@dcog(["Res"])
class ImgFun:

    def __init__(self, cfg, res):
        self.res = res

    @command()
    async def corrupt(self, ctx, *, user: converters.UserMemberConverter=None):
        """Corrupt a user's avatar."""
        user = user or ctx.message.author
        img_buff = bytearray(await fetch_image(user.avatar_url_as(format="jpg")))
        for i in range(random.randint(5, 25)):
            img_buff[random.randint(0, len(img_buff))] = random.randint(1, 254)
        await ctx.send(file=discord.File(io.BytesIO(img_buff), filename="img.jpg"))

    @staticmethod
    def _gifmap(avy1, avy2):
        """stolen from cute."""
        maxres = 200
        avy1 = Image.open(avy1).resize((maxres,maxres), resample=Image.BICUBIC)
        avy2 = Image.open(avy2).resize((maxres,maxres), resample=Image.BICUBIC)

        avy1data = avy1.load()
        avy1data = [[(x,y),avy1data[x,y]] for x in range(maxres) for y in range(maxres)]
        avy1data.sort(key = lambda c : get_lum(*c[1]))

        avy2data = avy2.load()
        avy2data = [[(x,y),avy2data[x,y]] for x in range(maxres) for y in range(maxres)]
        avy2data.sort(key = lambda c : get_lum(*c[1]))

        frames = []
        for mult in range(-10,11,1):
            m = 1 - (1/(1+(1.7**-mult)))

            base = Image.new('RGBA', (maxres,maxres))
            basedata = base.load()
            for i, d in enumerate(avy1data):
                x1, y1 = d[0]
                x2, y2 = avy2data[i][0]
                x, y = round(x1 + (x2 - x1)*m), round(y1 + (y2 - y1) * m)
                basedata[x, y] = avy2data[i][1]
            frames.append(base)

        frames = frames + frames[::-1]

        b = io.BytesIO()
        frames[0].save(b, 'gif', save_all=True, append_images=frames[1:], loop=0, duration=60)
        b.seek(0)
        return b

    @command()
    @checks.bot_needs(["attach_files"])
    async def colormap3(self, ctx, source: discord.Member, dest: discord.Member = None):
        """Hello my name is Koishi."""
        dest = dest or ctx.author

        start = time.time()
        async with ctx.typing():
            source_bytes = await fetch_image(source.avatar_url_as(format="png"))
            dest_bytes = await fetch_image(dest.avatar_url_as(format="png"))

            img_buff = await ctx.bot.loop.run_in_executor(None,
                    self._gifmap, io.BytesIO(dest_bytes), io.BytesIO(source_bytes)
                )
        elapsed = time.time() - start
        await ctx.send("took %02fs" % elapsed,
            file=discord.File(img_buff, filename="%s_to_%s.gif" % (source, dest)))


    @staticmethod
    def make_dot():
        width = 512
        img = Image.new('RGBA', (width, 1))
        img.putpixel((random.randrange(0, width), 0), 0xff0000ff)
        buff = io.BytesIO()
        img.save(buff, 'png')
        buff.seek(0)
        return buff


    @command()
    @checks.bot_needs(["attach_files"])
    async def dot(self, ctx):
        res = await ctx.bot.loop.run_in_executor(None, self.make_dot)
        await ctx.send(file=discord.File(res, filename="dot.png"))

    def make_dont_image(self, content):
        inset = Image.open(io.BytesIO(content))

        img = Image.new('RGB', (800, 600), 'White')

        img.paste(inset.resize((400, 400)), (271, 17, 671, 417))

        img.paste(inset.resize((128, 128)), (190, 387, 318, 515))

        f = ImageFont.truetype(
            font=self.res.dir() + "/font/comic sans ms/comic.ttf",
            size=26, encoding="unic")

        ayy = ImageDraw.Draw(img)

        ayy.text((340, 430), "dont talk to me or my son\never again",
                 (0, 0, 0), font=f)

        buff = io.BytesIO()
        img.save(buff, 'jpeg')

        buff.seek(0)

        return buff

    @command()
    @checks.bot_needs(["attach_files"])
    async def dont(self, ctx, *, url: converters.AnyImage=converters.AuthorAvatar):
        """dont run me or my son ever again"""
        print(url)
        if url is None:
            url = ctx.message.author.get_avatar_url(format='png')
            if not url:
                url = ctx.message.author.default_avatar_url

        with ctx.typing():
            content = await fetch_image(url)
            img_buff = await ctx.bot.loop.run_in_executor(None, self.make_dont_image, content)

            await ctx.send(file=discord.File(img_buff, filename="dont.jpg"))
