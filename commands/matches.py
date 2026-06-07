import asyncio
import discord
from discord.ext import commands
from math import ceil
import time

from modules.core import Bot, Player
from modules.course import course_autocomplete, COURSES
from modules.match import Match, QUICKPLAY_RULESET, INVITATIONAL_RULESET
from modules.ui import ChallengeView, construct_embed, YELLOW, RED, ReadyView, RoundView, RoundOverView, \
    StartClockView


class MatchCog(commands.Cog):
    def __init__(self, bot: Bot):
        super().__init__()
        self.bot = bot

    async def run_match(self, match: Match, message: discord.Message = None, **kwargs):
        p1 = match.p1
        p2 = match.p2
        ready_view = ReadyView(p1, p2)
        if message is None:
            if inter := kwargs.get("inter"):
                response = await inter.response.send_message(embed=match.ready_embed(), view=ready_view)
                message = response.resource
            else:
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

        if match.ruleset.wait_for_admin:
            clock_view = StartClockView([match.creator], timeout=600)
            await message.edit(embed=match.start_clock_embed(), view=clock_view)
            await clock_view.wait()
            if clock_view.value is None:
                return await message.edit(embed=construct_embed(title="Match timed out.", color=RED), view=None)
            if not clock_view.value:
                return await message.edit(embed=construct_embed(title="Match cancelled.", color=RED), view=None)

        await message.edit(embed=construct_embed(
            title="Match starting!",
            desc="**You may now start a Time Trial.** The round timer will start in 10 seconds. Good luck!",
            color=YELLOW
        ), view=None)
        await asyncio.sleep(10)

        round_view = RoundView(p1, p2, embed_generator=match.round_embed)
        match.start_round()
        round_message = await match.channel.send(embed=match.round_embed(), view=round_view)
        round_view.message = round_message
        warning_message = None
        warning_sent = False
        while match.time_remaining() and not (p1.quit or p2.quit):
            await round_view.wait()
            round_view = RoundView(p1, p2, message=round_message, embed_generator=match.round_embed)
            await round_message.edit(embed=match.round_embed(), view=round_view)
            if match.time_remaining() < 130 and not warning_sent:
                warning_message = await match.channel.send(embed=construct_embed(title="2 minute warning!", color=RED))
                warning_sent = True

        if warning_message is not None:
            await warning_message.delete()
        await round_message.edit(embed=match.round_embed(), view=None)
        round_over_view = RoundOverView(p1, p2, embed_generator=match.round_ending_embed)
        ending_message = await match.channel.send(embed=match.round_ending_embed(), view=round_over_view)
        round_over_view.message = ending_message
        ending_time = time.time() + round_over_view.timeout
        while not ((p1.finished and p2.finished) or await round_over_view.wait()):
            round_over_view = RoundOverView(
                p1, p2, message=ending_message, embed_generator=match.round_ending_embed,
                timeout=ceil(ending_time - time.time())
            )
            await ending_message.edit(
                embed=match.round_ending_embed(),
                view=(None if p1.finished and p2.finished else round_over_view)
            )

        if p1.time == p2.time:
            return await match.channel.send(embed=construct_embed(
                title="It's a tie!",
                desc="Because no one finished a run!" if p1.time == 0 else None,
                color=YELLOW
            ))
        winner = p1 if p1.time == match.winning_time() else p2
        return await match.channel.send(embed=construct_embed(
            title=f"{winner.discord.display_name} wins!!", color=YELLOW
        ))

    @discord.app_commands.command(
        name="quickplay",
        description="Challenge an opponent to a quickplay match."
    )
    @discord.app_commands.autocomplete(
        course=course_autocomplete
    )
    async def quickplay_command(self, inter: discord.Interaction, opponent: discord.User, course: str):
        if opponent.bot:
            return await inter.response.send_message("You can't challenge bot users.", ephemeral=True)
        if opponent == inter.user:
            return await inter.response.send_message("You can't challenge yourself.", ephemeral=True)
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

    @discord.app_commands.command(
        name="invitational",
        description="Create an invitational match between two players."
    )
    @discord.app_commands.autocomplete(
        course=course_autocomplete
    )
    async def invitational_match(self, inter: discord.Interaction, p1: discord.User, p2: discord.User, course: str):
        if not inter.user.guild_permissions.administrator:
            return await inter.response.send_message("Only admins may use this command.", ephemeral=True)
        if p1.bot or p2.bot or (p1 == p2):
            return await inter.response.send_message("Invalid participants.", ephemeral=True)
        if not (course := COURSES.get(course)):
            return await inter.response.send_message(
                f"Course not found. Please select from the list in the command menu.", ephemeral=True
            )

        return await self.run_match(
            Match(Player(p1), Player(p2), inter.channel, INVITATIONAL_RULESET, set_track=course),
            inter=inter
        )


async def setup(bot: Bot):
    await bot.add_cog(MatchCog(bot))
