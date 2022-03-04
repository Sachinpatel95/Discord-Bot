import logging
import typing

import discord
from discord.ext import commands
from discord.ext.commands.converter import Greedy
from discord_slash import SlashContext, cog_ext

from utils import helper


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.logger = logging.getLogger("Moderation")
        self.bot: commands.AutoShardedBot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("Loaded Moderation")

    @commands.command()
    async def ping(self, ctx):
        """pong 🏓"""
        await ctx.send(f"{int(self.bot.latency * 1000)} ms")

    @commands.command(alias=["clear", "purge"])
    @commands.has_guild_permissions(manage_messages=True)
    async def clean(
        self,
        ctx: commands.Context,
        amount: int,
        channel: typing.Optional[discord.TextChannel],
    ):
        """
        Clean a channel of messages
        Usage: clean amount [#channel/name/id]
        """

        if amount > 200:
            return await ctx.send("Too many messages to delete")

        if channel is None:
            amount += 1
            channel = ctx.channel

        def check(message):
            nonlocal amount
            amount -= 1
            return amount >= 0 and message.id != ctx.message.id

        deleted_messages = await channel.purge(limit=amount + 1, check=check)
        await ctx.reply(f"Deleted {len(deleted_messages)} messages")

        logging_channel = helper.get_logging_channel(ctx.guild)
        if logging_channel:
            fields = []
            f = {"name": "Deleted messages", "value": ""}
            for index, message in enumerate(reversed(deleted_messages)):

                if index != 0 and index % 5 == 0:
                    fields.append(f)
                    f = {"name": "Deleted messages", "value": ""}

                f[
                    "value"
                ] = f"{f['value']}\n {message.author.mention}: {message.content[:250]}"

            fields.append(f)

            embed = helper.create_embed(
                title="Messages cleaned",
                description=f"Deleted {len(deleted_messages)} messages in {channel.mention}",
                fields=fields,
                color=discord.Colour.green(),
            )
            await logging_channel.send(embed=embed)

    @commands.command()
    @commands.has_guild_permissions(mute_members=True)
    async def mute(
        self, ctx: commands.Context, member: discord.Member, *, reason: str = None
    ):
        """
        Mute a member.
        Usage: mute @member/name/id [reason]
        """
        mute_role = helper.get_mute_role(ctx.guild)
        if mute_role:
            await member.add_roles(mute_role, reason=reason)
            await ctx.reply("User muted.")

            logging_channel = helper.get_logging_channel(ctx.guild)
            if logging_channel:

                fields = []
                if reason:
                    fields = [{"name": "Reason", "value": reason}]

                embed = helper.create_embed(
                    title=f"Mute",
                    description=f"{member.mention} muted by {ctx.author.mention}",
                    fields=fields,
                    color=discord.Colour.orange(),
                )
                await logging_channel.send(embed=embed)

        else:
            await ctx.reply(
                f"No mute role set. Please set it using `set mute <role>` command"
            )

    @commands.command()
    @commands.has_guild_permissions(mute_members=True)
    async def unmute(self, ctx: commands.Context, member: discord.Member):
        """
        Unmute a member.
        Usage: unmute @member/name/id
        """
        mute_role = helper.get_mute_role(ctx.guild)
        if mute_role:
            await member.remove_roles(mute_role)
            await ctx.reply("User unmuted")

            logging_channel = helper.get_logging_channel(ctx.guild)
            if logging_channel:
                embed = helper.create_embed(
                    title=f"Unmute",
                    description=f"{member.mention} unmuted by {ctx.author.mention}",
                    color=discord.Colour.orange(),
                )
                await logging_channel.send(embed=embed)

        else:
            await ctx.reply(
                f"No mute role set. Please set it using `set mute <role>` command"
            )

    @commands.command()
    @commands.has_guild_permissions(kick_members=True)
    async def kick(
        self,
        ctx: commands.Context,
        user: discord.Member,
        *,
        reason: str = None,
    ):
        """kick an user
        Usage: kick @user/id <reason>
        """
        await user.kick(reason=reason)

        logging_channel = helper.get_logging_channel(ctx.guild)
        if logging_channel:
            embed = helper.create_embed(
                title="Ban",
                description=f"{user.mention} kicked by {ctx.author.mention}",
                fields=[{"name": "Reason", "value": str(reason)}],
                color=discord.Colour.red(),
            )

            await logging_channel.send(embed=embed)

        await ctx.reply(f"User banned.", delete_after=5)

    @commands.command()
    @commands.has_guild_permissions(ban_members=True)
    async def ban(
        self,
        ctx: commands.Context,
        user: discord.Member,
        *,
        reason: str = None,
    ):
        """Ban an user
        Usage: ban @user/id <reason>
        """
        await user.ban(reason=reason)

        logging_channel = helper.get_logging_channel(ctx.guild)
        if logging_channel:
            embed = helper.create_embed(
                title="Ban",
                description=f"{user.mention} banned by {ctx.author.mention}",
                fields=[{"name": "Reason", "value": str(reason)}],
                color=discord.Colour.red(),
            )

            await logging_channel.send(embed=embed)

        await ctx.reply(f"User banned.", delete_after=5)

    @commands.command()
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, id: int, *, reason=None):
        """Unban an user.
        Usage: unban id <reason>
        """

        ban_list = await ctx.guild.bans()

        logging_channel = helper.get_logging_channel(ctx.guild)

        for b in ban_list:
            if b.user.id == id:
                await ctx.guild.unban(b.user, reason=reason)

                await ctx.reply(f"Unbanned user.", delete_after=5)

                if logging_channel:
                    embed = helper.create_embed(
                        title="Un-Ban",
                        description=f"{b.user.name} unbanned by {ctx.author.mention}",
                        fields=[{"name": "Reason", "value": str(reason)}],
                        color=discord.Colour.red(),
                    )

                    await logging_channel.send(embed=embed)

    @commands.command()
    @commands.has_guild_permissions(manage_roles=True)
    async def role(
        self, ctx: commands.Context, member: discord.Member, role: discord.Role
    ):
        """
        Give or remove a role to/from a member.
        Usage: role @member/name/id @role/role_name/id
        """
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.reply(f"Removed `{role}` to {member.mention}.")

            logging_channel = helper.get_logging_channel(ctx.guild)
            if logging_channel:
                embed = helper.create_embed(
                    title=f"Removed Role",
                    description=f"Removed {role.mention} from {member.mention} by {ctx.author.mention}",
                    color=discord.Colour.greyple(),
                )
                await logging_channel.send(embed=embed)

        else:
            await member.add_roles(role)
            await ctx.reply(f"Gave `{role}` to {member.mention}.")

            logging_channel = helper.get_logging_channel(ctx.guild)
            if logging_channel:
                embed = helper.create_embed(
                    title=f"Gave Role",
                    description=f"Added {role.mention} to {member.mention} by {ctx.author.mention}",
                    color=discord.Colour.greyple(),
                )
                await logging_channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Moderation(bot))
