import discord
from discord.ext import commands


class admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x36393F

    @commands.command(name="reload", description="리로드 명령어입니다.")
    @commands.is_owner()
    async def _reload(self, ctx: commands.Context, cog):
        reaction = ["✅", "⛔"]
        try:
            self.bot.reload_extension(cog)
            await ctx.message.add_reaction(emoji=reaction[0])

        except Exception as e:
            await ctx.reply(e)
            await ctx.message.add_reaction(emoji=reaction[1])

def setup(bot):
    bot.add_cog(admin(bot))
