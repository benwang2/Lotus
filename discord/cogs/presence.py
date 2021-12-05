import discord, random
from discord import client
from discord.ext import tasks, commands

activities = [
    'Live, laugh, love.',
    'Be somebody who makes everybody feel like somebody.',
    'Be a pineapple. Stand tall, wear a crown, and be sweet on the inside.',
    'Do what you love. Love what you do ❤',
    'Less is more.',
    'From small beginnings come great things.',
    'Teach, love, inspire.',
    'Love builds a happy home.',
    'Home is where you are.',
    'One tough mother.',
    'Glam-ma!', 
    'Sweater weather.',
    'Pour some sugar on me.',
    'Wash, brush, floss, flush.',
    'Follow your heart.',
    'Full of happy.',
    'What happens in the bathroom... stays in the bathroom.',
    'Dome sweet dome.',
    'Never dunn.',
    'I\'m not lazy, I\'m in energy saving mode.',
    'In a world where you can be anything, be kind.',
    'Worry less, pray more.'
]

class Presence(commands.Cog):
    def __init__(self, bot):
        print("init presence")
        self.index = random.randrange(0, len(activities))
        self.bot = bot
        self.setPresence.start()

    async def cog_unload(self):
        self.setPresence.cancel()

    @tasks.loop(seconds=60*5)
    async def setPresence(self):
        self.index += 1
        if (self.index>=len(activities)):
            self.index = 0
        await self.bot.change_presence(activity=discord.Game(activities[self.index]+""))