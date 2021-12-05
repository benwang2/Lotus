from discord import client
from discord.ext import tasks, commands

from datetime import datetime as date

class Tracking(commands.Cog):
    def __init__(self, bot):
        print("init tracking")
        self.bot = bot

    def is_registered(self, member):
        guild_id, member_id = member.guild.id, member.id
        cnx, cursor = self.bot.get_cog("Connector").get()

        cursor.execute("SELECT username FROM discord.users WHERE guild_id = %s AND member_id = %s", (guild_id, member_id))
        return cursor.fetchone() != None

    def register(self, member):
        if member.bot: return
        
        guild_id, member_id, username = member.guild.id, member.id, member.name
        cnx, cursor = self.bot.get_cog("Connector").get()
        #cursor.execute("INSERT INTO discord.users(guild_id, member_id) VALUES (%s, %s)", (member.guild.id, member.id))
        pfp = None if member.avatar == None else f"https://cdn.discordapp.com/avatars/{member.id}/{member.avatar}.webp"
        cursor.execute("""
                            INSERT INTO discord.users (guild_id, member_id, username, pfp)
                            SELECT * FROM (SELECT %s, %s, %s, %s) AS tmp
                            WHERE NOT EXISTS (
                                SELECT guild_id, member_id from discord.users WHERE guild_id = %s AND member_id = %s
                            )
                            LIMIT 1;
                        """, (guild_id, member_id, username, pfp, guild_id, member_id))
        cnx.commit()

        # Insert a new user entry if it doesn't exist already.
    
    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        if after.name != before.name or after.avatar != before.avatar:
            cnx, cursor = self.bot.get_cog("Connector").get()
            pfp = None if after.avatar == None else f"https://cdn.discordapp.com/avatars/{after.id}/{after.avatar}.webp"
            cursor.execute("""
                UPDATE discord.users
                SET username = %s, pfp = %s
                WHERE member_id = %s""", (after.name, pfp, after.id)
            )
            cnx.commit()

    """ Members are eligible to receive a point reward every minute.
            ____________________
           |Activity |  Value   |
           |Text     |  1 pts   |
           |Voice    |  1 pts   |
           |Stream   |  1 pts   |
            ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
    """

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot: return
        if not self.is_registered(member):
            self.register(member)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        print(f"Joined {guild.name}")
        cnx, cursor = self.bot.get_cog("Connector").get()

        icon_url = None if guild.icon == None else f"https://cdn.discordapp.com/icons/{guild.id}/{guild.icon}.webp"
        cursor.execute("""
                            INSERT INTO discord.guilds (guild_id, name, icon, members, created)
                            SELECT * FROM (SELECT %s, %s, %s, %s, %s) AS tmp
                            WHERE NOT EXISTS (
                                SELECT guild_id from discord.guilds WHERE guild_id = %s
                            )
                            LIMIT 1;
                        """, (guild.id, guild.name, icon_url, guild.member_count, guild.created_at, guild.id))
        cnx.commit()

    @commands.Cog.listener()
    async def on_guild_update(self, _, after):
        cnx, cursor = self.bot.get_cog("Connector").get()

        icon_url = None if after.icon == None else f"https://cdn.discordapp.com/icons/{after.id}/{after.icon}.webp"

        cursor.execute("""
                            UPDATE discord.guilds
                            SET
                                name = %s,
                                icon = %s,
                                members = %s
                            WHERE guild_id = %s
                        """, (after.name, icon_url, after.member_count, after.id))
        cnx.commit()
        
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        if message.guild == None: return

        guild_id, member_id = message.guild.id, message.author.id

        if not self.is_registered(message.author): self.register(message.author)

        cnx, cursor = self.bot.get_cog("Connector").get()
        
        
        cursor.execute("SELECT last_message FROM discord.users WHERE guild_id = %s AND member_id = %s", (guild_id, member_id))
        
        last_message = cursor.fetchone()

        if (
            last_message == None or
            last_message[0] == None or
            (last_message[0] != None and len(last_message) > 0 and (message.created_at - date.fromtimestamp(last_message[0])).seconds >= 1)
            ):
            cursor.execute("""
                            UPDATE
                                discord.users
                            SET
                                last_message = %s,
                                text = text + 1,
                                points = points + 1
                            WHERE
                                guild_id = %s
                            AND
                                member_id = %s""",
                            (int(message.created_at.timestamp()), guild_id, member_id)
            )

            cnx.commit()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot: pass

        guild_id, member_id = member.guild.id, member.id

        if not self.is_registered(member): self.register(member)

        cnx, cursor = self.bot.get_cog("Connector").get()

        if before.channel != after.channel:
            if after.channel != None: # User is joining VC
                cursor.execute("UPDATE discord.users SET joined_vc = %s WHERE guild_id = %s AND member_id = %s",(date.utcnow().timestamp(), guild_id, member_id))
            else: # User is leaving VC
                cursor.execute("SELECT joined_vc FROM discord.users WHERE guild_id = %s AND member_id = %s",(guild_id, member_id))
                joined = cursor.fetchone()
                added_points = ""
                if joined != None and joined[0] != None and joined[0] > 0:
                    duration = (date.utcnow() - date.fromtimestamp(joined[0]))
                    if duration.seconds > 60:
                        minutes = int(duration.seconds / 60)
                        added_points = f", voice = voice + {minutes}, points = points + {minutes}"
                            
                cursor.execute(f"UPDATE discord.users SET joined_vc = -1 {added_points} WHERE guild_id = %s AND member_id = %s",(guild_id, member_id))
                
                if added_points != "": cnx.commit()