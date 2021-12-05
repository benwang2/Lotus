__MYSQL_CONFIG = {"host":"0.0.0.0","user":"admin","password":"admin","database":"default_schema"}

import os

import flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import (
    Flask,
    redirect,
    render_template,
    jsonify,
    g,
    request
)
from flask.helpers import make_response, send_from_directory, url_for

from time import (
    time as now,
    sleep
)

import mysql.connector
import json, threading

app = Flask(__name__)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["999 per minute"]
)

class MySQLClient():
    def __init__(self):
        self.cursor = None
        self.cnx = None
    
    def get(self):
        if self.cnx == None:
                       
            try:
                self.cnx = mysql.connector.connect(**__MYSQL_CONFIG)
                self.cursor = self.cnx.cursor(buffered=True)
            except mysql.connector.Error as err:
                print("Something went wrong: {}".format(err))

        return (self.cnx, self.cursor)

    def close(self):
        if self.cnx != None:
            self.cursor.close()
            self.cnx.close()
            self.cursor = None
            self.cnx = None
            print("Closed cursor")

    def timer(self):
        if now() > self.expires and self.cnx != None:
            self.close()

SQLClient = MySQLClient()

@app.route("/", methods=['GET','POST'])
def home():
    return None

@app.route('/resources/<path>/<filename>')
def serve_static(path, filename):
    root_dir = os.path.dirname(os.getcwd())
    return send_from_directory("resources/"+path, filename)     

@app.route("/guilds/<guild_id>")
def guilds(guild_id):
    _, cursor = SQLClient.get()
    cursor.execute("SELECT name, members, created, icon FROM discord.guilds WHERE guild_id = %s;",(guild_id,))
    
    row = cursor.fetchone()

    if row != None:
        name, members, created_at, icon_url = row[0], row[1], row[2], row[3]

        shorthand = name[0:1]
        if len(shorthand.split(" ")) > 1:
            words = shorthand.split(" ")
            shorthand = "".join(word[0:1] for word in words)

        g.guild = {
            "id":guild_id,
            "name":name,
            "members":members,
            "created_at":f"{created_at.month}/{created_at.day}/{created_at.year-2000}",
            "icon":icon_url,
            "short":shorthand.upper()
        }

        SQLClient.close()
        return render_template("guilds.html")
    else:

        SQLClient.close()
        return redirect("/")

cache = {}

@app.route("/json/<guild_id>", methods=["GET"])
@limiter.limit("60/minute",override_defaults=False)
def get_json(guild_id):
    data = {'members':[],'generated':0}

    if cache.get(guild_id) == None or (cache.get(guild_id) != None and now() - cache[guild_id]['generated'] > 60):
        
        _, cursor = SQLClient.get()

        cursor.execute("SELECT member_id FROM discord.users WHERE guild_id = %s LIMIT 1;",(guild_id, ))

        if cursor.fetchone() != None:
            
            cursor.execute("SELECT username, pfp, text, voice, points FROM discord.users WHERE guild_id = %s ORDER BY points DESC LIMIT 50;", (guild_id, ))
            data['generated'] = now()

            row = cursor.fetchone()
            while row != None:
                print(row[0],row[4])

                data['members'].append({
                    "username":row[0],
                    "pfp":row[1],
                    "messages":row[2],
                    "voice":row[3],
                    "points":row[4]
                })
                row = cursor.fetchone()

        cache[guild_id] = data
    else:
        data = cache[guild_id]

    SQLClient.close()

    return jsonify(data)
    
if __name__ == "__main__":
    app.run(host="0.0.0.0")