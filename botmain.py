from discord.ext import commands
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from os import urandom
from datetime import datetime, timedelta
from discord.utils import get
import discord
import random

# Intents設定
intents = discord.Intents.default()
intents.members = True  # メンバー管理の権限
intents.message_content = True  # メッセージの内容を取得する権限

# Botをインスタンス化
bot = commands.Bot(
    command_prefix="$",  # $コマンド名 でコマンドを実行できるようになる
    case_insensitive=True,  # コマンドの大文字小文字を区別しない
    intents=intents  # 権限を設定
)

# AES暗号化用のキー
aes_key = urandom(32)  # 256ビットキー

# 管理者のID
OWNER_ID = 959378199895212043
# BAN ID
TARGET_USER_ID = 966448197310504970
# StartChannelID
CHANNEL_ID = 1321266748506243113
# ROLL ID
ROLE_ID = 1322869157070377003

# Bot起動時のイベント
@bot.event
async def on_ready():
    print(f"discord.py version: {discord.__version__} bot ok owner_id = {OWNER_ID}")
    await bot.tree.sync()
    await greet()

async def greet():
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print(f"Error: チャンネル ID {CHANNEL_ID} が見つかりません。")
        return

    await channel.send("こんにちは！ボットが起動しました。")
  

# メンバー参加時のイベント
@bot.event
async def on_member_join(member):
    embed = discord.Embed(
        title=f"{member.name}さん、参加してくれてありがとう。",
        color=0x00ffff
    )
    channel = discord.utils.get(member.guild.text_channels, name="ようこそ")
    if channel:
        await channel.send(embed=embed)

    # 特定のIDの場合にキックする処理
    target_ids = [1234567890]
    if member.id in target_ids:
        try:
            await member.ban(reason="特定のIDのため自動キックされました。")
            if channel:
                await channel.send(f"{member.name} さんは特定のIDのためキックされました。")
        except discord.Forbidden:
            if channel:
                await channel.send(f"{member.name} さんをキックできませんでした（権限不足）。")
        except Exception as e:
            if channel:
                await channel.send(f"{member.name} さんをキック中にエラーが発生しました: {e}")
#botがサーバに参加した時のイベント
@bot.event
async def on_guild_join(guild):
    # メッセージを送信するためのチャンネルを探す
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send(f"bot追加ありがとー！よかったらサポートサーバー来てね！質問とか色々できるよ！https://discord.gg/qX4M83SZ9g")
            break

# AES暗号化コマンド
@bot.command()
async def aes_encrypt(ctx: commands.Context, *, text: str):
    iv = urandom(16)
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    padding_length = 16 - (len(text.encode("utf-8")) % 16)
    padded_data = text.encode("utf-8") + bytes([padding_length] * padding_length)

    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    await ctx.send(f"暗号化結果: `{iv.hex()}:{encrypted_data.hex()}`")

# AES復号化コマンド
@bot.command()
async def aes_decrypt(ctx: commands.Context, *, hex_data: str):
    try:
        iv, encrypted_data = hex_data.split(":")
        iv = bytes.fromhex(iv)
        encrypted_data = bytes.fromhex(encrypted_data)

        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        decrypted_padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        padding_length = decrypted_padded_data[-1]
        decrypted_data = decrypted_padded_data[:-padding_length].decode("utf-8")

        await ctx.send(f"復号化結果: `{decrypted_data}`")
    except Exception as e:
        await ctx.send(f"エラーが発生しました: {e}")

# オーナーチェック関数
def is_owner(interaction: discord.Interaction):
    return interaction.user.id == OWNER_ID

# 挨拶コマンド
@bot.tree.command(name='hello', description='挨拶')
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.name}")

# ダイスコマンド
@bot.tree.command(name='1d100', description='100面ダイス')
async def d100(interaction: discord.Interaction):
    result = random.randint(1, 100)
    await interaction.response.send_message(f"🎲 100面ダイス: {result}")

# 足し算コマンド
@bot.command()
async def add(ctx: commands.Context, a: int, b: int):
    await ctx.send(a + b)

# メッセージ履歴取得コマンド
@bot.command()
async def get_message(ctx: commands.Context, channel: discord.TextChannel):
    with open("messages.txt", "w", encoding="utf-8") as file:
        async for message in channel.history(
            after=datetime.utcnow() - timedelta(hours=1),
            oldest_first=True,
        ):
            jst = message.created_at + timedelta(hours=9)
            file.write(f"{message.author.name}: {jst.strftime('%Y/%m/%d %H:%M:%S')}\n{message.content}\n\n")

    await ctx.send(file=discord.File("messages.txt"))

# Botを実行
bot.run()
