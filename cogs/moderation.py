from discord.ext import commands
import discord
import random
import os
import json

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
        
    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await ctx.guild.kick(user=member, reason=reason)
        
        channel = self._get_log_channel(ctx)
        embed = discord.Embed(title=f"{ctx.author.name} kicked {member.name}", description=reason)
        await channel.send(embed=embed)
        
    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        await ctx.guild.ban(user=member, reason=reason)
        
        channel = self._get_log_channel(ctx)
        embed = discord.Embed(title=f"{ctx.author.name} banned {member.name}", description=reason)
        await channel.send(embed=embed)
        
    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self, ctx, member, *, reason=None):
        member = await self.bot.fetch_user(int(member))
        await ctx.guild.unban(user=member, reason=reason)
        
        channel = self._get_log_channel(ctx)
        embed = discord.Embed(title=f"{ctx.author.name} unbanned {member.name}", description=reason)
        await channel.send(embed=embed)
            
    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def purge(self, ctx, amount=15):
        await ctx.channel.purge(limit=amount+1)
        
        channel = self._get_log_channel(ctx)
        embed = discord.Embed(title=f"{ctx.author.name} purged {ctx.channel}", description=f"{amount} messages were cleared")
        await channel.send(embed=embed)
        
    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def set_log_channel(self, ctx, channel: discord.TextChannel):
        self._set_log_channel(ctx, channel.name)
        embed = discord.Embed(title=f"{ctx.author.name} changed the log channel", description=f"{ctx.author.name} changed the log channel to <#{self._get_log_channel(ctx).id}>")
        await self._get_log_channel(ctx).send(embed=embed)

    def _set_log_channel(self, ctx, name):
        with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'w+') as f:
            data = self._get_data(ctx)
            data[ctx.guild.name] = {
                "log_channel_name": name
            }
            
            json.dump(data, f)
            
    def _get_data(self, ctx):
        if os.path.exists(os.path.join(os.path.dirname(__file__), 'config.json')):
            with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r') as f:
                return json.load(f)
        else:
            with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'w+') as f:
                json.dump({}, f)
            return {}
            
    def _get_log_channel(self, ctx):
        return discord.utils.get(ctx.guild.channels, self._get_log_channel_name(ctx))
            
    def _get_log_channel_name(self, ctx):
        if ctx.guild.name in self._get_data(ctx):
            return self._get_data(ctx)[ctx.guild.name]['log_channel_name']
        else:
            return 'general'

def setup(bot):
    bot.add_cog(Moderation(bot))
