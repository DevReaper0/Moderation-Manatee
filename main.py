from discord.ext import commands, ipc
# Import the keep alive file
import keep_alive
import os
import replit

from pathlib import Path
import motor.motor_asyncio

from cogs._mongo import Document
import cogs._json
import cogs._utils

from dotenv import load_dotenv

load_dotenv()


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ipc = ipc.Server(self, secret_key="darubyminer360")

        self.connection_url = os.environ.get('MONGO')
        self.muted_users = {}

        self.default_rules = []
        self.default_filtered_messages = ["fuck", "shit", "ass"]

    async def on_ipc_ready(self):
        """Called upon the IPC Server being ready"""
        print("Ipc server is ready.")

    async def on_ipc_error(self, endpoint, error):
        """Called upon an error being raised within an IPC route"""
        print(endpoint, "raised", error)


def get_prefix(client, message):
    data = cogs._json.read_json('prefixes')
    if not str(message.guild.id) in data or data[str(message.guild.id)] == "=":
        prefixes = ['=']

        if not message.guild:
            prefixes = ['==']

        return commands.when_mentioned_or(*prefixes)(client, message)
    return commands.when_mentioned_or(data[str(message.guild.id)])(client, message)


bot = Bot(
    # Create a new bot
    command_prefix=get_prefix,  # Set the prefix
    description='A moderation bot',  # Set a description for the bot
    owner_id=595353331468075018,  # Your unique User ID
    case_insensitive=True  # Make the commands case insensitive
)

# case_insensitive=True is used as the commands are case sensitive by default

_cogs = ['cogs.moderation', 'cogs.misc', 'cogs.events']


@bot.ipc.route()
async def get_guild_count(data):
    return len(bot.guilds)  # returns the len of the guilds to the client


@bot.ipc.route()
async def get_guild_ids(data):
    final = []
    for guild in bot.guilds:
        final.append(guild.id)
    return final  # returns the guild ids to the client


@bot.ipc.route()
async def get_guild(data):
    guild = bot.get_guild(data.guild_id)
    if guild is None: return None

    guild_data = {
        "name": guild.name,
        "id": guild.id,
        "prefix": cogs._utils._get_prefix_for_guild(guild)
    }

    return guild_data


@bot.event
async def on_ready():
    replit.clear()
    print(f'Logged in as {bot.user.name} - {bot.user.id}')

    # Change status here

    bot.mongo = motor.motor_asyncio.AsyncIOMotorClient(str(bot.connection_url))
    bot.db = bot.mongo["darubyminer360"]
    bot.config = Document(bot.db, "config")
    bot.mutes = Document(bot.db, "mutes")
    bot.warns = Document(bot.db, "warns")

    currentMutes = await bot.mutes.get_all()
    for mute in currentMutes:
        bot.muted_users[mute["_id"]] = mute

    bot.remove_command('help')
    # Removes the help command
    # Make sure to do this before loading the cogs
    for cog in _cogs:
        bot.load_extension(cog)
    return


# Start the server
keep_alive.keep_alive(bot)

# Finally, login the bot
bot.ipc.start()
bot.run(os.environ.get('TOKEN'), bot=True, reconnect=True)
