import time
import os
from discord.ext.commands.bot import AutoShardedBot
from dotenv import load_dotenv
import logging

import discord
from discord.ext import commands

from utils import helper

# from discord_slash import SlashCommand

from rich.logging import RichHandler

logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
    handlers=[RichHandler(rich_tracebacks=True)],
)


def setup_guild_db(bot: AutoShardedBot):
    guild_ids = helper.get_guild_ids_json()

    new_guilds = []

    guilds = bot.guilds
    for guild in guilds:
        if guild.id not in guild_ids:
            print(guild.id)
            new_guilds.append(
                {
                    "guild_id": guild.id,
                    "mute_role": None,
                    "logging_channel": None,
                    "prefix": "!",
                }
            )

    helper.insert_guilds(new_guilds)

    return helper.get_guild_ids_json()


class Bot(commands.AutoShardedBot):
    """
    Main Bot
    """

    def __init__(self):
        super().__init__(
            command_prefix="!",
            case_insensitive=True,
            owner_id=389718094270038018,
            reconnect=True,
            intents=discord.Intents.default(),
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="tests."
            ),
        )

        # self.slash = SlashCommand(self)

        self.logger = logging.getLogger(__name__)

        fails = {}
        cogs = [
            "cogs.dev",
            "cogs.errors",
            "cogs.moderation",
            "cogs.setter",
            "cogs.stat",
            "cogs.automod",
        ]
        for cog in cogs:
            try:
                super().load_extension(cog)
                self.logger.info(f"Loading {cog}")

            except Exception as e:
                self.logger.error(f"Unable to load {cog}")
                fails[cog] = e

        if fails == {}:
            self.logger.info("All cogs loaded successfully.")
        else:
            for f in fails:
                self.logger.exception(fails[f])

        self.guild_ids = None

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        helper.insert_guild(guild)
        self.guild_ids = helper.get_guild_ids_json()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        helper.remove_guild(guild.id)
        self.guild_ids = helper.get_guild_ids_json()

    async def on_ready(self):
        self.logger.info("Logged in as:")
        self.logger.info(f"\tBot: {self.user.name}")
        self.logger.info(f"\tID  : {self.user.id}")
        self.logger.info("-" * 30)

        self.guild_ids = setup_guild_db(self)


def main():
    load_dotenv()

    logger = logging.getLogger(__name__)

    logger.info("Starting the bot.")

    Bot().run(os.environ.get("KNIGHT_TOKEN"))


if __name__ == "__main__":
    main()
