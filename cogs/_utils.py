from discord.ext import commands, tasks
from discord.ext.buttons import Paginator
import discord
import re
from copy import deepcopy
from dateutil.relativedelta import relativedelta
import os
import cogs._json

time_regex = re.compile("(?:(\d{1,5})(h|s|m|d))+?")
time_dict = {'h': 3600, 's': 1, 'm': 60, 'd': 86400}

class TimeConverter(commands.Converter):
    async def convert(self, ctx, argument):
        args = argument.lower()
        matches = re.findall(time_regex, args)
        time = 0
        for key, value in matches:
            try:
                time += time_dict[value] * float(key)
            except KeyError:
                raise commands.BadArgument(f"{value} is an invalid time key! h|m|s|d are valid arguments")
            except ValueError:
                raise commands.BadArgument(f"{key} is not a number!")
        return round(time)

class Pag(Paginator):
    async def teardown(self):
        try:
            await self.page.clear_reactions()
        except discord.HTTPException:
            pass

def _set_log_channel(ctx, name):
    data = _get_data(ctx)
    data[str(ctx.guild.id)] = name

    cogs._json.write_json(data, 'log_channel_names')

def _get_data(ctx):
    cwd = cogs._json.get_path()
    if os.path.exists(cwd + '/bot_config/log_channel_names.json'):
        return cogs._json.read_json('log_channel_names')
    else:
        data = {
            str(ctx.guild.id): "general"
        }

        cogs._json.write_json(data, 'log_channel_names')
        return cogs._json.read_json('log_channel_names')

def _get_guild_data(guild):
    cwd = cogs._json.get_path()
    if os.path.exists(cwd + '/bot_config/log_channel_names.json'):
        return cogs._json.read_json('log_channel_names')
    else:
        data = {
            str(guild.id): "general"
        }

        cogs._json.write_json(data, 'log_channel_names')
        return cogs._json.read_json('log_channel_names')

def _get_log_channel(ctx):
    return discord.utils.get(ctx.guild.channels, name=_get_log_channel_name(ctx))

def _get_guild_log_channel(guild):
    return discord.utils.get(guild.channels, name=_get_guild_log_channel_name(guild))

def _get_log_channel_name(ctx):
    return _get_data(ctx)[str(ctx.guild.id)]

def _get_guild_log_channel_name(guild):
    return _get_guild_data(guild)[str(guild.id)]

def _get_prefix(ctx):
    data = cogs._json.read_json('prefixes')

    if str(ctx.guild.id) in data:
        prefix = data[str(ctx.guild.id)]
    else:
        prefix = "="
    return prefix

def _get_prefix_for_guild(guild):
    data = cogs._json.read_json('prefixes')

    if str(guild.id) in data:
        prefix = data[str(guild.id)]
    else:
        prefix = "="
    return prefix

async def _set_guild_prefix(user, guild, pre='='):
    data = cogs._json.read_json('prefixes')
    data[str(guild.id)] = pre
    cogs._json.write_json(data, 'prefixes')

    try:
        channel = cogs._utils._get_guild_log_channel(guild)
        if isinstance(user, discord.User):
            name = user.display_name
        else:
            name = user.name
        embed = discord.Embed(title=f"{name} changed the prefix",
                              description=f"The prefix is now `{pre}`")
        await channel.send(embed=embed)
    except:
        pass
