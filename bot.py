import os
import discord
from discord import app_commands

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True


class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


bot = MyBot()


@bot.event
async def on_ready():
    print(f"로그인 완료: {bot.user}")


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    if message.content == "안녕":
        await message.channel.send(f"안녕하세요, {message.author.display_name}님!")


@bot.tree.command(name="ping", description="봇이 살아있는지 확인해요")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"퐁! {round(bot.latency * 1000)}ms")


@bot.tree.command(name="주사위", description="주사위를 굴려요")
@app_commands.describe(sides="주사위 면의 개수 (기본 6)")
async def dice(interaction: discord.Interaction, sides: app_commands.Range[int, 2, 1000] = 6):
    import random
    await interaction.response.send_message(f"🎲 {sides}면 주사위 결과: **{random.randint(1, sides)}**")


@bot.tree.command(name="서버정보", description="이 서버의 정보를 보여줘요")
@app_commands.guild_only()
async def server_info(interaction: discord.Interaction):
    g = interaction.guild
    embed = discord.Embed(title=g.name, color=discord.Color.blurple())
    embed.add_field(name="멤버 수", value=str(g.member_count))
    embed.add_field(name="생성일", value=g.created_at.strftime("%Y-%m-%d"))
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="내정보", description="내 계정 정보를 보여줘요")
@app_commands.guild_only()
async def my_info(interaction: discord.Interaction):
    m = interaction.user
    embed = discord.Embed(title=m.display_name, color=discord.Color.green())
    embed.set_thumbnail(url=m.display_avatar.url)
    embed.add_field(name="계정 생성일", value=m.created_at.strftime("%Y-%m-%d"))
    if m.joined_at:
        embed.add_field(name="서버 가입일", value=m.joined_at.strftime("%Y-%m-%d"))
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="따라해", description="[관리자] 입력한 말을 봇이 대신 말해요")
@app_commands.describe(text="봇이 할 말")
@app_commands.default_permissions(administrator=True)
@app_commands.guild_only()
async def echo(interaction: discord.Interaction, text: str):
    await interaction.channel.send(text, allowed_mentions=discord.AllowedMentions.none())
    await interaction.response.send_message("전송했어요.", ephemeral=True)


@bot.tree.command(name="채팅기록", description="채널의 최근 메시지를 확인해요 (나만 보임)")
@app_commands.describe(channel="조회할 채널", 개수="가져올 메시지 수 (최대 25)")
@app_commands.guild_only()
async def chat_history(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    개수: app_commands.Range[int, 1, 25] = 10,
):
    await interaction.response.defer(ephemeral=True)
    lines = []
    async for msg in channel.history(limit=개수):
        ts = msg.created_at.strftime("%m-%d %H:%M")
        content = msg.content or "(첨부파일/임베드)"
        lines.append(f"`{ts}` **{msg.author.display_name}**: {content}")

    if not lines:
        await interaction.followup.send("메시지가 없어요.", ephemeral=True)
        return

    text = "\n".join(reversed(lines))
    if len(text) > 3900:
        text = text[:3900] + "\n...(생략)"
    embed = discord.Embed(title=f"#{channel.name} 최근 메시지", description=text, color=discord.Color.orange())
    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="감사로그", description="최근 감사 로그를 확인해요 (나만 보임)")
@app_commands.describe(개수="가져올 로그 수 (최대 25)")
@app_commands.guild_only()
async def audit_log(interaction: discord.Interaction, 개수: app_commands.Range[int, 1, 25] = 10):
    await interaction.response.defer(ephemeral=True)
    lines = []
    async for entry in interaction.guild.audit_logs(limit=개수):
        ts = entry.created_at.strftime("%m-%d %H:%M")
        target = getattr(entry.target, "name", entry.target)
        lines.append(f"`{ts}` **{entry.user}** → {entry.action.name} ({target})")

    if not lines:
        await interaction.followup.send("감사 로그가 없어요.", ephemeral=True)
        return

    text = "\n".join(lines)
    if len(text) > 3900:
        text = text[:3900] + "\n...(생략)"
    embed = discord.Embed(title="최근 감사 로그", description=text, color=discord.Color.red())
    await interaction.followup.send(embed=embed, ephemeral=True)


bot.run(TOKEN)