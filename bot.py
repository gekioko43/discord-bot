import logging
import sys
import os
import discord
from discord.ext import commands
from discord.ui import View, Button
from dotenv import load_dotenv

# --- 📜 ログ設定 ---
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.info("Bot is starting...")

# --- 📤 標準出力ログ保存（オプション）---
sys.stdout = open('stdout.log', 'a')
sys.stderr = open('stderr.log', 'a')

# --- 📦 環境変数読み込み ---
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# --- ⚙️ Bot設定 ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- 🔧 定数 ---
AGREE_ROLE_NAME = "当事者"
INTRO_CHANNEL_ID = 1392100464870424597  # #はじめに
CHAT_CHANNEL_ID = 1392000861605072917   # #会話部屋
ARCHIVE_CHANNEL_ID = 1391977518147305614  # #保存用（←あなたの環境に合わせて！）

# --- ✅ 同意ビュー定義 ---
class AgreeView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="同意する", style=discord.ButtonStyle.success, custom_id="agree_button")
    async def agree_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name=AGREE_ROLE_NAME)
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("✅ 会話部屋へどうぞ", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ ロールが見つかりません。", ephemeral=True)

# --- ✅ Bot起動時処理 ---
@bot.event
async def on_ready():
    print(f"✅ ログインしました: {bot.user}")
    bot.add_view(AgreeView())  # 永続ビューの登録

# --- ✅ コマンド：任意で同意ボタンを送信 ---
@bot.command()
@commands.has_permissions(administrator=True)
async def send_agree_button(ctx):
    channel = bot.get_channel(INTRO_CHANNEL_ID)
    if channel:
        await channel.send(
            "📜 利用規約に同意する場合は下のボタンを押してください。",
            view=AgreeView()
        )
        await ctx.send("✅ 同意ボタンを送信しました。")
    else:
        await ctx.send("⚠️ チャンネルが見つかりません。")

@send_agree_button.error
async def send_agree_button_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("⚠️ 管理者権限が必要です。")
    else:
        await ctx.send(f"❌ エラー: {error}")

# --- 📦 メッセージ転送（会話部屋 → 保存用） ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == CHAT_CHANNEL_ID:
        archive_channel = bot.get_channel(ARCHIVE_CHANNEL_ID)
        if archive_channel:
            content = f"**{message.author.display_name}**: {message.content}"

            # 添付ファイルがあれば一緒に送信
            if message.attachments:
                files = []
                for attachment in message.attachments:
                    try:
                        file = await attachment.to_file()
                        files.append(file)
                    except Exception as e:
                        print(f"ファイル読み込みエラー: {e}")
                await archive_channel.send(content if content.strip() else "【ファイルのみ】", files=files)
            else:
                await archive_channel.send(content)

    await bot.process_commands(message)

# --- ✅ Bot起動 ---
bot.run(TOKEN)
