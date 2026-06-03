import discord
from discord.ext import commands
import re


_COGS = [
    "commands.admin",
    "commands.matches"
]


def closeness(search_term: str, match: str) -> int:
    return 4 if match == search_term else 2 if match.startswith(search_term) else 1 if search_term in match else 0


def prettify_seconds(seconds: float, include_ms: bool = True) -> str:
    return f"{int(abs(seconds))}" + \
        (f".{str(round((abs(seconds) % 1) * 1000)).rjust(3, '0')}" if include_ms else "")


def prettify_time(time: float, include_hour: bool = False, include_ms: bool = True) -> str:
    if not (rounded := round(time, 3)):
        return ("-:-" if include_hour else "") + "-:--" + (".---" if include_ms else "")
    return (f"{int(rounded // 3600)}:" if include_hour else "") + \
        f"{str(int((rounded % 3600) // 60)).rjust(2, '0') if include_hour else int(rounded // 60)}:" \
        f"{prettify_seconds(rounded % 60, include_ms=include_ms).rjust(6 if include_ms else 2, '0')}"


def unprettify_time(text: str) -> float:
    if not (match := re.fullmatch(
            r"(?P<min>[0-9]+)[:'.](?P<sec>[0-9]{1,2})[.\"](?P<mil>[0-9]{1,4})",
            text.strip('"')
    )):
        raise ValueError(f"Cannot interpret string as time: {text}")
    return round(int(match["min"]) * 60 + int(match["sec"]) + int(match["mil"]) / 1000, 3)


class Player:
    def __init__(self, discord_user: discord.User | discord.Member):
        self.discord = discord_user
        self.ready = False
        self.time = 0.0
        self.finished = False
        self.quit = False

    def __eq__(self, other):
        if isinstance(other, Player):
            return self.discord == other.discord
        return self.discord == other

    def reset(self):
        self.ready = False
        self.time = 0.0
        self.finished = False


class Bot(commands.Bot):  # main bot class
    def __init__(self, owner_id: int = None):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(
            intents=intents, command_prefix="!",
            allowed_contexts=discord.app_commands.AppCommandContext(guild=True, dm_channel=True, private_channel=True),
            allowed_installs=discord.app_commands.AppInstallationType(guild=True, user=True)
        )

        if owner_id:
            self.owner_id = owner_id

    async def setup_hook(self) -> None:
        for extension in _COGS:
            await self.load_extension(extension)
