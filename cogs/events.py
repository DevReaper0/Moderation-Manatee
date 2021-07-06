from discord.ext import commands
import discord
import random
import datetime
import cogs._json
import cogs._utils

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            if self.bot.muted_users[member.id]:
                roles = cogs._json.read_json('muted_roles')

                if str(member.guild.id) in roles:
                    role = discord.utils.get(member.guild.roles, id=int(str(roles[str(member.guild.id)])))
                else:
                    role = discord.utils.get(member.guild.roles, name="Muted")
                if role:
                    await member.add_roles(role)
        except KeyError:
            pass

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.bot.handler.propagate(message)

        if self.bot.tracker.is_spamming(message):
            roles = cogs._json.read_json('muted_roles')

            if self.bot.tracker.get_user_count(message) == 1:
                if message.author.id in [message.author.id, self.bot.user.id]:
                    return await message.send("You cannot warn yourself or the bot!")

                current_warn_count = len(
                    await self.bot.warns.find_many_by_custom(
                        {
                            "user_id": message.author.id,
                            "guild_id": message.guild.id
                        }
                    )
                ) + 1

                warn_filter = {"user_id": message.author.id, "guild_id": message.guild.id, "number": current_warn_count}
                warn_data = {"reason": "Spamming", "timestamp": message.created_at, "warned_by": message.author.id}

                await self.bot.warns.upsert_custom(warn_filter, warn_data)

                embed = discord.Embed(
                    title="You are being warned:",
                    description=f"__**Reason**__:\nSpamming",
                    color=discord.Color.red(),
                    timestamp=message.created_at
                )
                embed.set_author(name=message.guild.name, icon_url=message.guild.icon_url)
                embed.set_footer(text=f"Warn: {current_warn_count}")

                try:
                    await message.author.send(embed=embed)
                    await message.send("Warned that user in dm's for you.")
                except discord.HTTPException:
                    await message.send(message.author.mention, embed=embed)
            elif self.bot.tracker.get_user_count(message) == 2:
                if str(message.guild.id) in roles:
                    role = discord.utils.get(message.guild.roles, id=int(str(roles[str(message.guild.id)])))
                else:
                    role = discord.utils.get(message.guild.roles, name="Muted")

                data = {
                    '_id': message.author.id,
                    'mutedAt': datetime.datetime.now(),
                    'muteDuration': None,
                    'mutedBy': message.author.id,
                    'guildId': message.guild.id,
                }
                await self.bot.mutes.upsert(data)
                self.bot.muted_users[message.author.id] = data

                await message.author.add_roles(role)
            elif self.bot.tracker.get_user_count(message) == 3:
                await message.guild.kick(user=message.author, reason="Spamming")

            # ETC
            self.bot.tracker.remove_punishments(message)

        data = cogs._json.read_json('filtered_words')
        if message.guild is None or not str(message.guild.id) in data:
            filtered_words = self.bot.default_filtered_messages
        else:
            filtered_words = data[str(message.guild.id)]

        deleted = False

        for word in filtered_words:
            if (word.lower() in message.content.lower() or word.lower().replace(" ",
                                                                                "") in message.content.lower().replace(
                    " ", "")) and not message.author == self.bot.user and message.guild and not deleted:
                await message.delete()
                deleted = True

        data = cogs._json.read_json('muted_roles')
        if message.guild and str(message.guild.id) in data and discord.utils.get(message.guild.roles, id=int(str(data[str(message.guild.id)]))) in message.author.roles and not message.author.guild_permissions.administrator:
            await message.delete()


def setup(bot):
    bot.add_cog(Events(bot))
