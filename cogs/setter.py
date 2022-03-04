import logging

import discord
from discord.ext import commands

from utils import helper


class Setter(commands.Cog):
    def __init__(self, bot):
        self.logger = logging.getLogger("Setter")
        self.bot: commands.AutoShardedBot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("Loaded Setter")

    @commands.group(invoke_without_command=False)
    @commands.has_guild_permissions(manage_guild=True)
    async def set(self, ctx: commands.Context):
        """Set stuff"""
        pass

    @set.command(aliases=["logging"])
    @commands.has_guild_permissions(manage_guild=True)
    async def logging_channel(
        self, ctx: commands.Context, channel: discord.TextChannel
    ):
        """
        Set logging channel.
        Usage: set logging #channel/id
        """
        helper.set_logging_channel(ctx.guild, channel)
        await ctx.reply(
            f"Logging channel set to {helper.get_logging_channel(ctx.guild).mention}"
        )

    @set.command(aliases=["mute"])
    @commands.has_guild_permissions(manage_guild=True)
    async def mute_role(self, ctx: commands.Context, role: discord.Role):
        """
        Set mute role.
        Usage: set mute @role/id
        """
        helper.set_mute_role(ctx.guild, role)
        await ctx.reply(f"Mute role set to `{helper.get_mute_role(ctx.guild)}`")


def setup(bot):
    bot.add_cog(Setter(bot))
