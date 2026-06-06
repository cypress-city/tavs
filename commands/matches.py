import asyncio
import discord
from discord.ext import commands
from math import ceil
import time

from modules.core import Bot, Player, prettify_time
from modules.course import course_autocomplete, COURSES
from modules.match import Match, QUICKPLAY_RULESET
from modules.ui import error, ChallengeView, construct_embed, YELLOW, RED, ReadyView, RoundView, RoundOverView


class MatchCog(commands.Cog):
    def __init__(self, bot: Bot):
        super().__init__()
        self.bot = bot

    async def run_match(self, match: Match, message: discord.Message = None):
        p1 = match.p1
        p2 = match.p2
        ready_view = ReadyView(p1, p2)
        if message is None:
            message = await match.channel.send(embed=match.ready_embed(), view=ready_view)
        else:
            await message.edit(embed=match.ready_embed(), view=ready_view)
        while not ((p1.ready and p2.ready) or p1.quit or p2.quit or await ready_view.wait()):
            ready_view = ReadyView(p1, p2)
            await message.edit(embed=match.ready_embed(), view=ready_view)
        if p1.quit or p2.quit:
            return await message.edit(embed=construct_embed(title="Match cancelled.", color=RED), view=None)
        if not (p1.ready and p2.ready):
            return await message.edit(embed=construct_embed(title="Match timed out.", color=RED), view=None)

        await message.edit(embed=construct_embed(
            title="Match starting!",
            desc="**You may now start a Time Trial.** The round timer will start in 10 seconds. Good luck!",
            color=YELLOW
        ), view=None)
        await asyncio.sleep(10)

        round_view = RoundView(p1, p2, timeout=10)
        match.start_round()
        round_message = await inter.channel.send(embed=match.round_embed(), view=round_view)
        warning_message = None
        warning_sent = False
        while match.time_remaining() and not (p1.quit or p2.quit):
            await round_view.wait()
            round_view = RoundView(p1, p2, timeout=10)
            await round_message.edit(embed=match.round_embed(), view=round_view)
            if match.time_remaining() < 130 and not warning_sent:
                warning_message = await inter.channel.send(embed=construct_embed(title="2 minute warning!", color=RED))
                warning_sent = True

        if warning_message is not None:
            await warning_message.delete()
        await round_message.edit(embed=match.round_embed(), view=None)
        round_over_view = RoundOverView(p1, p2, timeout=180)
        ending_message = await inter.channel.send(embed=match.round_ending_embed(), view=round_over_view)
        ending_time = time.time() + 180
        while not ((p1.finished and p2.finished) or await round_over_view.wait()):
            round_over_view = RoundOverView(p1, p2, timeout=ceil(ending_time - time.time()))
            await ending_message.edit(
                embed=match.round_ending_embed(),
                view=(None if p1.finished and p2.finished else round_over_view)
            )

        if p1.time == p2.time:
            return await inter.channel.send(embed=construct_embed(
                title="It's a tie!",
                desc="Because no one finished a run!" if p1.time == 0 else None,
                color=YELLOW
            ))
        winner = p1 if p1.time == match.winning_time() else p2
        return await inter.channel.send(embed=construct_embed(
            title=f"{winner.discord.name} wins!!", color=YELLOW
        ))

    @discord.app_commands.command(
        name="quickplay",
        description="Create a quickplay match."
    )
    @discord.app_commands.autocomplete(
        course=course_autocomplete
    )
    async def quickplay_command(self, inter: discord.Interaction, opponent: discord.User, course: str):
        if opponent.bot:
            return await inter.response.send_message("You can't challenge bot users.", ephemeral=True)
        if not (course := COURSES.get(course)):
            return await inter.response.send_message(
                f"Course not found. Please select from the list in the command menu.", ephemeral=True
            )

        challenge_view = ChallengeView(inter.user, opponent)
        message = await inter.response.send_message(embed=construct_embed(
            title="Quickplay Challenge",
            desc=f"{inter.user.mention} has challenged {opponent.mention} to a 15-minute match on **{course.name}**. "
                 f"Do you accept?",
            color=YELLOW
        ), view=challenge_view)
        message = message.resource
        await challenge_view.wait()
        if challenge_view.status != "accepted":
            return await message.edit(embed=construct_embed(title=f"Match {challenge_view.status}.", color=RED), view=None)

        p1 = Player(inter.user)
        p2 = Player(opponent)
        return await self.run_match(
            Match(p1, p2, inter.channel, QUICKPLAY_RULESET, set_track=course),
            message=message
        )


async def setup(bot: Bot):
    await bot.add_cog(MatchCog(bot))
