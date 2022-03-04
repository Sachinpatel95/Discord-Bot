from datetime import datetime
import logging
from typing import Dict, List

import discord
from pymongo import errors

from utils.database import guilds_db

logger = logging.getLogger("Helper util")

### Embed
def create_embed(
    title: str,
    description: str,
    fields: list = [],
    color: discord.Colour = discord.Color.default(),
) -> discord.Embed:
    """Create a basic embed with title, description, and color

    Args:
        title (str): embed title
        description (str): embed description
        fields (list, optional): list of embed fields with {"name": _, "value": _}. Defaults to [].
        color (discord.Colour, optional): Color of the embed. Defaults to discord.Color.default().

    Returns:
        discord.Embed
    """
    embed = discord.Embed(
        title=title, description=description, color=color, timestamp=datetime.utcnow()
    )

    for field in fields:
        embed.add_field(name=field["name"], value=field["value"], inline=False)

    return embed


### Database
def get_guild_ids_json():
    """Get ids of all guilds"""
    res = guilds_db.find({}, {"guild_id": 1})
    return {r["guild_id"] for r in res}


def insert_guild(guild: discord.Guild):
    """Insert info for single guild"""
    try:
        guilds_db.insert_one(
            {
                "guild_id": guild.id,
                "mute_role": None,
                "logging_channel": None,
                "prefix": "!",
            }
        )
    except errors.DuplicateKeyError:
        pass


def insert_guilds(guilds: List[Dict]):
    """Insert info for multiple guilds"""
    try:
        if guilds != []:
            guilds_db.insert_many(guilds)
    except errors.DuplicateKeyError:
        pass


def remove_guild(id: int):
    """Remove a single guild"""
    guilds_db.delete_one({"guild_id": id})


### Logging
def get_logging_channel(guild: discord.Guild) -> discord.TextChannel:
    lc_id = guilds_db.find_one({"guild_id": guild.id})["logging_channel"]
    return discord.utils.get(guild.text_channels, id=lc_id)


def set_logging_channel(guild: discord.Guild, channel: discord.TextChannel):
    guilds_db.update_one(
        {"guild_id": guild.id}, {"$set": {"logging_channel": channel.id}}
    )


### Mute
def get_mute_role(guild: discord.Guild) -> discord.Role:
    mute_id = guilds_db.find_one({"guild_id": guild.id})["mute_role"]
    return discord.utils.get(guild.roles, id=mute_id)


def set_mute_role(guild: discord.Guild, role: discord.Role):
    guilds_db.update_one({"guild_id": guild.id}, {"$set": {"mute_role": role.id}})
