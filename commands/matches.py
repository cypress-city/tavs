import discord
from discord.ext import commands

from modules.core import Bot
from modules.match import Match


class MatchCog(commands.Cog):
    def __init__(self, bot: Bot):
        super().__init__()
        self.bot = bot

    @discord.app_commands.command(
        name="c",
        description="Create a match."
    )
    async def sample_command(self, inter: discord.Interaction, opponent: discord.User):
        match = Match(inter.user, opponent, inter.channel)
        return await inter.response.send_message(f"Test match created with {opponent.mention}.")


async def setup(bot: Bot):
    await bot.add_cog(MatchCog(bot))
