from discord.ext import commands
import discord
import random
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
                    role = discord.utils.get(member.guild.roles, id=int(str(member.guild.id)))
                else:
                    role = discord.utils.get(member.guild.roles, name="Muted")
                if role:
                    await member.add_roles(role)
        except KeyError:
            pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            data = cogs._json.read_json('filtered_words')
            if not str(message.guild.id) in data:
                filtered_words = self.bot.default_filtered_messages
            else:
                filtered_words = data[str(message.guild.id)]

            deleted = False

            for word in filtered_words:
                if (word.lower() in message.content.lower() or word.lower().replace(" ", "") in message.content.lower().replace(" ", "")) and not deleted:
                    await message.delete()
                    deleted = True

        await self.bot.process_commands(message)


def setup(bot):
    bot.add_cog(Events(bot))
