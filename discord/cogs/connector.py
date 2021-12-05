from discord.ext import tasks, commands

from time import time as now
import mysql.connector
from config import __MYSQL_CONFIG as cnx_conf

class Connector(commands.Cog):
    def __init__(self, bot):
        print("init connector")
        self.cursor = None
        self.cnx = None
        self.expires = 0

    def get(self):
        self.expires = int(now())+3
        if self.cnx == None:
            self.cnx = mysql.connector.connect(**cnx_conf)
            self.cursor = self.cnx.cursor(buffered=True)
        elif self.cnx != None and self.cursor == None:
            self.cursor = self.cnx.cursor(buffered=True)
        return (self.cnx, self.cursor)

    def close(self):
        if self.cnx != None:
            self.cnx.close()

    @tasks.loop(seconds=1)
    async def timer(self):
        if now() > self.expires and self.cnx != None:
            self.cursor.close()
            self.cnx.close()
            self.cursor = None
            self.cnx = None