import datetime
import logging
import typing

import discord
from discord.ext import commands

from utils import helper


class Stat(commands.Cog):
    def __init__(self, bot):
        self.logger = logging.getLogger("Stat")
        self.bot: commands.AutoShardedBot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("Loaded Stat")

    @commands.group(invoke_without_command=False)
    async def info(self, ctx: commands.Context):
        """Command description"""
        pass

    @info.command(aliases=["member"])
    async def user(self, ctx: commands.Context, user: discord.Member = None):
        """Get information about an user."""

        if not user:
            user = ctx.author

        u = await commands.UserConverter().convert(ctx, str(user.id))

        embed = discord.Embed(
            title=f"{user.name}#{user.discriminator}'s Information",
            description=f"ID: {user.id}",
            color=user.color,
            timestamp=datetime.datetime.utcnow(),
        )

        embed.set_thumbnail(url=u.avatar_url)

        embed.add_field(
            name="Account Created At",
            value=user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            inline=False,
        )
        embed.add_field(
            name="Joined Server At",
            value=f"{user.joined_at.strftime('%Y-%m-%d %H:%M:%S')}",
        )
        if len(user.roles) > 1:
            embed.add_field(
                name="Roles",
                value=", ".join(
                    [r.mention or "" for r in user.roles if r.name != "@everyone"]
                ),
            )
        if user.premium_since:
            embed.add_field(
                name="Nitro Member Since", value=user.premium_since, inline=False
            )

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Stat(bot))
