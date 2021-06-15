from discord.ext import commands, tasks
import discord
import asyncio
import datetime
from copy import deepcopy
from dateutil.relativedelta import relativedelta
import cogs._utils
from cogs._utils import Pag

colors = {
  'DEFAULT': 0x000000,
  'WHITE': 0xFFFFFF,
  'AQUA': 0x1ABC9C,
  'GREEN': 0x2ECC71,
  'BLUE': 0x3498DB,
  'PURPLE': 0x9B59B6,
  'LUMINOUS_VIVID_PINK': 0xE91E63,
  'GOLD': 0xF1C40F,
  'ORANGE': 0xE67E22,
  'RED': 0xE74C3C,
  'GREY': 0x95A5A6,
  'NAVY': 0x34495E,
  'DARK_AQUA': 0x11806A,
  'DARK_GREEN': 0x1F8B4C,
  'DARK_BLUE': 0x206694,
  'DARK_PURPLE': 0x71368A,
  'DARK_VIVID_PINK': 0xAD1457,
  'DARK_GOLD': 0xC27C0E,
  'DARK_ORANGE': 0xA84300,
  'DARK_RED': 0x992D22,
  'DARK_GREY': 0x979C9F,
  'DARKER_GREY': 0x7F8C8D,
  'LIGHT_GREY': 0xBCC0C0,
  'DARK_NAVY': 0x2C3E50,
  'BLURPLE': 0x7289DA,
  'GREYPLE': 0x99AAB5,
  'DARK_BUT_NOT_BLACK': 0x2C2F33,
  'NOT_QUITE_BLACK': 0x23272A
}


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mute_task = self.check_current_mutes.start()

    def cog_unload(self):
        self.mute_task.cancel()

    @commands.command(
        name="kick",
        description="Kicks the given user",
        usage="<user> [reason]",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await ctx.guild.kick(user=member, reason=reason)
        
        channel = cogs._utils._get_log_channel(ctx)
        embed = discord.Embed(title=f"{ctx.author.display_name} kicked {member.display_name}", description=reason)
        await channel.send(embed=embed)

    @commands.command(
        name="ban",
        description="Bans the given user",
        usage="<user> [reason]",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        await ctx.guild.ban(user=member, reason=reason)

        channel = cogs._utils._get_log_channel(ctx)
        embed = discord.Embed(title=f"{ctx.author.display_name} banned {member.display_name}", description=reason)
        await channel.send(embed=embed)

    @commands.command(
        name="unban",
        description="Unbans the given user",
        usage="<user> [reason]",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self, ctx, member, *, reason=None):
        member = await self.bot.fetch_user(int(member))
        await ctx.guild.unban(user=member, reason=reason)

        channel = cogs._utils._get_log_channel(ctx)
        embed = discord.Embed(title=f"{ctx.author.display_name} unbanned {member.display_name}", description=reason)
        await channel.send(embed=embed)

    @tasks.loop(minutes=5)
    async def check_current_mutes(self):
        currentTime = datetime.datetime.now()
        mutes = deepcopy(self.bot.muted_users)
        for key, value in mutes.items():
            if value['muteDuration'] is None:
                continue

            unmuteTime = value['mutedAt'] + relativedelta(seconds=value['muteDuration'])

            if currentTime >= unmuteTime:
                guild = self.bot.get_guild(value['guildId'])
                member = guild.get_member(value['_id'])

                roles = cogs._json.read_json('muted_roles')

                if str(guild.id) in roles:
                    role = discord.utils.get(guild.roles, id=int(str(guild.id)))
                else:
                    role = discord.utils.get(guild.roles, name="Muted")

                await self.bot.mutes.delete(member.id)
                try:
                    self.bot.muted_users.pop(member.id)
                except KeyError:
                    pass

    @check_current_mutes.before_loop
    async def before_check_current_mutes(self):
        await self.bot.wait_until_ready()

    @commands.command(
        name='mute',
        description="Mutes the given user for x time!",
        ussage='<user> [time] [reason]'
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, *, time: cogs._utils.TimeConverter=None, reason=None):
        roles = cogs._json.read_json('muted_roles')

        if str(ctx.guild.id) in roles:
            role = discord.utils.get(ctx.guild.roles, id=int(str(ctx.guild.id)))
        else:
            role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not role:
            await ctx.send(f"No muted role was found! Please create one named `Muted` or set one with {cogs._utils._get_prefix(ctx)}set_muted_role")
            return

        try:
            if self.bot.muted_users[member.id]:
                await ctx.send(f"This user is already muted")
                return
        except KeyError:
            pass

        data = {
            '_id': member.id,
            'mutedAt': datetime.datetime.now(),
            'muteDuration': time or None,
            'mutedBy': ctx.author.id,
            'guildId': ctx.guild.id,
        }
        await self.bot.mutes.upsert(data)
        self.bot.muted_users[member.id] = data

        await member.add_roles(role)

        channel = cogs._utils._get_log_channel(ctx)

        if not time:
            embed = discord.Embed(title=f"{ctx.author.display_name} muted {member.display_name}", description=reason)
        else:
            minutes, seconds = divmod(time, 60)
            hours, minutes = divmod(minutes, 60)
            if int(hours):
                embed = discord.Embed(
                    title=f"{ctx.author.display_name} muted {member.display_name} for {hours} hours, {minutes} minutes, and {seconds} seconds",
                    description=reason)
            elif int(minutes):
                embed = discord.Embed(
                    title=f"{ctx.author.display_name} muted {member.display_name} for {minutes} minutes and {seconds} seconds",
                    description=reason)
            elif int(seconds):
                embed = discord.Embed(
                    title=f"{ctx.author.display_name} muted {member.display_name} for {seconds} seconds",
                    description=reason)

        await channel.send(embed=embed)

        if time and time < 300:
            await asyncio.sleep(time)

            if role in member.roles:
                await member.remove_roles(role)
                await member.send(f"You have been unmuted in `{ctx.guild.name}`")

            await self.bot.mutes.delete(member.id)
            try:
                self.bot.muted_users.pop(member.id)
            except KeyError:
                pass

    @commands.command(
        name='unmute',
        description="Unmutes a muted user!",
        usage='<user> [reason]'
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def unmute(self, ctx, member, *, reason=None):
        data = cogs._json.read_json('muted_roles')

        if str(ctx.guild.id) in data:
            role = discord.utils.get(ctx.guild.roles, id=int(str(ctx.guild.id)))
        else:
            role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not role:
            await ctx.send(
                f"No muted role was found! Please create one named `Muted` or set one with {cogs._utils._get_prefix(ctx)}set_muted_role")
            return

        await self.bot.mutes.delete(member.id)
        try:
            self.bot.muted_users.pop(member.id)
        except KeyError:
            pass

        if role not in member.roles:
            await ctx.send("This member is not muted.")
            return

        await member.remove_roles(role)
        await member.send(f"You have been unmuted in `{ctx.guild.name}`")

        channel = cogs._utils._get_log_channel(ctx)
        embed = discord.Embed(title=f"{ctx.author.display_name} unmuted {member.display_name}", description=reason)
        await channel.send(embed=embed)

    @commands.command(
        name="warn",
        description="Warns the given user",
        usage="<member> [reason]",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def warn(self, ctx, member: discord.Member, *, reason):
        if member.id in [ctx.author.id, self.bot.user.id]:
            return await ctx.send("You cannot warn yourself or the bot!")

        current_warn_count = len(
            await self.bot.warns.find_many_by_custom(
                {
                    "user_id": member.id,
                    "guild_id": member.guild.id
                }
            )
        ) + 1

        warn_filter = {"user_id": member.id, "guild_id": member.guild.id, "number": current_warn_count}
        warn_data = {"reason": reason, "timestamp": ctx.message.created_at, "warned_by": ctx.author.id}

        await self.bot.warns.upsert_custom(warn_filter, warn_data)

        embed = discord.Embed(
            title="You are being warned:",
            description=f"__**Reason**__:\n{reason}",
            color=discord.Color.red(),
            timestamp=ctx.message.created_at
        )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.set_footer(text=f"Warn: {current_warn_count}")

        try:
            await member.send(embed=embed)
            await ctx.send("Warned that user in dm's for you.")
        except discord.HTTPException:
            await ctx.send(member.mention, embed=embed)

        embed = discord.Embed(
            title=f"{ctx.author.display_name} warned {member.display_name}",
            description=f"__**Reason**__:\n{reason}",
            color=discord.Color.red(),
            timestamp=ctx.message.created_at
        )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.set_footer(text=f"Warn: {current_warn_count}")

        await cogs._utils._get_log_channel(ctx).send(embed=embed)

    @commands.command(
        name="warns",
        description="Gives a list of warns the given user has",
        usage="<member>",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def warns(self, ctx, member: discord.Member):
        warn_filter = {"user_id": member.id, "guild_id": member.guild.id}
        warns = await self.bot.warns.find_many_by_custom(warn_filter)

        if not bool(warns):
            return await ctx.send(f"Couldn't find any warns for: `{member.display_name}`")

        warns = sorted(warns, key=lambda x: x["number"])

        pages = []
        for warn in warns:
            description = f"""
                Warn Number: `{warn['number']}`
                Warn Reason: `{warn['reason']}`
                Warned By: <@{warn['warned_by']}>
                Warn Date: {warn['timestamp'].strftime("%I:%M %p %B %d, %Y")}
                """
            pages.append(description)

        await Pag(
            title=f"Warns for `{member.display_name}`",
            color=0xCE2029,
            entries=pages,
            length=1
        ).start(ctx)

    @commands.command(
        name="deletewarn",
        description="Deletes the given warn or every warn for the given user",
        aliases=["delwarn", "dw"],
        usage="<member> [reason]",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def deletewarn(self, ctx, member: discord.Member, warn: int = None):
        filter_dict = {"user_id": member.id, "guild_id": member.guild.id}
        if warn:
            filter_dict["number"] = warn

        was_deleted = await self.bot.warns.delete_by_custom(filter_dict)
        if was_deleted and was_deleted.acknowledged:
            if warn:
                embed = discord.Embed(
                    title=f"{ctx.author.display_name} deleted warn number `{warn}` for `{member.display_name}`",
                    description=f"Warns remaining: {len(await self.bot.warns.find_many_by_custom(filter_dict))}",
                    color=discord.Color.red(),
                    timestamp=ctx.message.created_at
                )

                return await cogs._utils._get_log_channel(ctx).send(embed=embed)

            embed = discord.Embed(
                title=f"{ctx.author.display_name} deleted `{was_deleted.deleted_count}` warns for `{member.display_name}`",
                description=f"Warns remaining: {len(await self.bot.warns.find_many_by_custom(filter_dict))}",
                color=discord.Color.red(),
                timestamp=ctx.message.created_at
            )

            return await cogs._utils._get_log_channel(ctx).send(embed=embed)

        await ctx.send(
            f"I could not find any warns for `{member.display_name}` to delete matching your input"
        )

    @commands.command(
        name="purge",
        description="Purges the current channel",
        aliases=["clear"],
        usage="[amount]",
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def purge(self, ctx, amount=15):
        await ctx.channel.purge(limit=amount+1)
        
        channel = cogs._utils._get_log_channel(ctx)
        messages = "message"
        if amount != 1: messages += "s"
        embed = discord.Embed(title=f"{ctx.author.display_name} purged {ctx.channel}", description=f"{amount} {messages} were cleared")
        await channel.send(embed=embed)

    @commands.command(
        name='lockdown',
        description='Puts the current or given channel under lockdown',
        usage='[channel]'
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    async def lockdown(self, ctx, channel: discord.TextChannel=None):
        channel = channel or ctx.channel

        data = cogs._json.read_json('member_roles')
        if ctx.guild.default_role not in channel.overwrites and (str(ctx.guild.id) in data and discord.utils.get(ctx.guild.roles, id=int(str(ctx.guild.id))) not in channel.overwrites):
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False)
            }
            await channel.edit(overwrites=overwrites)

            embed = discord.Embed(title=f"{ctx.author.display_name} put `{channel.name}` on lockdown",
                                  description=f"<#{channel.id}> is now on lockdown")
        elif str(ctx.guild.id) in data and (channel.overwrites[discord.utils.get(ctx.guild.roles, id=int(str(ctx.guild.id)))].send_messages == True or channel.overwrites[discord.utils.get(ctx.guild.roles, id=int(str(ctx.guild.id)))].send_messages is None):
            overwrites = channel.overwrites[discord.utils.get(ctx.guild.roles, id=int(str(ctx.guild.id)))]
            overwrites.send_messages = False
            await channel.set_permissions(discord.utils.get(ctx.guild.roles, id=int(str(ctx.guild.id))), overwrites=overwrites)

            embed = discord.Embed(title=f"{ctx.author.display_name} put `{channel.name}` on lockdown",
                                  description=f"<#{channel.id}> is now on lockdown")
        elif channel.overwrites[ctx.guild.default_role].send_messages == True or channel.overwrites[ctx.guild.default_role].send_messages is None:
            overwrites = channel.overwrites[ctx.guild.default_role]
            overwrites.send_messages = False
            await channel.set_permissions(ctx.guild.default_role, overwrites=overwrites)
            embed = discord.Embed(title=f"{ctx.author.display_name} put `{channel.name}` on lockdown",
                                  description=f"<#{channel.id}> is now on lockdown")
        else:
            if str(ctx.guild.id) in data:
                overwrites = channel.overwrites[discord.utils.get(ctx.guild.roles, id=int(str(ctx.guild.id)))]
                overwrites.send_messages = False
                await channel.set_permissions(discord.utils.get(ctx.guild.roles, id=int(str(ctx.guild.id))), overwrites=overwrites)
            else:
                overwrites = channel.overwrites[ctx.guild.default_role]
                overwrites.send_messages = False
                await channel.set_permissions(ctx.guild.default_role, overwrites=overwrites)

            embed = discord.Embed(title=f"{ctx.author.display_name} removed `{channel.name}` from lockdown",
                                  description=f"<#{channel.id}> is no longer on lockdown")

        await channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Moderation(bot))
