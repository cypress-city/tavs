import discord
from discord.ext import commands

from modules.core import Bot


class AdminCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name="close", aliases=["stop"], hidden=True)
    async def close_command(self, ctx: commands.Context):
        if ctx.author.id == self.bot.owner_id:
            await ctx.send("😴 Stopping bot.")
            await self.bot.close()

    @commands.command(name="sync", hidden=True)
    async def sync_command(self, ctx: commands.Context):
        if ctx.author.id == self.bot.owner_id:
            await self.bot.tree.sync()
            return await ctx.send("✅ Command tree re-synced.")


async def setup(bot: Bot):
    await bot.add_cog(AdminCog(bot))
