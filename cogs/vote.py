import discord, sqlite3, datetime

from discord.ext import commands
from discord.commands import Option

from discord.ui import Modal, InputText, Button, View, Select

class closeButton(Button):
    def __init__(self, id: int | None, disable: bool = False):
        self.id = id
        self.color = 0x36393F

        super().__init__(label=f"투표 종료", custom_id=f"{id}:close", style=discord.ButtonStyle.red, row=2, disabled=disable)
                
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator == True:
            con = sqlite3.connect("./data/vote.db", isolation_level=None)
            cur = con.cursor()
            
            cur.execute("SELECT * FROM voteList WHERE id = ?", (self.id,))
            voteList = cur.fetchone()
            
            view=View()

            view.add_item(voteSelect(None, voteList[2], disable=True))
            view.add_item(closeButton(None, disable=True))

            await interaction.response.edit_message(view=view)                
            
        
            beforeEmbed = interaction.message.embeds[0]

            if voteList[3] == "공개": 
                embed = discord.Embed(title="투표 결과 [유저]", description="투표자 보호를 위해 종료자 본인만 확인할 수 있어요!", color=self.color)
            
                for c in range(len(beforeEmbed.fields)):
                    cur.execute("SELECT vote FROM voteStatus WHERE id = ? and vote = ?", (self.id, c)) 
                    rows = cur.fetchall() 

                    userList = []
                    
                    for _ in rows:
                        cur.execute("SELECT user FROM voteStatus WHERE id = ? and vote = ?", (self.id, c)) 
                        rows = cur.fetchall()
                        
                    for i in rows:
                        userList.append(f"<@{i[0]}>\n")
                    
                    embed.add_field(name=beforeEmbed.fields[c].name, value=f"".join(userList if userList != [] else "없음"), inline=False)
                    await interaction.followup.send(embed=embed, ephemeral=True)
            
            cur.execute("SELECT * FROM voteList WHERE id = ?", (self.id,)) 
            _voteList = cur.fetchall() 
            
            for c in range(len(beforeEmbed.fields)):
                cur.execute("SELECT * FROM voteStatus WHERE id = ? and vote = ?", (self.id, c)) 
                rows = cur.fetchall() 

                percent = int(len(rows) / len(_voteList) * 100) if len(rows) != 0 else 0

                beforeEmbed.set_field_at(index=c, name=beforeEmbed.fields[c].name, value=f"{len(rows)}명 투표 (`{percent}%`)", inline=False)
        
            await interaction.followup.send(embed=beforeEmbed)
        
            embed = discord.Embed(title="안내 드립니다.", description="일부 데이터가 현재 DB에 저장되어 있습니다.", color = self.color)

            embed.add_field(name="Q. 저장하는 이유와 대상은 무엇인가요?", value="A. 투표 정보(유저X)가 투표 저장 버튼 사용을 위해 저장됩니다.", inline=False)
            embed.add_field(name="Q. 데이터 삭제는 언제 되나요?", value="A. 해당 서버에서 봇이 탈퇴하면 자동으로 삭제됩니다.", inline=False)
            
            embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            cur.execute("UPDATE voteList SET voteStatus = ? WHERE id = ?", ("false", self.id))
            cur.execute("DELETE FROM voteStatus WHERE id = ?", (self.id,))
            con.close()
            
        else:
            return await interaction.response.send_message("어드민 전용 버튼입니다.", ephemeral=True)
        
class voteSelect(Select):
    def __init__(self, id: int | None, count: int, disable: bool = False):
        self.id = id
        
        options = []

        for i in range(count):
            options.append(
                discord.SelectOption(label=f"{i+1}번 투표하기", value=str(i), description=f"{i+1}을 투표 하시려면 클릭해주세요.")
            )

        super().__init__(placeholder="투표 하려면 클릭해주세요!", options=options, custom_id=f"{id}:{count}", row=1, disabled=disable)
                
    async def callback(self, interaction: discord.Interaction):
        con = sqlite3.connect("./data/vote.db", isolation_level=None)
        cur = con.cursor()
        
        cur.execute("SELECT vote FROM voteStatus WHERE id = ? and user = ?", (self.id, interaction.user.id))
        rows = cur.fetchone()
        if rows:
            cur.execute("UPDATE voteStatus SET vote = ? WHERE id = ? AND user = ?", (self.values[0], self.id, interaction.user.id))
            
        else:
            cur.execute("INSERT INTO voteStatus(id, vote, user) VALUES (?, ?, ?)", (self.id, self.values[0], interaction.user.id))
            
        embed = interaction.message.embeds[0]
        
        for c in range(len(interaction.message.embeds[0].fields)):
            cur.execute("SELECT vote FROM voteStatus WHERE id = ? and vote = ?", (self.id, c)) 
            rows = cur.fetchall()

            embed.set_field_at(index=c, name=embed.fields[c].name, value=f"{len(rows)}명 투표", inline=False)
        
        await interaction.response.edit_message(embed=embed)
        con.close()

