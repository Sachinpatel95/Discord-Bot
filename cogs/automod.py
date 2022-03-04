import asyncio
import logging
import re
import threading

import demoji
from better_profanity import profanity
import discord
from discord.ext import commands

# from utils.helper import mod_and_above, helper_and_above
from difflib import SequenceMatcher


def add_to_general(word):
    with open("swearfilters/generalfilter.txt", "a") as f:
        f.write(word)


class Filter(commands.Cog):
    def __init__(self, bot):
        self.logger = logging.getLogger("Automod")
        self.bot = bot

        self.general_list = []
        self.white_list = []
        self.message_history_list = {}
        self.message_history_lock = threading.RLock()
        with open("swearfilters/generalfilter.txt") as f:
            self.general_list = f.read().splitlines()
        with open("swearfilters/whitelist.txt") as f:
            self.white_list = f.read().splitlines()

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("loaded Automod")

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.moderate(message)

    @commands.Cog.listener()
    async def on_message_edit(self, oldMessage, newMessage):
        await self.moderate(newMessage)

    @commands.Cog.listener()
    async def on_message_update(self, oldMessage, newMessage):
        await self.moderate(newMessage)

    async def moderate(self, message):
        event = False
        wordlist = self.general_list
        event = await self.check_message(message, wordlist)
        if not message.author.bot:
            if event[0]:
                if event[1] == "profanity":
                    await message.delete()
                    await message.channel.send(
                        f"Be nice, Don't say bad things {message.author.mention}",
                        delete_after=5,
                    )

                if event[1] == "emoji":
                    await message.delete()
                    await message.channel.send(
                        f"Please do not spam emojis {message.author.mention}",
                        delete_after=5,
                    )

                if event[1] == "text":
                    await message.delete()
                    await message.channel.send(
                        f"Please do not spam {message.author.mention}", delete_after=5
                    )

    def isExcluded(self, author):

        if author.bot:
            return True

        return False

    async def check_message(self, message, word_list):

        # check for profanity
        def check_profanity(word_list, message):
            profanity.load_censor_words(word_list)
            regex_list = self.generate_regex(word_list)
            # stores all words that are aparently profanity
            offending_list = []
            toReturn = False
            # filter out bold and italics but keep *
            message_clean = message.content
            indexes = re.finditer("(\*\*.*\*\*)", message.content)
            if indexes:
                tracker = 0
                for i in indexes:
                    message_clean = message_clean.replace(
                        message_clean[i.start() - tracker : i.end() - tracker],
                        message_clean[i.start() + 2 - tracker : i.end() - 2 - tracker],
                    )
                    tracker = tracker + 4
            indexes = re.finditer(r"(\*.*\*)", message_clean)
            if indexes:
                tracker = 0
                for i in indexes:
                    message_clean = message_clean.replace(
                        message_clean[i.start() - tracker : i.end() - tracker],
                        message_clean[i.start() + 1 - tracker : i.end() - 1 - tracker],
                    )
                    tracker = tracker + 2
            # Chagnes letter emojis to normal ascii ones
            message_clean = self.convert_regional(message_clean)
            # find all question marks in message
            indexes = [x.start() for x in re.finditer(r"\?", message_clean)]
            # get rid of all other non ascii charcters
            message_clean = demoji.replace(message_clean, "*")
            message_clean = (
                str(message_clean)
                .encode("ascii", "replace")
                .decode()
                .lower()
                .replace("?", "*")
            )
            # put back question marks
            message_clean = list(message_clean)
            for i in indexes:
                message_clean[i] = "?"
            message_clean = "".join(message_clean)
            # sub out discord emojis
            message_clean = re.sub(r"(<[A-z]*:[^\s]+:[0-9]*>)", "*", message_clean)
            if profanity.contains_profanity(message_clean):
                return True
            elif profanity.contains_profanity(str(message_clean).replace(" ", "")):
                return True
            else:
                for regex in regex_list:
                    if re.search(regex, message_clean):
                        found_items = re.findall(regex[:-3] + "[A-z]*)", message_clean)
                        for e in found_items:
                            offending_list.append(e)
                        toReturn = True
            if toReturn:
                if self.exception_list_check(offending_list):
                    return toReturn

            return False

        # check for emoji spam
        def check_emoji_spam(message):

            if (
                len(
                    re.findall(
                        r"(<:[^\s]+:[0-9]*>)",
                        re.sub(
                            r"(>[^/s]*<)+",
                            "> <",
                            str(message.content).encode("ascii", "ignore").decode(),
                        ),
                    )
                )
                + len(demoji.findall_list(message.content))
                > 5
            ):
                return True
            return False

        # check for text spam
        def check_text_spam(self, message):

            # if the user has past messages
            if message.author.id in self.message_history_list:
                adv = 0
                count = len(self.message_history_list[message.author.id])
                # atleast 3 prior messages
                if count > 3:
                    for m in self.message_history_list[message.author.id]:
                        adv = (
                            adv
                            + SequenceMatcher(None, m.content, message.content).ratio()
                        )
                    # if the passed x message are similar with a 75% threshold
                    if adv / count > 0.60:
                        return True
            if message.channel.id in self.message_history_list:
                match_count = 0
                # atleast 3 prior messages
                if len(self.message_history_list[message.channel.id]) > 5:
                    for m in self.message_history_list[message.channel.id]:
                        if (
                            SequenceMatcher(None, m.content, message.content).ratio()
                            > 0.75
                        ):
                            match_count = match_count + 1
                        if match_count > 3:
                            return True

        # check for mass ping
        # def check_ping_spam(message):

        # run checks
        if check_profanity(word_list, message):
            return [True, "profanity"]
        if check_emoji_spam(message):
            return [True, "emoji"]

        # this one goes last due to lock
        with self.message_history_lock:
            # if getting past this point we write to message history and pop if to many messages
            if check_text_spam(self, message):
                return [True, "text"]
            if message.author.id in self.message_history_list:
                found = False
                for n in self.message_history_list[message.author.id]:
                    if message.id == n.id:
                        found = True
                        self.message_history_list[message.author.id][
                            self.message_history_list[message.author.id].index(n)
                        ] = message
                if not found:
                    self.message_history_list[message.author.id].append(message)
            else:
                self.message_history_list[message.author.id] = [message]

            if message.channel.id in self.message_history_list:
                found = False
                for n in self.message_history_list[message.channel.id]:
                    if message.id == n.id:
                        found = True
                        self.message_history_list[message.channel.id][
                            self.message_history_list[message.channel.id].index(n)
                        ] = message
                if not found:
                    self.message_history_list[message.channel.id].append(message)
            else:
                self.message_history_list[message.channel.id] = [message]

            # print(f"{message.author.id} {len(self.message_history_list[message.author.id])}")
            # print(f"{message.channel.id} {len(self.message_history_list[message.channel.id])}")

            if len(self.message_history_list[message.author.id]) > 5:
                self.message_history_list[message.author.id].pop()

            if len(self.message_history_list[message.channel.id]) > 10:
                self.message_history_list[message.channel.id].pop()

        return [False, "none"]

    def exception_list_check(self, offending_list):
        for bad_word in offending_list:
            if bad_word in self.white_list:
                continue
            else:
                return True

        return False

    def convert_regional(self, word):
        replacement = {
            "🇦": "a",
            "🇧": "b",
            "🇨": "c",
            "🇩": "d",
            "🇪": "e",
            "🇫": "f",
            "🇬": "g",
            "🇭": "h",
            "🇮": "i",
            "🇯": "j",
            "🇰": "k",
            "🇱": "l",
            "🇲": "m",
            "🇳": "n",
            "🇴": "o",
            "🇵": "p",
            "🇶": "q",
            "🇷": "r",
            "🇸": "s",
            "🇹": "t",
            "🇺": "u",
            "🇻": "v",
            "🇼": "w",
            "🇽": "x",
            "🇾": "y",
            "🇿": "z",
        }

        counter = 0
        to_return = ""
        letter_list = list(word)
        for letter in letter_list:
            if replacement.get(letter) is not None:
                to_return = to_return + replacement.get(letter)
            else:
                to_return = to_return + letter
            counter = counter + 1
        return to_return

    def generate_regex(self, words):
        joining_chars = r'[ _\-\+\.*!@#$%^&():\'"]*'
        replacement = {
            "a": r"a\@\#",
            "b": r"b\*",
            "c": r"c¢\*",
            "d": r"d\*",
            "e": r"e\*",
            "f": r"f\*",
            "g": r"g\*",
            "h": r"h\*",
            "i": r"!1il\*",
            "j": r"!j\*",
            "k": r"k\*",
            "l": r"!1il\*",
            "m": r"m\*",
            "n": r"n\*",
            "o": r"o\*",
            "p": r"pq\*",
            "q": r"qp\*",
            "r": r"r\*",
            "s": r"s$\*",
            "t": r"t\+\*",
            "u": r"uv\*",
            "v": r"vu\*",
            "w": r"w\*",
            "x": r"x\*",
            "y": r"y\*",
            "z": r"z\*",
            " ": r" _\-\+\.*",
        }
        regexlist = []
        for word in words:
            regex_parts = []
            for c in word:
                regex_parts.append(f"[{replacement.get(c)}]")
            regex = r"\b(" + joining_chars.join(regex_parts) + r")\b"
            regexlist.append(regex)
        return regexlist


def setup(bot):
    bot.add_cog(Filter(bot))
