from discord.ext import commands
import discord
import random
import cogs._json
import cogs._utils

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


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(
        name='help',
        description='Gives a list of the commands and groups of commands',
        aliases=['commands', 'command'],
        usage='[cog]'
    )
    async def help_command(self, ctx, cog='all'):
        # The third parameter comes into play when
        # only one word argument has to be passed by the user

        # Prepare the embed

        color_list = [c for c in colors.values()]
        help_embed = discord.Embed(
            title='Help',
            color=random.choice(color_list)
        )
        help_embed.set_thumbnail(url=self.bot.user.avatar_url)
        help_embed.set_footer(
            text=f'Requested by {ctx.message.author.display_name}',
            icon_url=self.bot.user.avatar_url
        )

        # Get a list of all cogs
        cogs = [c for c in self.bot.cogs.keys()]

        # If cog is not specified by the user, we list all cogs and commands

        if cog == 'all':
            for cog in cogs:
                # Get a list of all commands under each cog

                cog_commands = self.bot.get_cog(cog).get_commands()
                if len(cog_commands) > 0:
                    commands_list = ''
                    for comm in cog_commands:
                        commands_list += f'**{comm.name}** - *{comm.description}*\n'

                    # Add the cog's details to the embed.

                    help_embed.add_field(
                        name=cog,
                        value=commands_list,
                        inline=False
                    ).add_field(
                        name='\u200b', value='\u200b', inline=False
                    )

                    # Also added a blank field '\u200b' is a whitespace character.
            pass
        else:

            # If the cog was specified

            lower_cogs = [c.lower() for c in cogs]

            # If the cog actually exists.
            if cog.lower() in lower_cogs:

                # Get a list of all commands in the specified cog
                commands_list = self.bot.get_cog(cogs[ lower_cogs.index(cog.lower()) ]).get_commands()
                help_text=''

                # Add details of each command to the help text
                # Command Name
                # Description
                # [Aliases]
                #
                # Format
                for command in commands_list:
                    help_text += f'```{command.name}```\n' \
                        f'**{command.description}**\n\n'

                    # Also add aliases, if there are any
                    if len(command.aliases) > 0:
                        help_text += f'**Aliases :** `{"`, `".join(command.aliases)}`\n\n\n'
                    else:
                        # Add a newline character to keep it pretty
                        # That IS the whole purpose of custom help
                        help_text += '\n'

                    # Finally the format
                    help_text += f'Format: `@{self.bot.user.display_name}#{self.bot.user.discriminator}' \
                        f' {command.name} {command.usage if command.usage is not None else ""}`\n\n\n\n'

                help_embed.description = help_text
            else:
                # Notify the user of invalid cog and finish the command
                await ctx.send('Invalid cog specified.\nUse `help` command to list all cogs.')
                return

        await ctx.send(embed=help_embed)
        
        return

    @commands.command(
        name='prefix',
        description='Sets the prefix for the current server',
        usage='[prefix]'
    )
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx, *, pre='='):
        await cogs._utils._set_guild_prefix(ctx.author, ctx.guild, pre)

    @commands.command(
        name='set_member_role',
        description='Sets the member role for the current server',
        aliases=['setMemberRole', 'member_role', 'memberRole', 'member'],
        usage='[role]'
    )
    @commands.has_permissions(administrator=True)
    async def set_member_role(self, ctx, *, role: discord.Role):
        data = cogs._json.read_json('member_roles')
        data[str(ctx.message.guild.id)] = role.id
        cogs._json.write_json(data, 'member_roles')

        channel = cogs._utils._get_log_channel(ctx)
        embed = discord.Embed(title=f"{ctx.author.display_name} changed the member role", description=f"The member role is now `{role.name}`")
        await channel.send(embed=embed)

    @commands.command(
        name='set_muted_role',
        description='Sets the muted role for the current server',
        aliases=['setMutedRole', 'muted_role', 'mutedRole'],
        usage='[role]'
    )
    @commands.has_permissions(administrator=True)
    async def set_muted_role(self, ctx, *, role: discord.Role):
        data = cogs._json.read_json('muted_roles')
        data[str(ctx.message.guild.id)] = role.id
        cogs._json.write_json(data, 'muted_roles')

        channel = cogs._utils._get_log_channel(ctx)
        embed = discord.Embed(title=f"{ctx.author.display_name} changed the muted role",
                              description=f"The muted role is now `{role.name}`")
        await channel.send(embed=embed)

    @commands.command(
        name='set_log_channel',
        description='Sets the modlog channel for the current server',
        aliases=['setLogChannel', 'log_channel', 'logChannel', 'modlog'],
        usage='[channel]'
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def set_log_channel(self, ctx, channel: discord.TextChannel):
        cogs._utils._set_log_channel(ctx, channel.name)
        embed = discord.Embed(title=f"{ctx.author.display_name} changed the log channel",
                              description=f"{ctx.author.display_name} changed the log channel to <#{channel.id}>")
        await channel.send(embed=embed)

    @commands.command(
        name='set_filtered_words',
        description='Sets the filtered words for the current server',
        aliases=['setFilteredWords', 'filtered_words', 'filteredWords'],
        usage='<words>'
    )
    @commands.has_permissions(administrator=True)
    async def set_filtered_words(self, ctx, *words: str):
        data = cogs._json.read_json('filtered_words')
        new_words = []
        if len(words) == 1 and words[0] == "__reset__":
            new_words = self.bot.default_filtered_messages
        else:
            for word in words:
                if word.replace("_", " ") not in new_words:
                    new_words.append(word.replace("_", " "))
        data[str(ctx.message.guild.id)] = new_words
        cogs._json.write_json(data, 'filtered_words')

        channel = cogs._utils._get_log_channel(ctx)
        words_string = "`"
        for i in range(len(new_words)):
            words_string += new_words[i]
            if i < len(new_words) - 2:
                words_string += "`, `"
            elif i == len(new_words) - 2:
                words_string += "`, and `"
            words_string += "`"
        embed = discord.Embed(title=f"{ctx.author.display_name} updated the filtered words",
                              description=f"The filtered words are now {words_string}")
        await channel.send(embed=embed)

    @commands.command(
        name='get_filtered_words',
        description='Gives the filtered words for the current server',
        aliases=['getFilteredWords', 'give_filtered_words', 'giveFilteredWords', 'say_filtered_words',
                 'sayFilteredWords'],
        usage=''
    )
    @commands.has_permissions(administrator=True)
    async def get_filtered_words(self, ctx):
        data = cogs._json.read_json('filtered_words')
        words = data[str(ctx.message.guild.id)]

        channel = ctx.channel
        words_string = ""
        for i in range(len(words)):
            words_string += words[i]
            if i < len(words) - 2:
                words_string += ", "
            elif i == len(words) - 2:
                words_string += ", and "
        embed = discord.Embed(title=f"Filtered Words",
                              description=f"The filtered words are `{words_string}`")
        await channel.send(embed=embed)

    @commands.command(
        name='set_rules',
        description='Sets the rules for the current server',
        aliases=['setRules'],
        usage='<rules>'
    )
    @commands.has_permissions(administrator=True)
    async def set_rules(self, ctx, *rules: str):
        data = cogs._json.read_json('rules')
        new_rules = []
        if len(rules) == 1 and rules[0] == "__reset__":
            new_rules = self.bot.default_rules
        else:
            for rule in rules:
                if rule.replace("_", " ") not in new_rules:
                    new_rules.append(rule.replace("_", " "))
        data[str(ctx.message.guild.id)] = new_rules
        cogs._json.write_json(data, 'rules')

        channel = cogs._utils._get_log_channel(ctx)
        rules_string = "`"
        for i in range(len(new_rules)):
            rules_string += new_rules[i]
            if i < len(new_rules) - 2:
                rules_string += "`, `"
            elif i == len(new_rules) - 2:
                rules_string += "`, and `"
            rules_string += "`"
        embed = discord.Embed(title=f"{ctx.author.display_name} updated the rules",
                              description=f"The rules are now {rules_string}")
        await channel.send(embed=embed)


    @commands.command(
        name='rules',
        description='Says the rules for the current server',
        aliases=['get_rules', 'getRules', 'give_rules', 'giveRules', 'say_rules', 'sayRules'],
        usage=''
    )
    @commands.has_permissions(administrator=True)
    async def rules(self, ctx):
        data = cogs._json.read_json('rules')
        rules = data[str(ctx.message.guild.id)]

        channel = ctx.channel
        embed = discord.Embed(title=f"Rules",
                              description=f"The rules are:")
        for i in range(len(rules)):
            rule = rules[i]
            embed.add_field(name=str(i + 1), value=(str(i + 1) + ". " + rule))
        await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Misc(bot))
