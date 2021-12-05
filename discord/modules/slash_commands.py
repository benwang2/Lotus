from challonge.tournaments import start
import discord

from datetime import datetime, timedelta
from calendar import monthrange
import pytz, random, string, traceback

from discord_slash import SlashCommand, SlashContext
from discord_slash.model import SlashCommandPermissionType
from discord_slash.utils.manage_commands import create_option, create_choice, create_permission

from config import __HOST

guilds = []

class slash_commands():
    def __init__(self, client):
        self.slash = SlashCommand(client, sync_commands=True)
        self.client = client

    def setup(self):
        slash, client = self.slash, self.client

        @slash.slash(
            guild_ids=guilds,
            name="reminders",
            description="List and interact with your reminders. ID option is used for reminder deletion.",
            options = [
                create_option(
                    name="action",
                    description="Action to perform on reminders.",
                    option_type=3,
                    required=False,
                    choices=[
                        create_choice(
                            name="list",
                            value="list"
                        ),
                        create_choice(
                            name="delete",
                            value="del"
                        ),
                        create_choice(
                            name="clear",
                            value="clear"
                        )
                    ]
                ),
                create_option(
                    name="id",
                    description="ID of reminder to delete.",
                    option_type=3,
                    required=False
                ),
            ],
            
        )
        async def _reminders(ctx: SlashContext, action: str = "list", id: str=None):
            cnx, cursor = client.get_cog("Connector").get()
            if action == "list":
                cursor.execute(f"SELECT reminder_id, channel_id, message, time FROM discord.reminders WHERE member_id = {ctx.author_id}")
                reminders = cursor.fetchall()
                embed = discord.Embed(title="Reminders",description=f"You have {len(reminders)} active reminders.", color=discord.Color.blue())
                for reminder in reminders:
                    embed_name = datetime.fromtimestamp(reminder[3]).astimezone(pytz.timezone('US/Eastern')) + timedelta(hours=4)
                    embed_name = embed_name.strftime('%Y-%m-%d %I:%M %p')+" EST"
                    embed_value = f"**{reminder[0]}** {client.get_channel(reminder[1]).mention} {reminder[2]}"
                    embed.add_field(name=embed_name, value=embed_value, inline=True)

                await ctx.send(embed=embed)

            elif action == "del":
                if id != None:
                    cursor.execute(f"DELETE FROM discord.reminders WHERE reminder_id = '{id}' AND member_id = {ctx.author_id}")
                    cnx.commit()
                    await ctx.send(
                        embed = discord.Embed(
                            title=f"Deleted {cursor.rowcount} reminder{'s' if cursor.rowcount != 1 else ''}",
                            color=discord.Color.green()
                        )
                    )
                else:
                    await ctx.send(embed=discord.Embed(title="Failed to delete reminder",description="No ID was specified.",color=discord.Color.red()))

            elif action == "clear":
                cursor.execute(f"DELETE FROM discord.reminders WHERE member_id = {ctx.author_id}")
                cnx.commit()
                await ctx.send(f"Deleted {cursor.rowcount} active reminders.")

        @slash.slash(
            guild_ids=guilds,
            name="top",
            description="Get a link to leaderboard for your guild.",
            options = []
        )
        async def _top(ctx: SlashContext):
            await ctx.send(f"{__HOST}/guilds/{ctx.guild.id}}")

        @slash.slash(
            guild_ids=guilds,
            name="remind",
            description="Sets a personal reminder for you. All times in EST, 24-Hour clock",
            options = [
                create_option(
                    name="text",
                    description="We'll remind you with this text as the message. (max_characters=250)",
                    option_type=3,
                    required=True
                ),
                create_option(
                    name="date",
                    description = "[mm/dd/yy]",
                    option_type = 3,
                    required=False
                ),
                create_option(
                    name="time",
                    description = "[hh:mm] (24 HOUR EST)",
                    option_type = 3,
                    required=False
                ),
                create_option(
                    name="channel",
                    description = "Channel to send reminder to",
                    option_type = 7,
                    required=False
                ),
                create_option(
                    name = "mention",
                    description = "Should the bot mention you in the reminder?",
                    option_type = 5,
                    required = False
                )
            ],
            
        )
        async def _remind(ctx: SlashContext, text: str, date_str: str=None, time_str: str=None, mention: bool=True):
            today = (datetime.now() - timedelta(hours=4))

            month = today.month
            day = today.day
            year = today.year
            hour = today.hour
            minute = today.minute

            reminder = None

            channel_id, member_id = ctx.channel_id, ctx.author_id

            cnx, cursor = client.get_cog("Connector").get()

            cursor.execute(f"SELECT message FROM discord.reminders WHERE member_id = {member_id}")
            reminders = cursor.fetchall()

            errs = []

            if (reminders != None and len(reminders) >= 100):
                errs.append("You have too many reminders (max 100)")

            if text != None and len(text) > 250:
                errs.append("Message too long")
            elif text == None:
                errs.append("No message")

            if date_str != None:
                params = date_str.split("/")
                if len(params)<2 or len(params)>3:
                    errs.append("Dates should be mm/dd/yyyy")
                else:
                    month, day, year = params[0], params[1], today.year if len(params) else params[2]

                    try:
                        month = int(month)
                        day = int(day)
                        year = int(year)

                        num_days = monthrange(year, month)[1]

                        if month > 12 or month < 1:
                            errs.append("Month should be between 1 and 12")

                        if day > num_days or day < 1:
                            errs.append(f"Day should be between 1 and {num_days}")

                        if year < today.year or month < today.month or (today.month == month and today.day < today.day):
                            errs.append(f"Date invalid, must be today or later.")

                        
                    except Exception as e:
                        errs.append(repr(e))

            if time_str != None:
                params = time_str.split(":")

                if len(params) != 2:
                    errs.append("Time must be formatted as mm:ss")
                else:
                    hour, minute = params[0], params[1]

                    try:
                        hour, minute = int(hour), int(minute)

                        if hour < 0 or hour > 24:
                            errs.append(f"Hour must be between 0 and 24")
                        
                        if minute < 0 or minute > 59:
                            errs.append(f"Minute must be between 0 and 59")

                    except Exception as e:
                        errs.append(repr(e))
            else:
                errs.append("You must specify a time")


            if len(errs) > 0:
                embed = discord.Embed(title="Reminder failed to generate", description="Parameters were invalid.", color=discord.Color.red())
                embed.add_field(name="Errors",value=",".join(errs))
                await ctx.send(embed=embed)
            else: # TODO: Implement new date / time styling
                reminder = datetime(year=year,month=month,day=day,hour=hour,minute=minute)
                embed = discord.Embed(title="Reminder set!",description=f"Use the /reminders command to see a list of your reminders.", color=discord.Color.green())
                id = ''.join(random.choices(string.ascii_lowercase+string.digits,k=6))
                
                for i in range(5):
                    cursor.execute(f"""SELECT EXISTS (SELECT * FROM discord.reminders WHERE reminder_id = '{id}')""")
                    if len(cursor.fetchone()) == 0:
                        break
                    id = ''.join(random.choices(string.ascii_lowercase+string.digits,k=6))

                embed.add_field(name="ID",value=id)
                embed.add_field(name="Message",value=text)
                embed.add_field(name="Time",value=reminder.strftime('%Y-%m-%d %I:%M %p'))

                if mention:
                    text = f"<@{ctx.author.id}>"+text

                try:
                    formatted_time = int(reminder.timestamp())
                    cursor.execute(f"""INSERT INTO discord.reminders(member_id, reminder_id, channel_id, message, time)
                    VALUES ({member_id}, '{id}', {channel_id}, %s, %s);""",(text,formatted_time))
                    cnx.commit()
                    await ctx.send(embed=embed)
                except Exception as e:
                    await ctx.send(repr(e))

                

        @slash.slash(
            guild_ids=[711371824155590666, 675897612091785226],
            name="get",
            description="Gets the value of a field in a member's database entry.",
            permissions={
                'default_permission':False,
                675897612091785226:[
                    create_permission(675917068079464448, SlashCommandPermissionType.ROLE, True), # Leaders
                    create_permission(675916820682768388, SlashCommandPermissionType.ROLE, True), # Moderators
                    create_permission(825252691197689857, SlashCommandPermissionType.ROLE, True),  # Technicians
                    create_permission(675897612091785226, SlashCommandPermissionType.ROLE, False),
                ],
                711371824155590666:[
                    create_permission(711371824155590666, SlashCommandPermissionType.ROLE, True)
                ]
            },
            options = [
                create_option(
                    name = "id",
                    description = "Member ID",
                    option_type = 3,
                    required = True,
                )
            ]
        )
        async def _get(ctx: SlashContext, id: str):
            data = []
            try:
                id = ''.join(i for i in id if i.isdigit())
                _, cursor = client.get_cog("Connector").get()
                cursor.reset()
                cursor.execute("SELECT points, text, voice, username FROM discord.users WHERE guild_id = %s AND member_id = %s LIMIT 0, 1;",(ctx.guild_id, id))
                data = cursor.fetchone()

                if data == None or (data != None and len(data) == 0):
                    raise Exception("CustomException: User is either not registered or data could not be retrieved.")

                embed = discord.Embed(title="User activity statistics", description=f"<@{id}>'s stats.", color=0xCD5D67)
                embed.add_field(name="points", value=data[0], inline=True)
                embed.add_field(name="text", value=data[1], inline=True)
                embed.add_field(name="voice", value=data[2], inline=True)
                embed.add_field(name="name", value=data[3], inline=True)

                await ctx.send(embed = embed, allowed_mentions=None)
            except Exception as e:
                await ctx.send(f"""{traceback.print_exc()}""")

        @slash.slash(
            guild_ids=guilds,
            name="update",
            description="Sets a field in a member's database entry.",
            options = [
                create_option(
                    name = "id",
                    description = "Member ID",
                    option_type = 3,
                    required = True,
                ),
                create_option(
                    name = "field",
                    description = "Field to be edited",
                    option_type = 3,
                    required = True,
                    choices=[
                        create_choice(
                            name="points",
                            value="points"
                        ),
                        create_choice(
                            name="text",
                            value="text"
                        ),
                        create_choice(
                            name="voice",
                            value="voice"
                        )
                    ]
                ),
                create_option(
                    name = "value",
                    description = "New value",
                    option_type = 3,
                    required = True,
                ),
            ],
            permissions={
                'default_permission':False,
                711371824155590666: [
                    create_permission(154046172254830592, SlashCommandPermissionType.USER, True)
                ],
                675897612091785226: [
                    create_permission(675917068079464448, SlashCommandPermissionType.ROLE, True), #leaders
                    create_permission(154046172254830592, SlashCommandPermissionType.USER, True)  #me
                ]
            }
        )
        async def _update(ctx: SlashContext, id: str, field: str, value: str):
            id = ''.join(i for i in id if i.isdigit())
            try:
                cnx, cursor = client.get_cog("Connector").get()
                cursor.execute(f"UPDATE discord.users SET {field} = %s WHERE guild_id = %s AND member_id = %s", (int(value), ctx.guild.id, id))
                cnx.commit()
                await ctx.send(f"Set field={field} to value={value} for <@{id}>", allowed_mentions=None)
            except Exception as e:
                await ctx.send("Exception: "+repr(e))