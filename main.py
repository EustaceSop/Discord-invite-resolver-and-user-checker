import discord
from discord import app_commands
from discord.ext import commands
import datetime
import aiohttp
import asyncio  #控制 Semaphore

#並行限制 防止同時太多人使用被擋
MAX_CONCURRENT_REQUESTS = 3 #限制同時只能3個請求
api_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

MESSAGES = {
    'zh-TW': {
        'success_title': "🔍 詳細用戶解析結果",
        'inviter': "👤 用戶名稱",
        'user_id': "🆔 用戶 ID",
        'created_at': "📅 帳號建立日期",
        'account_age': "🎂 帳號壽命",
        'other_info': "📊 其他資訊",
        'accent_color': "🎨 側邊欄顏色",
        'clan': "🏷️ 伺服器標籤 (Clan)",
        'decoration': "✨ 頭像裝飾框",
        'guild': "🏠 目標伺服器",
        'members': "人數: {count}",
        'badges': "🏅 持有勳章",
        'years': "年", 'days': "天",
        'footer_invite': "邀請碼: {code}",
        'footer_id': "查詢 ID: {id}",
        'cooldown': "⏳ 請求太快了！請等待 {time} 秒後再試一次。",
        'error_id': "❌ 無法找到 ID 為 `{id}` 的用戶。",
        'queue_full': "⚠️ 伺服器繁忙中，請稍後再試。"
    },
    'en-US': {
        'success_title': "🔍 Detailed User Lookup",
        'inviter': "👤 Username",
        'user_id': "🆔 User ID",
        'created_at': "📅 Created At",
        'account_age': "🎂 Account Age",
        'other_info': "📊 Other Info",
        'accent_color': "🎨 Accent Color",
        'clan': "🏷️ Clan / Guild Tag",
        'decoration': "✨ Avatar Decoration",
        'guild': "🏠 Target Server",
        'members': "Members: {count}",
        'badges': "🏅 Badges",
        'years': "y", 'days': "d",
        'footer_invite': "Invite: {code}",
        'footer_id': "ID Searched: {id}",
        'cooldown': "⏳ Too fast! Please wait {time}s.",
        'error_id': "❌ Could not find user with ID `{id}`.",
        'queue_full': "⚠️ Server is busy, please try again later."
    }
}

#勳章Flag
FLAGS = { 1 << 0: "Staff", 1 << 1: "Partner", 1 << 2: "HypeSquad Events", 1 << 3: "Bug Hunter Lvl 1", 1 << 6: "Bravery", 1 << 7: "Brilliance", 1 << 8: "Balance", 1 << 9: "Early Supporter", 1 << 14: "Bug Hunter Lvl 2", 1 << 17: "Verified Dev", 1 << 22: "Active Developer" }

def get_msg(locale, key):
    lang = str(locale) if str(locale) in MESSAGES else 'en-US'
    if lang.startswith('zh'): lang = 'zh-TW'
    return MESSAGES[lang][key]

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()

#獨立出來讓兩個指令都能優雅調用
async def fetch_and_send_user_info(interaction, user_id, extra_data=None):
    locale = interaction.locale
    headers = {"Authorization": f"Bot {bot.http.token}"}

    async with api_semaphore:
        async with aiohttp.ClientSession() as session:
            #get profile
            async with session.get(f"https://discord.com/api/v10/users/{user_id}", headers=headers) as res:
                if res.status != 200:
                    await interaction.followup.send(get_msg(locale, 'error_id').format(id=user_id))
                    return
                u = await res.json()

            #處理資料和嵌入介面排版
            created_ts = int(((int(user_id) >> 22) + 1420070400000) / 1000)
            delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(created_ts)
            age_str = f"{delta.days // 365}{get_msg(locale, 'years')} {delta.days % 365}{get_msg(locale, 'days')}"
            user_badges = [name for mask, name in FLAGS.items() if u.get('public_flags', 0) & mask]

            embed = discord.Embed(title=get_msg(locale, 'success_title'), description=u.get('bio', ''), color=u.get('accent_color') or 0x5865F2)
            embed.add_field(name=get_msg(locale, 'inviter'), value=f"**{u['username']}**", inline=True)
            embed.add_field(name=get_msg(locale, 'user_id'), value=f"`{user_id}`", inline=True)
            embed.add_field(name=get_msg(locale, 'account_age'), value=f"`{age_str}`", inline=True)
            embed.add_field(name=get_msg(locale, 'created_at'), value=f"<t:{created_ts}:F> (<t:{created_ts}:R>)", inline=False)
            if user_badges: embed.add_field(name=get_msg(locale, 'badges'), value="`" + "`, `".join(user_badges) + "`", inline=False)
            
            if extra_data:
                guild = extra_data.get('guild', {})
                count = extra_data.get('approximate_member_count', 'N/A')
                embed.add_field(name=get_msg(locale, 'guild'), value=f"**{guild.get('name')}**\n({get_msg(locale, 'members').format(count=count)})", inline=False)
                embed.set_footer(text=get_msg(locale, 'footer_invite').format(code=extra_data['code']))
            else:
                embed.set_footer(text=get_msg(locale, 'footer_id').format(id=user_id))

            #頭像和頭像框顯示
            avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{u.get('avatar')}.png?size=1024"
            embed.set_thumbnail(url=avatar_url)
            deco = u.get('avatar_decoration_data')
            if deco:
                deco_url = f"https://cdn.discordapp.com/avatar-decoration-presets/{deco.get('asset')}.png"
                embed.add_field(name=get_msg(locale, 'decoration'), value=f"[Decoration]({deco_url})", inline=True)
            banner = u.get('banner')
            if banner: embed.set_image(url=f"https://cdn.discordapp.com/banners/{user_id}/{banner}.png?size=1024")

            await interaction.followup.send(embed=embed)

#以下是指令
@bot.tree.command(name="lookup", description="Look up user info from an invite link")
@app_commands.describe(invite_url="Enter the invite URL or code")
@app_commands.checks.cooldown(1, 60.0, key=lambda i: (i.user.id))
async def lookup(interaction: discord.Interaction, invite_url: str):
    await interaction.response.defer(ephemeral=True)
    invite_code = invite_url.split('/')[-1]
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://discord.com/api/v10/invites/{invite_code}?with_counts=true") as res:
            if res.status != 200:
                await interaction.followup.send("❌ Invalid Invite.")
                return
            inv_data = await res.json()
            inv_data['code'] = invite_code
    user_id = inv_data.get('inviter', {}).get('id')
    if not user_id: return await interaction.followup.send("⚠️ No inviter found.")
    await fetch_and_send_user_info(interaction, user_id, inv_data)

@bot.tree.command(name="id_lookup", description="Directly look up user info by User ID")
@app_commands.describe(user_id="Enter the Discord User ID")
@app_commands.checks.cooldown(1, 60.0, key=lambda i: (i.user.id))
async def id_lookup(interaction: discord.Interaction, user_id: str):
    await interaction.response.defer(ephemeral=True)
    if not user_id.isdigit(): return await interaction.followup.send("❌ ID must be digits.")
    await fetch_and_send_user_info(interaction, user_id)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        msg = get_msg(interaction.locale, 'cooldown').format(time=f"{error.retry_after:.1f}")
        await interaction.response.send_message(msg, ephemeral=True)

bot.run('token')
