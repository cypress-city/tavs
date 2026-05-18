import discord
from discord.ext import commands


_COGS = [
    "commands.admin",
    "commands.matches"
]


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
