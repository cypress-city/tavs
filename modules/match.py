import discord

from modules.course import Course, CourseSelection, DEFAULT_POOL


class Match:
    def __init__(self, p1: discord.User, p2: discord.User, channel: discord.TextChannel,
                 course_pool: CourseSelection = DEFAULT_POOL):
        self.player1 = p1
        self.player2 = p2
        self.channel = channel
        self.course_pool = course_pool
