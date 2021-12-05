import discord
from discord import client
from discord.ext import tasks, commands

from datetime import datetime, timedelta
import json

class Tasks(commands.Cog):
    def __init__(self, bot):
        print("init tasks")
        self.bot = bot
        self.auto_delete.start()
        self.reminders.start()
        

    @tasks.loop(minutes=10)
    async def auto_delete(self):
        _, cursor = self.bot.get_cog("Connector").get()
        cursor.execute("SELECT autodelete FROM discord.guilds")

        channels = []
        for data in cursor.fetchall():
            if data != None and len(data) > 0 and data[0] != None:
                channels.extend(json.loads(data[0]))

        today = datetime.utcnow()

        def ignore(m):
            return not m.pinned and ((today - m.created_at).seconds/3600) >= 2
        
        for channel in channels:
            channel = self.bot.get_channel(channel)
            if channel != None:
                await channel.purge(check=ignore)

    
    @tasks.loop(seconds=30)    
    async def reminders(self):
        cnx, cursor = self.bot.get_cog("Connector").get()
        now_ts = (datetime.now() - timedelta(hours=4))
        now_ts = now_ts.timestamp()
        cursor.execute(f"""SELECT reminder_id, member_id, channel_id, message, time FROM discord.reminders WHERE time <= {int(now_ts)}""") # 
        todo = cursor.fetchall()
        if len(todo) > 0:
            ids = []
            for reminder in todo:
                ids.append(f"'{reminder[0]}'")

                channel = self.bot.get_channel(reminder[2])
                if channel != None:
                    await channel.send(f"{reminder[3]}")

            ids = ",".join(ids)
            cursor.execute(f"DELETE FROM discord.reminders WHERE reminder_id IN ({ids})")
            cnx.commit()