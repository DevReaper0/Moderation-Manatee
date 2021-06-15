from quart import Quart, render_template, request, session, redirect, url_for
from quart_discord import DiscordOAuth2Session
import discord as dis
from discord.ext import ipc

from threading import Thread

import cogs._utils

app = Quart(__name__)
ipc_client = ipc.Client(secret_key="darubyminer360")

app.config["SECRET_KEY"] = "test123"
app.config["DISCORD_CLIENT_ID"] = 852752482123644959
app.config["DISCORD_CLIENT_SECRET"] = "vb_H7gq17qRufR9O8CTv31ny9V-hEhVD"
app.config["DISCORD_REDIRECT_URI"] = "http://127.0.0.1:5000/callback"

discord = DiscordOAuth2Session(app)

bot = ""

@app.route("/")
async def home():
    return await render_template("index.html", authorized=await discord.authorized)


@app.route("/login")
async def login():
    return await discord.create_session()


@app.route("/callback")
async def callback():
    try:
        await discord.callback()
    except Exception:
        pass

    return redirect(url_for("dashboard"))


@app.route("/dashboard")
async def dashboard():
    if not await discord.authorized:
        return redirect(url_for("login"))

    guild_count = await ipc_client.request("get_guild_count")
    guild_ids = await ipc_client.request("get_guild_ids")

    user_guilds = await discord.fetch_guilds()

    guilds = []

    for guild in user_guilds:
        if guild.permissions.administrator:
            guild.class_color = "green-border" if guild.id in guild_ids else "red-border"
            guilds.append(guild)
        elif guild.id in guild_ids:
            guild.class_color = "yellow-border"
            guilds.append(guild)

    guilds.sort(key=lambda x: x.class_color == "red-border")
    name = (await discord.fetch_user()).name
    return await render_template("dashboard.html", guild_count=guild_count, guilds=guilds, username=name)


@app.route("/dashboard/<int:guild_id>", methods=["POST", "GET"])
async def dashboard_server(guild_id):
    if not await discord.authorized:
        return redirect(url_for("login"))

    guild_data = await ipc_client.request("get_guild", guild_id=guild_id)
    if guild_data is None:
        return redirect(
            f'https://discord.com/oauth2/authorize?&client_id={app.config["DISCORD_CLIENT_ID"]}&scope=bot&permissions=8&guild_id={guild_id}&response_type=code&redirect_uri={app.config["DISCORD_REDIRECT_URI"]}')

    for g in await discord.fetch_guilds():
        if g.id == guild_id:
            guild = g

    user = await discord.fetch_user()
    admin = guild.permissions.administrator
    name = user.name

    guild1 = bot.get_guild(guild.id)

    if request.method == "POST":
        prefix = (await request.form)["newprefix"]

        await cogs._utils._set_guild_prefix(user, guild1, prefix)

        return redirect(url_for("dashboard") + "/" + str(guild_id))
    else:
        prefix = cogs._utils._get_prefix_for_guild(guild1)
        return await render_template("dashboard_server.html", guild=guild, admin=admin, username=name, user=user,
                                     prefix=prefix)


def run():
    app.run(debug=True)


def keep_alive(b):
    global bot
    bot = b

    server = Thread(target=run)
    server.start()
