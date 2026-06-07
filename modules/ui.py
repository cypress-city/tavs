import discord

from modules.core import Player, unprettify_time


RED = discord.Colour.from_rgb(224, 16, 32)
YELLOW = discord.Colour.from_rgb(255, 224, 0)


def timing_gradient(progress: float) -> discord.Colour:
    return discord.Colour.from_hsv(0.35 * progress, 0.95, 0.95)


def construct_embed(**kwargs) -> discord.Embed:
    ret = discord.Embed(
        title=kwargs.get("title"),
        description=kwargs.get("desc"),
        color=kwargs.get("color"),
        url=kwargs.get("url")
    )
    ret.set_thumbnail(url=kwargs.get("thumb"))
    ret.set_footer(text=kwargs.get("footer"))
    return ret


def error(**kwargs) -> discord.Embed:
    return construct_embed(color=RED, **kwargs)


class TimeModal(discord.ui.Modal, title="Submit time"):
    time = discord.ui.TextInput(label="Time", placeholder="1:23.456", min_length=8, max_length=8)

    def __init__(self, callback):
        super().__init__()
        self._callback = callback

    async def on_submit(self, inter: discord.Interaction):
        await self._callback(inter, self.time.value)


class QuitModal(discord.ui.Modal, title="Are you sure?"):
    warning = discord.ui.TextDisplay("Are you sure you want to quit and end the match early? If so, press Submit.")

    def __init__(self, callback):
        super().__init__()
        self._callback = callback

    async def on_submit(self, inter: discord.Interaction):
        await self._callback(inter)


class LimitedUserView(discord.ui.View):
    def __init__(self, users: list[discord.User], timeout: int = 180):
        super().__init__(timeout=timeout)
        self.allowed_users = users

    async def interaction_check(self, inter: discord.Interaction, /) -> bool:
        if inter.user in self.allowed_users:
            return True
        await inter.response.defer()
        return False


class ChallengeView(LimitedUserView):
    def __init__(self, challenger: discord.User, challengee: discord.User):
        super().__init__(users=[challenger, challengee])
        self.sender = challenger
        self.recipient = challengee
        self.status = "sent"

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, inter: discord.Interaction, button: discord.ui.Button):
        await inter.response.defer()
        if inter.user == self.recipient:
            self.status = "accepted"
            self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline(self, inter: discord.Interaction, button: discord.ui.Button):
        await inter.response.defer()
        if inter.user == self.recipient:
            self.status = "declined"
            self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, inter: discord.Interaction, button: discord.ui.Button):
        await inter.response.defer()
        self.status = "cancelled"
        self.stop()

    def on_timeout(self) -> None:
        self.status = "timed out"


class StartClockView(LimitedUserView):
    value = None

    @discord.ui.button(label="Start", style=discord.ButtonStyle.green)
    async def start_clock(self, inter: discord.Interaction, button: discord.ui.Button):
        await inter.response.defer()
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, inter: discord.Interaction, button: discord.ui.Button):
        await inter.response.defer()
        self.value = False
        self.stop()


class MatchView(LimitedUserView):
    _timeout: int = 180

    def __init__(self, player1: Player, player2: Player, **kwargs):
        super().__init__([player1.discord, player2.discord], timeout=kwargs.get("timeout", self._timeout))
        self.player1 = player1
        self.player2 = player2

    def matching_player(self, player: Player | discord.User):
        return self.player1 if self.player1 == player else self.player2 if self.player2 == player else None


class ReadyView(MatchView):
    _timeout = 120

    @discord.ui.button(label="Ready", style=discord.ButtonStyle.green)
    async def ready(self, inter: discord.Interaction, button: discord.ui.Button):
        await inter.response.defer()
        if player := self.matching_player(inter.user):
            player.ready = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, inter: discord.Interaction, button: discord.ui.Button):
        await inter.response.defer()
        if player := self.matching_player(inter.user):
            player.quit = True
        self.stop()


class RoundViewBase(MatchView):
    _timeout = 10

    def __init__(self, p1: Player, p2: Player, **kwargs):
        super().__init__(p1, p2, **kwargs)
        self.message: discord.Message = kwargs.get("message", None)
        self.embed_generator = kwargs.get("embed_generator", None)

    async def submit(self, inter: discord.Interaction):
        async def callback(modal_inter: discord.Interaction, value: str):
            if player := self.matching_player(inter.user):
                try:
                    player.time = unprettify_time(value)
                except ValueError:
                    return await modal_inter.response.send_message("Bad formatting. Times should look like `1:23.456`", ephemeral=True)
            await modal_inter.response.defer()
            if self.message and self.embed_generator:
                await self.message.edit(embed=self.embed_generator())

        await inter.response.send_modal(TimeModal(callback))
        self.stop()

    @discord.ui.button(label="Submit time", style=discord.ButtonStyle.green)
    async def submit_button(self, inter: discord.Interaction, button: discord.ui.Button):
        await self.submit(inter)


class RoundView(RoundViewBase):
    quit = False

    @discord.ui.button(label="Quit match", style=discord.ButtonStyle.grey)
    async def quit(self, inter: discord.Interaction, button: discord.ui.Button):
        async def callback(modal_inter: discord.Interaction):
            if player := self.matching_player(inter.user):
                player.quit = True
            await modal_inter.response.send_message(embed=construct_embed(title=f"{inter.user.name} has quit. Ending..."))

        await inter.response.send_modal(QuitModal(callback))
        self.stop()


class RoundOverView(RoundViewBase):
    _timeout = 180

    @discord.ui.button(label="Update time", style=discord.ButtonStyle.grey)
    async def submit_button(self, inter: discord.Interaction, button: discord.ui.Button):
        await self.submit(inter)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def finish(self, inter: discord.Interaction, button: discord.ui.Button):
        await inter.response.defer()
        if player := self.matching_player(inter.user):
            player.finished = True
        self.stop()
