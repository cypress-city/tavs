import discord
import random

from modules.core import closeness


class Course:
    def __init__(self, abbreviation: str, name: str):
        self.abbreviation = abbreviation
        self.name = name

    def __eq__(self, other):
        if isinstance(other, str):
            return other == self.abbreviation or other == self.name
        elif isinstance(other, Course):
            return self.abbreviation == other.abbreviation and self.name == other.name
        return False

    def __str__(self):
        return f"[{self.abbreviation}] {self.name}"

    def closeness(self, user_input: str):
        term = user_input.lower()
        return closeness(term, self.abbreviation.lower()) * 8 + closeness(term, self.name.lower())


COURSES = {
    "MBC": Course("MBC", "Mario Bros. Circuit"),
    "CC": Course("CC", "Crown City"),
    "WS": Course("WS", "Whistlestop Summit"),
    "DKS": Course("DKS", "DK Spaceport"),
    "rDH": Course("rDH", "Desert Hills"),
    "rSGB": Course("rSGB", "Shy Guy Bazaar"),
    "rWS": Course("rWS", "Wario Stadium"),
    "rAF": Course("rAF", "Airship Fortress"),
    "rDKP": Course("rDKP", "DK Pass"),
    "SP": Course("SP", "Starview Peak"),
    "rSHS": Course("rSHS", "Sky-High Sundae"),
    "rWSh": Course("rWSh", "Wario Shipyard"),
    "rKTB": Course("rKTB", "Koopa Troopa Beach"),
    "FO": Course("FO", "Faraway Oasis"),
    "PS": Course("PS", "Peach Stadium"),
    "rPB": Course("rPB", "Peach Beach"),
    "SSS": Course("SSS", "Salty Salty Speedway"),
    "rDDJ": Course("rDDJ", "Dino Dino Jungle"),
    "GBR": Course("GBR", "Great ? Block Ruins"),
    "CCF": Course("CCF", "Cheep Cheep Falls"),
    "DD": Course("DD", "Dandelion Depths"),
    "BCi": Course("BCi", "Boo Cinema"),
    "DBB": Course("DBB", "Dry Bones Burnout"),
    "rMMM": Course("rMMM", "Moo Moo Meadows"),
    "rCM": Course("rCM", "Choco Mountain"),
    "rTF": Course("rTF", "Toad's Factory"),
    "BC": Course("BC", "Bowser's Castle"),
    "AH": Course("AH", "Acorn Heights"),
    "rMC": Course("rMC", "Mario Circuit"),
    "RR": Course("RR", "Rainbow Road")
}


async def course_autocomplete(inter: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    matches = sorted([g for g in COURSES.values() if g.closeness(current)], key=lambda c: -c.closeness(current))
    return [discord.app_commands.Choice(name=str(g), value=g.abbreviation) for g in matches][:25]


class CourseSelection:
    def __init__(self, course_pool: list[Course]):
        self._course_pool = {g.abbreviation: True for g in course_pool}

    @staticmethod
    def random(n: int):
        return CourseSelection(random.sample(list(COURSES.values()), k=n))

    @property
    def available_courses(self) -> list[Course]:
        return [COURSES[k] for k, v in self._course_pool.items() if v]

    @property
    def banned_courses(self) -> list[Course]:
        return [COURSES[k] for k, v in self._course_pool.items() if not v]

    def ban(self, course: str | Course):
        if isinstance(course, Course):
            course = course.abbreviation
        if course in self._course_pool:
            self._course_pool[course] = False


DEFAULT_POOL = CourseSelection(list(COURSES.values()))
