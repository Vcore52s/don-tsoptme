import discord, os, configparser

from discord.ext import commands

config = configparser.ConfigParser()
config.read('./data/config.ini')

bot = commands.Bot(
    command_prefix="!", 
    help_command=None, 
    intents=discord.Intents.all(), 
)

@bot.event
async def on_ready():
    if __name__ == '__main__':
        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"[!] {filename[:-3]}이(가) 로딩되었습니다.")
        
        await bot.sync_commands()
        
        print("[!] 로딩이 완료되었습니다.")

if config["DEFAULT"]["token"] != "None":
    bot.run(config["DEFAULT"]["token"])

else:
    print("data/config.ini에 token을 수정해주세요.")