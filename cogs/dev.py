import math
import io
import textwrap
import traceback
from contextlib import redirect_stdout
import logging

import discord
from discord.ext import commands
from discord.ext.commands.core import command
from discord.ext.commands.errors import ExtensionNotLoaded


class Dev(commands.Cog):
    def __init__(self, bot):
        self.logger = logging.getLogger("Dev")
        self.bot: commands.AutoShardedBot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("Loaded Dev")

    def cleanup_code(self, content):
        """
        Remove code-block from eval
        """
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])

        return content.strip("`\n")

    def get_syntax_error(self, e):
        if e.text is None:
            return f"```py\n{e.__class__.__name__}: {e}\n```"
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    @commands.is_owner()
    @commands.command(pass_context=True, name="eval", hidden=True)
    async def eval(self, ctx, *, body: str):
        """Evaluates a code"""
        env = {
            "bot": self.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "self": self,
            "math": math,
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f"```py\n{e.__class__.__name__}: {e}\n```")

        func = env["func"]
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            value = stdout.getvalue()
            await ctx.send(f"```py\n{value}{traceback.format_exc()}\n```")
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction("\u2705")
            except Exception as _:
                await ctx.message.add_reaction("\u274C")
                pass

            if ret is None:
                self.logger.info(f"Output chars: {len(str(value))}")
                if value:
                    if len(str(value)) >= 2000:
                        await ctx.send(
                            f"Returned over 2k chars, sending as file instead.\n"
                            f"(first 1.5k chars for quick reference)\n"
                            f"```py\n{value[0:1500]}\n```",
                            file=discord.File(
                                io.BytesIO(value.encode()), filename="output.txt"
                            ),
                        )
                    else:
                        await ctx.send(f"```py\n{value}\n```")
            else:
                self.logger.info(f"Output chars: {len(str(value)) + len(str(ret))}")
                self._last_result = ret
                if len(str(value)) + len(str(ret)) >= 2000:
                    await ctx.send(
                        f"Returned over 2k chars, sending as file instead.\n"
                        f"(first 1.5k chars for quick reference)\n"
                        f'```py\n{f"{value}{ret}"[0:1500]}\n```',
                        file=discord.File(
                            io.BytesIO(f"{value}{ret}".encode()), filename="output.txt"
                        ),
                    )
                else:
                    await ctx.send(f"```py\n{value}{ret}\n```")

    @commands.is_owner()
    @commands.command(name="reload", hidden=True, aliases=["r"])
    async def reload(self, ctx: commands.Context, *, module: str):
        """Reload a module"""

        if module == "all":
            names = [f"cogs.{key.lower()}" for key in self.bot.cogs.keys().__iter__()]

            for name in names:
                try:
                    self.logger.debug(f"{name=}")
                    self.bot.reload_extension(name)
                    await ctx.send(f"Reloaded {name[5:]}")
                except ExtensionNotLoaded as enl:
                    await ctx.send(f"Unable to reload {name[5:]}")

        else:
            if "cogs" not in module:
                module = f"cogs.{module}"
            try:
                self.bot.reload_extension(module)
                await ctx.send("Module Loaded")
            except ExtensionNotLoaded as enl:
                await ctx.send(
                    f"Unable to reload {module}, possibly no such module exist.",
                    delete_after=5,
                )

    @commands.command()
    async def test(
        self,
        ctx: commands.Context,
    ):
        x = 1 / 0


def setup(bot):
    bot.add_cog(Dev(bot))
