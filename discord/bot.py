from datetime import datetime
import discord
from discord.ext.commands.core import has_any_role

from config import __DISCORD_TOKEN, __DISCORD_CLIENT_ID, __DEVELOPERS

from discord.ext import commands

from modules.slash_commands import slash_commands
from cogs import presence, scheduled, tracking, connector

import time

client = commands.Bot(command_prefix="l.", intents=discord.Intents.all())
slash = slash_commands(client)

@client.event
async def on_ready():
    client.add_cog(connector.Connector(client))
    client.add_cog(presence.Presence(client))
    client.add_cog(scheduled.Tasks(client))
    client.add_cog(tracking.Tracking(client))
    print("booted v1.06")

slash.setup()

def in_query(query, kws):
    for kw in kws:
        if kw.lower() in query.lower():
            return True
    return False

MYSQL_RETURN_STATEMENTS = ["SELECT", "DESCRIBE", "VALUES", "TABLE"]
MYSQL_MANIPULATION_STATEMENTS = ["UPDATE", "SET", "DELETE", "INSERT", "REPLACE", "ALTER", "CREATE", "DROP", "RENAME"]

@client.command()
async def invite(ctx):
    await ctx.send(f"https://discord.com/api/oauth2/authorize?client_id={__DISCORD_CLIENT_ID}&permissions=8&scope=bot%20applications.commands")

@client.command()
async def sql(ctx, *args):
    if ctx.message.author.id in __DEVELOPERS:
        query = ctx.message.content[6:]

        if not ";" in query: return
        cnx, cursor = client.get_cog("Connector").get()
        cursor.execute(query)
        
        if in_query(query, MYSQL_MANIPULATION_STATEMENTS):
            cnx.commit()
        elif in_query(query, MYSQL_RETURN_STATEMENTS):
            await ctx.send(str(cursor.fetchall()))

@client.command()
async def todb(ctx, *args):
    if ctx.message.author.id in __DEVELOPERS:
        num_members = ctx.guild.member_count
        start = time.time()

        await ctx.send(f"Updating DB entries for {num_members} members.")
        cnx, cursor = client.get_cog("Connector").get()
        tracking = client.get_cog("Tracking")

        created_at = (ctx.guild.created_at) 
        icon_url = None if ctx.guild.icon == None else f"https://cdn.discordapp.com/icons/{ctx.guild.id}/{ctx.guild.icon}.webp"

        cursor.execute("""
        UPDATE discord.guilds
        SET name = %s, members = %s, created = %s, icon = %s
        WHERE guild_id = %s
        """, (ctx.guild.name, ctx.guild.member_count, created_at, icon_url, ctx.guild.id))

        for member in ctx.guild.members:
            if not tracking.is_registered(member):
                tracking.register(member)
            else:
                pfp = None if member.avatar == None else f"https://cdn.discordapp.com/avatars/{member.id}/{member.avatar}.webp"

                cursor.execute("""
                    UPDATE discord.users
                    SET username = %s, pfp = %s
                    WHERE member_id = %s
                """, (member.name, pfp, member.id))

        cnx.commit()

        rows_affected = cursor.rowcount
        await ctx.send(f"Updated {rows_affected} in {time.time()-start}s.")

client.run(__DISCORD_TOKEN)