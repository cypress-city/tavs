import discord
import time

from modules.core import Player, prettify_time
from modules.course import Course, CourseSelection, DEFAULT_POOL
from modules.ui import construct_embed, RoundView, YELLOW, RED


class Ruleset:
    def __init__(self, **kwargs):
        self.name: str = kwargs.get("name", "TAVS")
        self.rounds: int = kwargs.get("rounds", 1)
        self.round_time: int = kwargs.get("round_time", 900)  # in seconds
        self.random_selection: int = kwargs.get("random_selection", 0)  # number of tracks to select from, 0 for no limit
        self.ban_order: list[int] = kwargs.get("ban_order", [])  # 0 = player1, 1 = player2, empty for no bans
        self.picks_first: int = kwargs.get("picks_first", 1)  # same as above
        self.set_track: bool = kwargs.get("set_track", False)


QUICKPLAY_RULESET = Ruleset(
    name="Quickplay",
    rounds=1,
    round_time=900,
    random_selection=0,
    ban_order=[],
    picks_first=0,
    set_track=True
)
TOURNAMENT_RULESET = Ruleset(
    name="Tournament",
    rounds=3,
    round_time=900,
    random_selection=0,
    ban_order=[0, 1, 1, 0],
    picks_first=1,
    set_track=False
)


class Match:
    def __init__(self, p1: Player, p2: Player, channel: discord.TextChannel, ruleset: Ruleset, **kwargs):
        self.player1 = p1
        self.player2 = p2
        self.channel = channel
        self.ruleset = ruleset
        if self.ruleset.random_selection:
            self.course_pool = CourseSelection.random(self.ruleset.random_selection)
        else:
            self.course_pool = DEFAULT_POOL

        self.phase = "ready"
        self.bans_completed = 0
        self.current_track: Course | None = kwargs.get("set_track")
        self.rounds_completed = 0
        self.round_view = RoundView(p1, p2)
        self.round_start_time = 0
        self.previous_loser = 0

    @property
    def players(self):
        return [self.player1, self.player2]

    def next_player_to_act(self):
        if self.rounds_completed:
            return self.players[self.previous_loser]
        elif self.ruleset.ban_order:
            if self.bans_completed < len(self.ruleset.ban_order):
                return self.players[self.ruleset.ban_order[self.bans_completed]]
            else:
                return self.players[self.ruleset.picks_first]
        else:
            return self.player1

    def round_end_time(self):
        return self.round_start_time + self.ruleset.round_time

    def time_remaining(self):
        return min(max(self.round_end_time() - time.time(), 0), self.ruleset.round_time)

    def winning_time(self):
        try:
            return min([g for g in [self.player1.time, self.player2.time] if g])
        except ValueError:
            return -1

    def start_round(self):
        self.round_start_time = time.time()
        self.player1.reset()
        self.player2.reset()

    def ready_embed(self):
        return construct_embed(
            title=f"{self.ruleset.name} Match",
            desc=(f"**{self.current_track.name}**\n\n" if self.current_track else "") +
                 "Select your combo and course, but do not start a Time Trial yet. "
                 "The match will begin after both players press the Ready button.\n\n"
                 f"{self.player1.discord.mention}: {'✅' if self.player1.ready else '...'}\n"
                 f"{self.player2.discord.mention}: {'✅' if self.player2.ready else '...'}\n",
            color=YELLOW
        )

    def course_select_embed(self):
        if self.course_pool.banned_courses:
            desc = "**Banned:**\n" + ("\n".join(str(g) for g in self.course_pool.banned_courses)) + "\n\n"
        else:
            desc = ""
        if self.ruleset.random_selection:
            desc += "**Remaining:**\n" + ("\n".join(str(g) for g in self.course_pool.available_courses)) + "\n\n"

        desc += (f"**{self.next_player_to_act().discord.mention}**, press the button to select a track to "
                 f"{'play' if self.bans_completed >= len(self.ruleset.ban_order) else '**ban**'}.")

        return construct_embed(
            title="Course Selection", desc=desc, color=YELLOW
        )

    def round_embed(self):
        return construct_embed(
            title=f"{self.ruleset.name} Match",
            desc=f"**{self.current_track.name}**\n"
                 f"Round time: **{prettify_time(self.time_remaining(), include_ms=False)}**\n\n"
                 f"{self.player1.discord.mention} — `{prettify_time(self.player1.time)}`"
                 f"{' 👑' if self.winning_time() == self.player1.time else ''}\n"
                 f"{self.player2.discord.mention} — `{prettify_time(self.player2.time)}`"
                 f"{' 👑' if self.winning_time() == self.player2.time else ''}",
            color=YELLOW
        )

    def round_ending_embed(self):
        return construct_embed(
            title="Round over!",
            desc="**You may finish your current run.** You have 3 minutes to submit your final time.\n\n"
                 "Press \"Finish\" when you're done, or if you don't have a new time to submit.\n\n"
                 f"{self.player1.discord.mention}: `{prettify_time(self.player1.time)}` "
                 f"{'✅' if self.player1.finished else '❓'}\n"
                 f"{self.player2.discord.mention}: `{prettify_time(self.player2.time)}` "
                 f"{'✅' if self.player2.finished else '❓'}",
            color=RED
        )