class voteModal(Modal):
    def __init__(self, count: int, private_use: str) -> None:
        super().__init__(title="투표 작성 창")
        
        self.private_use = private_use
        
        self.voteCount = count
        self.color = 0x36393F
        
        itemList = [
            InputText(label="설명", placeholder="투표 설명을 입력해주세요.", style=discord.InputTextStyle.long)
        ]
        
        for i in range(count):
            itemList.append(
                InputText(label=f"{i+1}번 투표(항목)", placeholder=f"{i+1}번째 투표 항목을 입력해주세요.")
            )
        
        for c in range(len(itemList)):
            self.add_item(itemList[c])
            
    async def callback(self, interaction: discord.Interaction):
        con = sqlite3.connect("./data/vote.db", isolation_level=None)
        cur = con.cursor()

        embed = discord.Embed(description=self.children[0].value, color=self.color)
        view = View(timeout=None)
        
        cur.execute("INSERT INTO voteList(guild, maxNumber, privateUse, voteStatus) VALUES (?, ?, ?, ?)", (interaction.guild.id, self.voteCount, self.private_use, "true"))
        
        cur.execute("SELECT LAST_INSERT_ROWID() AS id")
        rows = cur.fetchone()
        
        for i in range(self.voteCount):
            embed.add_field(name=f">>> {self.children[i+1].value}", value="0명 투표", inline=False)
            
        view.add_item(voteSelect(id=rows[0], count=self.voteCount))
            
        view.add_item(closeButton(rows[0]))
            
        embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed, view=view)
        con.close()

class vote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x36393F

    async def getID(self, ctx:discord.AutocompleteContext):
        con = sqlite3.connect("./data/vote.db", isolation_level=None)
        cur = con.cursor()

        cur.execute("SELECT * FROM voteList WHERE guild = ? and votStatus = ?", (ctx.interaction.guild.id, "true"))
        rows = cur.fetchall()
        
        
        con.close()
        return [i[0] for i in rows]
        
    @commands.slash_command(name="투표", description="투표를 생성해요.")
    @discord.default_permissions(administrator=True)
    async def _createVote(
        self,
        ctx:discord.ApplicationContext,
        count:Option(int, name="개수", description="투표 목록 개수를 입력해주세요. (최대 4개, 생성 후 추가 가능)", min_value=1, max_value=4),
        private_use:Option(str, name="상태", description="투표 상태를 선택해주세요.", choices=["공개", "비공개"], required=False, default="비공개")
    ):
        await ctx.send_modal(voteModal(count, private_use))

def bot_start(bot: commands.Bot):
    con = sqlite3.connect("./data/vote.db", isolation_level=None)
    cur = con.cursor()
    
    cur.execute("CREATE TABLE IF NOT EXISTS voteList(id INTEGER PRIMARY KEY AUTOINCREMENT, guild INTEGER NOT NULL, maxNumber INTEGER NOT NULL, privateUse TEXT NOT NULL, voteStatus TEXT NOT NULL)")
    cur.execute("CREATE TABLE IF NOT EXISTS voteStatus(id INTEGER NOT NULL, vote INTEGER NOT NULL, user INTEGER NOT NULL)")
    
    for i in bot.guilds:
        cur.execute("SELECT * FROM voteList WHERE guild = ?", (i.id,))
        rows =  cur.fetchall()
        
        for i in rows:
            defaultView = View(timeout=None) 

            defaultView.add_item(voteSelect(i[0], i[2]))
            defaultView.add_item(closeButton(i[0]))

            bot.add_view(defaultView)
        
    con.close()
    
def setup(bot):
    bot_start(bot)

    bot.add_cog(vote(bot))