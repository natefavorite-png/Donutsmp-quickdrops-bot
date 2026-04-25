import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
from datetime import datetime, timedelta, timezone

CONFIG_FILE = “config.json”

def load_config():
if not os.path.exists(CONFIG_FILE):
return {}
with open(CONFIG_FILE, “r”) as f:
return json.load(f)

def save_config(data):
with open(CONFIG_FILE, “w”) as f:
json.dump(data, f, indent=4)

def get_guild_config(guild_id):
config = load_config()
gid = str(guild_id)
if gid not in config:
config[gid] = {}
return config, gid

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=”!”, intents=intents)

@bot.event
async def on_ready():
print(“Logged in as “ + str(bot.user))
try:
synced = await bot.tree.sync()
print(“Synced “ + str(len(synced)) + “ commands.”)
except Exception as e:
print(“Sync error: “ + str(e))
await bot.change_presence(activity=discord.Activity(
type=discord.ActivityType.watching, name=“your server”
))

@bot.event
async def on_member_join(member):
config, gid = get_guild_config(member.guild.id)
cfg = config.get(gid, {})

```
welcome_channel_id = cfg.get("welcome_channel")
if welcome_channel_id:
    channel = member.guild.get_channel(int(welcome_channel_id))
    if channel:
        welcome_msg = cfg.get(
            "welcome_message",
            "Welcome to {server}, {user}! You are member #{count}."
        )
        welcome_msg = welcome_msg.replace("{user}", member.mention)
        welcome_msg = welcome_msg.replace("{username}", member.display_name)
        welcome_msg = welcome_msg.replace("{server}", member.guild.name)
        welcome_msg = welcome_msg.replace("{count}", str(member.guild.member_count))
        embed = discord.Embed(description=welcome_msg, color=discord.Color.green(), timestamp=datetime.now(timezone.utc))
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

auto_role_id = cfg.get("auto_role")
if auto_role_id:
    role = member.guild.get_role(int(auto_role_id))
    if role:
        try:
            await member.add_roles(role, reason="Auto-role on join")
        except discord.Forbidden:
            pass
```

@bot.event
async def on_member_remove(member):
config, gid = get_guild_config(member.guild.id)
cfg = config.get(gid, {})
leave_channel_id = cfg.get(“leave_channel”)
if leave_channel_id:
channel = member.guild.get_channel(int(leave_channel_id))
if channel:
leave_msg = cfg.get(
“leave_message”,
“{username} has left the server. We now have {count} members.”
)
leave_msg = leave_msg.replace(”{username}”, member.display_name)
leave_msg = leave_msg.replace(”{server}”, member.guild.name)
leave_msg = leave_msg.replace(”{count}”, str(member.guild.member_count))
embed = discord.Embed(description=leave_msg, color=discord.Color.red(), timestamp=datetime.now(timezone.utc))
embed.set_thumbnail(url=member.display_avatar.url)
await channel.send(embed=embed)

setup_group = app_commands.Group(name=“setup”, description=“Configure bot systems”)

@setup_group.command(name=“welcome”, description=“Set the welcome channel and message”)
@app_commands.describe(channel=“Channel for welcome messages”, message=“Use {user} {username} {server} {count}”)
@app_commands.checks.has_permissions(administrator=True)
async def setup_welcome(interaction, channel: discord.TextChannel, message: str = None):
config, gid = get_guild_config(interaction.guild.id)
config[gid][“welcome_channel”] = str(channel.id)
if message:
config[gid][“welcome_message”] = message
save_config(config)
await interaction.response.send_message(“Welcome channel set to “ + channel.mention, ephemeral=True)

@setup_group.command(name=“leave”, description=“Set the leave channel and message”)
@app_commands.describe(channel=“Channel for leave messages”, message=“Use {username} {server} {count}”)
@app_commands.checks.has_permissions(administrator=True)
async def setup_leave(interaction, channel: discord.TextChannel, message: str = None):
config, gid = get_guild_config(interaction.guild.id)
config[gid][“leave_channel”] = str(channel.id)
if message:
config[gid][“leave_message”] = message
save_config(config)
await interaction.response.send_message(“Leave channel set to “ + channel.mention, ephemeral=True)

@setup_group.command(name=“autorole”, description=“Give a role to every new member”)
@app_commands.describe(role=“Role to assign on join”)
@app_commands.checks.has_permissions(administrator=True)
async def setup_autorole(interaction, role: discord.Role):
config, gid = get_guild_config(interaction.guild.id)
config[gid][“auto_role”] = str(role.id)
save_config(config)
await interaction.response.send_message(“Auto-role set to “ + role.mention, ephemeral=True)

@setup_group.command(name=“logs”, description=“Set a channel for moderation logs”)
@app_commands.describe(channel=“Channel for mod logs”)
@app_commands.checks.has_permissions(administrator=True)
async def setup_logs(interaction, channel: discord.TextChannel):
config, gid = get_guild_config(interaction.guild.id)
config[gid][“log_channel”] = str(channel.id)
save_config(config)
await interaction.response.send_message(“Log channel set to “ + channel.mention, ephemeral=True)

bot.tree.add_command(setup_group)

class TicketCloseView(discord.ui.View):
def **init**(self):
super().**init**(timeout=None)

```
@discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
async def close_ticket(self, interaction, button):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("No permission to close tickets.", ephemeral=True)
        return
    await interaction.response.send_message("Closing ticket in 5 seconds...")
    await asyncio.sleep(5)
    await interaction.channel.delete(reason="Ticket closed by " + str(interaction.user))
```

class TicketOpenView(discord.ui.View):
def **init**(self):
super().**init**(timeout=None)

```
@discord.ui.button(label="Open a Ticket", style=discord.ButtonStyle.primary, custom_id="open_ticket")
async def open_ticket(self, interaction, button):
    guild = interaction.guild
    config, gid = get_guild_config(guild.id)
    cfg = config.get(gid, {})

    safe_name = interaction.user.name.lower().replace(" ", "-")
    for channel in guild.text_channels:
        if channel.name == "ticket-" + safe_name:
            await interaction.response.send_message("You already have an open ticket: " + channel.mention, ephemeral=True)
            return

    ticket_category_id = cfg.get("ticket_category")
    category = guild.get_channel(int(ticket_category_id)) if ticket_category_id else None

    support_role_id = cfg.get("ticket_support_role")
    support_role = guild.get_role(int(support_role_id)) if support_role_id else None

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
    }
    if support_role:
        overwrites[support_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

    channel = await guild.create_text_channel(
        name="ticket-" + safe_name,
        category=category,
        overwrites=overwrites,
        reason="Ticket opened by " + str(interaction.user)
    )

    embed = discord.Embed(
        title="Support Ticket",
        description="Welcome " + interaction.user.mention + "!\n\nA staff member will be with you shortly.\nPlease describe your issue.",
        color=discord.Color.blurple(),
        timestamp=datetime.now(timezone.utc)
    )
    content = interaction.user.mention
    if support_role:
        content = content + " | " + support_role.mention
    await channel.send(content=content, embed=embed, view=TicketCloseView())
    await interaction.response.send_message("Your ticket: " + channel.mention, ephemeral=True)
```

ticket_group = app_commands.Group(name=“ticket”, description=“Ticket system commands”)

@ticket_group.command(name=“setup”, description=“Configure ticket category and support role”)
@app_commands.describe(category=“Category for ticket channels”, support_role=“Role that can see tickets”)
@app_commands.checks.has_permissions(administrator=True)
async def ticket_setup(interaction, category: discord.CategoryChannel, support_role: discord.Role = None):
config, gid = get_guild_config(interaction.guild.id)
config[gid][“ticket_category”] = str(category.id)
if support_role:
config[gid][“ticket_support_role”] = str(support_role.id)
save_config(config)
msg = “Ticket category set to “ + category.name
if support_role:
msg = msg + “. Support role: “ + support_role.mention
await interaction.response.send_message(msg, ephemeral=True)

@ticket_group.command(name=“panel”, description=“Send the ticket panel to a channel”)
@app_commands.describe(channel=“Channel to post panel in”, title=“Panel title”, description=“Panel description”)
@app_commands.checks.has_permissions(administrator=True)
async def ticket_panel(interaction, channel: discord.TextChannel, title: str = “Support Tickets”, description: str = “Click the button below to open a support ticket.”):
embed = discord.Embed(title=title, description=description, color=discord.Color.blurple())
await channel.send(embed=embed, view=TicketOpenView())
await interaction.response.send_message(“Ticket panel sent to “ + channel.mention, ephemeral=True)

bot.tree.add_command(ticket_group)

class ApplicationModal(discord.ui.Modal):
def **init**(self, app_name, questions):
super().**init**(title=“Application: “ + app_name)
self.app_name = app_name
self.questions = questions
self.fields = []
for i, q in enumerate(questions[:5]):
field = discord.ui.TextInput(
label=q[:45],
style=discord.TextStyle.paragraph if i > 0 else discord.TextStyle.short,
required=True,
max_length=1000
)
self.add_item(field)
self.fields.append(field)

```
async def on_submit(self, interaction):
    config, gid = get_guild_config(interaction.guild.id)
    cfg = config.get(gid, {})
    apps = cfg.get("applications", {})
    app_cfg = apps.get(self.app_name, {})
    results_channel_id = app_cfg.get("results_channel")

    embed = discord.Embed(
        title="New Application: " + self.app_name,
        color=discord.Color.gold(),
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
    embed.add_field(name="Applicant", value=interaction.user.mention, inline=False)
    for i, field in enumerate(self.fields):
        q = self.questions[i] if i < len(self.questions) else "Question " + str(i + 1)
        embed.add_field(name=q, value=field.value or "No answer", inline=False)
    embed.set_footer(text="User ID: " + str(interaction.user.id))

    if results_channel_id:
        results_channel = interaction.guild.get_channel(int(results_channel_id))
        if results_channel:
            await results_channel.send(embed=embed, view=ApplicationReviewView(interaction.user.id))
            await interaction.response.send_message("Your application has been submitted!", ephemeral=True)
            return
    await interaction.response.send_message("Application submitted! No results channel configured yet.", ephemeral=True)
```

class ApplicationReviewView(discord.ui.View):
def **init**(self, applicant_id):
super().**init**(timeout=None)
self.applicant_id = applicant_id

```
@discord.ui.button(label="Accept", style=discord.ButtonStyle.success, custom_id="app_accept")
async def accept(self, interaction, button):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("No permission.", ephemeral=True)
        return
    member = interaction.guild.get_member(self.applicant_id)
    embed = interaction.message.embeds[0]
    embed.color = discord.Color.green()
    embed.set_footer(text="Accepted by " + str(interaction.user))
    await interaction.message.edit(embed=embed, view=None)
    if member:
        try:
            await member.send("Your application in " + interaction.guild.name + " has been accepted!")
        except Exception:
            pass
    await interaction.response.send_message("Application accepted.", ephemeral=True)

@discord.ui.button(label="Deny", style=discord.ButtonStyle.danger, custom_id="app_deny")
async def deny(self, interaction, button):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("No permission.", ephemeral=True)
        return
    member = interaction.guild.get_member(self.applicant_id)
    embed = interaction.message.embeds[0]
    embed.color = discord.Color.red()
    embed.set_footer(text="Denied by " + str(interaction.user))
    await interaction.message.edit(embed=embed, view=None)
    if member:
        try:
            await member.send("Your application in " + interaction.guild.name + " has been denied.")
        except Exception:
            pass
    await interaction.response.send_message("Application denied.", ephemeral=True)
```

class ApplicationButtonView(discord.ui.View):
def **init**(self, app_name, questions):
super().**init**(timeout=None)
self.app_name = app_name
self.questions = questions
btn = discord.ui.Button(label=“Apply for “ + app_name, style=discord.ButtonStyle.primary, custom_id=“apply_” + app_name)
btn.callback = self.apply_callback
self.add_item(btn)

```
async def apply_callback(self, interaction):
    modal = ApplicationModal(self.app_name, self.questions)
    await interaction.response.send_modal(modal)
```

app_group = app_commands.Group(name=“application”, description=“Application system commands”)

@app_group.command(name=“create”, description=“Create a new application”)
@app_commands.describe(name=“Application name”, results_channel=“Where applications are sent”, q1=“Question 1”, q2=“Question 2”, q3=“Question 3”, q4=“Question 4”, q5=“Question 5”)
@app_commands.checks.has_permissions(administrator=True)
async def application_create(interaction, name: str, results_channel: discord.TextChannel, q1: str, q2: str = None, q3: str = None, q4: str = None, q5: str = None):
questions = [q for q in [q1, q2, q3, q4, q5] if q]
config, gid = get_guild_config(interaction.guild.id)
if “applications” not in config[gid]:
config[gid][“applications”] = {}
config[gid][“applications”][name] = {
“questions”: questions,
“results_channel”: str(results_channel.id)
}
save_config(config)
await interaction.response.send_message(“Application “ + name + “ created with “ + str(len(questions)) + “ questions. Use /application panel to post it.”, ephemeral=True)

@app_group.command(name=“panel”, description=“Post an application panel”)
@app_commands.describe(name=“Application name”, channel=“Channel to post in”, title=“Panel title”, description=“Panel description”)
@app_commands.checks.has_permissions(administrator=True)
async def application_panel(interaction, name: str, channel: discord.TextChannel, title: str = None, description: str = None):
config, gid = get_guild_config(interaction.guild.id)
apps = config.get(gid, {}).get(“applications”, {})
if name not in apps:
await interaction.response.send_message(“No application named “ + name + “. Use /application create first.”, ephemeral=True)
return
questions = apps[name][“questions”]
embed = discord.Embed(
title=title or name + “ Application”,
description=description or “Click the button below to apply for “ + name + “.”,
color=discord.Color.blue()
)
await channel.send(embed=embed, view=ApplicationButtonView(name, questions))
await interaction.response.send_message(“Panel sent to “ + channel.mention, ephemeral=True)

@app_group.command(name=“list”, description=“List all applications”)
@app_commands.checks.has_permissions(administrator=True)
async def application_list(interaction):
config, gid = get_guild_config(interaction.guild.id)
apps = config.get(gid, {}).get(“applications”, {})
if not apps:
await interaction.response.send_message(“No applications yet. Use /application create.”, ephemeral=True)
return
embed = discord.Embed(title=“Applications”, color=discord.Color.blue())
for name, data in apps.items():
qs = “\n”.join(str(i + 1) + “. “ + q for i, q in enumerate(data[“questions”]))
embed.add_field(name=name, value=qs or “No questions”, inline=False)
await interaction.response.send_message(embed=embed, ephemeral=True)

@app_group.command(name=“delete”, description=“Delete an application”)
@app_commands.describe(name=“Application name to delete”)
@app_commands.checks.has_permissions(administrator=True)
async def application_delete(interaction, name: str):
config, gid = get_guild_config(interaction.guild.id)
apps = config.get(gid, {}).get(“applications”, {})
if name not in apps:
await interaction.response.send_message(“No application named “ + name, ephemeral=True)
return
del config[gid][“applications”][name]
save_config(config)
await interaction.response.send_message(“Application “ + name + “ deleted.”, ephemeral=True)

bot.tree.add_command(app_group)

async def log_action(guild, action, moderator, target, reason):
config, gid = get_guild_config(guild.id)
log_channel_id = config.get(gid, {}).get(“log_channel”)
if not log_channel_id:
return
channel = guild.get_channel(int(log_channel_id))
if not channel:
return
embed = discord.Embed(title=“Moderation: “ + action, color=discord.Color.orange(), timestamp=datetime.now(timezone.utc))
embed.add_field(name=“Target”, value=str(target) + “ (” + str(target.id) + “)”, inline=True)
embed.add_field(name=“Moderator”, value=str(moderator), inline=True)
embed.add_field(name=“Reason”, value=reason or “No reason provided”, inline=False)
await channel.send(embed=embed)

@bot.tree.command(name=“ban”, description=“Ban a member”)
@app_commands.describe(member=“Member to ban”, reason=“Reason”, delete_days=“Days of messages to delete 0-7”)
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction, member: discord.Member, reason: str = “No reason provided”, delete_days: int = 0):
if member.top_role >= interaction.user.top_role:
await interaction.response.send_message(“You cannot ban someone with equal or higher roles.”, ephemeral=True)
return
try:
await member.send(“You have been banned from “ + interaction.guild.name + “. Reason: “ + reason)
except Exception:
pass
await member.ban(reason=str(interaction.user) + “: “ + reason, delete_message_days=min(delete_days, 7))
await interaction.response.send_message(str(member) + “ has been banned. Reason: “ + reason)
await log_action(interaction.guild, “Ban”, interaction.user, member, reason)

@bot.tree.command(name=“unban”, description=“Unban a user by ID”)
@app_commands.describe(user_id=“User ID to unban”, reason=“Reason”)
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction, user_id: str, reason: str = “No reason provided”):
try:
user = await bot.fetch_user(int(user_id))
await interaction.guild.unban(user, reason=reason)
await interaction.response.send_message(str(user) + “ has been unbanned.”)
await log_action(interaction.guild, “Unban”, interaction.user, user, reason)
except Exception as e:
await interaction.response.send_message(“Could not unban: “ + str(e), ephemeral=True)

@bot.tree.command(name=“kick”, description=“Kick a member”)
@app_commands.describe(member=“Member to kick”, reason=“Reason”)
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction, member: discord.Member, reason: str = “No reason provided”):
if member.top_role >= interaction.user.top_role:
await interaction.response.send_message(“You cannot kick someone with equal or higher roles.”, ephemeral=True)
return
try:
await member.send(“You have been kicked from “ + interaction.guild.name + “. Reason: “ + reason)
except Exception:
pass
await member.kick(reason=str(interaction.user) + “: “ + reason)
await interaction.response.send_message(str(member) + “ has been kicked. Reason: “ + reason)
await log_action(interaction.guild, “Kick”, interaction.user, member, reason)

@bot.tree.command(name=“timeout”, description=“Timeout a member”)
@app_commands.describe(member=“Member to timeout”, minutes=“Duration in minutes”, reason=“Reason”)
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout_cmd(interaction, member: discord.Member, minutes: int, reason: str = “No reason provided”):
if member.top_role >= interaction.user.top_role:
await interaction.response.send_message(“You cannot timeout someone with equal or higher roles.”, ephemeral=True)
return
until = datetime.now(timezone.utc) + timedelta(minutes=minutes)
await member.timeout(until, reason=reason)
await interaction.response.send_message(str(member) + “ timed out for “ + str(minutes) + “ minutes. Reason: “ + reason)
await log_action(interaction.guild, “Timeout “ + str(minutes) + “m”, interaction.user, member, reason)

@bot.tree.command(name=“untimeout”, description=“Remove a timeout”)
@app_commands.describe(member=“Member to untimeout”)
@app_commands.checks.has_permissions(moderate_members=True)
async def untimeout_cmd(interaction, member: discord.Member):
await member.timeout(None)
await interaction.response.send_message(“Timeout removed from “ + str(member))
await log_action(interaction.guild, “Untimeout”, interaction.user, member, “Removed”)

@bot.tree.command(name=“warn”, description=“Warn a member”)
@app_commands.describe(member=“Member to warn”, reason=“Reason”)
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction, member: discord.Member, reason: str):
config, gid = get_guild_config(interaction.guild.id)
if “warnings” not in config[gid]:
config[gid][“warnings”] = {}
uid = str(member.id)
if uid not in config[gid][“warnings”]:
config[gid][“warnings”][uid] = []
config[gid][“warnings”][uid].append({
“reason”: reason,
“moderator”: str(interaction.user),
“timestamp”: datetime.now(timezone.utc).isoformat()
})
save_config(config)
count = len(config[gid][“warnings”][uid])
try:
await member.send(“You have been warned in “ + interaction.guild.name + “. Reason: “ + reason + “. Total warnings: “ + str(count))
except Exception:
pass
await interaction.response.send_message(str(member) + “ warned. Total warnings: “ + str(count) + “. Reason: “ + reason)
await log_action(interaction.guild, “Warn #” + str(count), interaction.user, member, reason)

@bot.tree.command(name=“warnings”, description=“View warnings for a member”)
@app_commands.describe(member=“Member to check”)
@app_commands.checks.has_permissions(manage_messages=True)
async def warnings(interaction, member: discord.Member):
config, gid = get_guild_config(interaction.guild.id)
warns = config.get(gid, {}).get(“warnings”, {}).get(str(member.id), [])
if not warns:
await interaction.response.send_message(str(member) + “ has no warnings.”, ephemeral=True)
return
embed = discord.Embed(title=“Warnings for “ + str(member), color=discord.Color.orange())
for i, w in enumerate(warns):
embed.add_field(name=“Warning #” + str(i + 1), value=“Reason: “ + w[“reason”] + “\nBy: “ + w[“moderator”] + “\nDate: “ + w[“timestamp”][:10], inline=False)
await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name=“clearwarnings”, description=“Clear all warnings for a member”)
@app_commands.describe(member=“Member to clear”)
@app_commands.checks.has_permissions(administrator=True)
async def clearwarnings(interaction, member: discord.Member):
config, gid = get_guild_config(interaction.guild.id)
if “warnings” in config[gid]:
config[gid][“warnings”][str(member.id)] = []
save_config(config)
await interaction.response.send_message(“Cleared all warnings for “ + str(member), ephemeral=True)

@bot.tree.command(name=“purge”, description=“Delete messages in this channel”)
@app_commands.describe(amount=“Number of messages to delete 1-100”)
@app_commands.checks.has_permissions(manage_messages=True)
async def purge(interaction, amount: int):
if amount < 1 or amount > 100:
await interaction.response.send_message(“Amount must be between 1 and 100.”, ephemeral=True)
return
await interaction.response.defer(ephemeral=True)
deleted = await interaction.channel.purge(limit=amount)
await interaction.followup.send(“Deleted “ + str(len(deleted)) + “ messages.”, ephemeral=True)

@bot.tree.command(name=“slowmode”, description=“Set slowmode for a channel”)
@app_commands.describe(seconds=“Seconds (0 to disable)”, channel=“Channel to set slowmode in”)
@app_commands.checks.has_permissions(manage_channels=True)
async def slowmode(interaction, seconds: int, channel: discord.TextChannel = None):
target = channel or interaction.channel
await target.edit(slowmode_delay=seconds)
if seconds == 0:
await interaction.response.send_message(“Slowmode disabled in “ + target.mention)
else:
await interaction.response.send_message(“Slowmode set to “ + str(seconds) + “s in “ + target.mention)

@bot.tree.command(name=“lock”, description=“Lock a channel”)
@app_commands.describe(channel=“Channel to lock”)
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction, channel: discord.TextChannel = None):
target = channel or interaction.channel
await target.set_permissions(interaction.guild.default_role, send_messages=False)
await interaction.response.send_message(target.mention + “ has been locked.”)

@bot.tree.command(name=“unlock”, description=“Unlock a channel”)
@app_commands.describe(channel=“Channel to unlock”)
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction, channel: discord.TextChannel = None):
target = channel or interaction.channel
await target.set_permissions(interaction.guild.default_role, send_messages=True)
await interaction.response.send_message(target.mention + “ has been unlocked.”)

@bot.tree.command(name=“nick”, description=“Change a member nickname”)
@app_commands.describe(member=“Member to rename”, nickname=“New nickname or blank to reset”)
@app_commands.checks.has_permissions(manage_nicknames=True)
async def nick(interaction, member: discord.Member, nickname: str = None):
await member.edit(nick=nickname)
if nickname:
await interaction.response.send_message(“Changed “ + member.name + “ nickname to “ + nickname)
else:
await interaction.response.send_message(“Reset “ + member.name + “ nickname.”)

@bot.tree.command(name=“ping”, description=“Check bot latency”)
async def ping(interaction):
latency = round(bot.latency * 1000)
await interaction.response.send_message(“Pong! Latency: “ + str(latency) + “ms”)

@bot.tree.command(name=“userinfo”, description=“Get info about a user”)
@app_commands.describe(member=“Member to look up”)
async def userinfo(interaction, member: discord.Member = None):
member = member or interaction.user
embed = discord.Embed(title=str(member), color=member.color, timestamp=datetime.now(timezone.utc))
embed.set_thumbnail(url=member.display_avatar.url)
embed.add_field(name=“ID”, value=str(member.id), inline=True)
embed.add_field(name=“Nickname”, value=member.nick or “None”, inline=True)
embed.add_field(name=“Top Role”, value=member.top_role.mention, inline=True)
embed.add_field(name=“Account Created”, value=member.created_at.strftime(”%d %b %Y”), inline=True)
embed.add_field(name=“Joined Server”, value=member.joined_at.strftime(”%d %b %Y”) if member.joined_at else “Unknown”, inline=True)
roles = [r.mention for r in member.roles if r != interaction.guild.default_role]
embed.add_field(name=“Roles (” + str(len(roles)) + “)”, value=” “.join(roles) if roles else “None”, inline=False)
await interaction.response.send_message(embed=embed)

@bot.tree.command(name=“serverinfo”, description=“Get info about the server”)
async def serverinfo(interaction):
guild = interaction.guild
embed = discord.Embed(title=guild.name, color=discord.Color.blurple(), timestamp=datetime.now(timezone.utc))
if guild.icon:
embed.set_thumbnail(url=guild.icon.url)
embed.add_field(name=“Owner”, value=guild.owner.mention if guild.owner else “Unknown”, inline=True)
embed.add_field(name=“Members”, value=str(guild.member_count), inline=True)
embed.add_field(name=“Channels”, value=str(len(guild.channels)), inline=True)
embed.add_field(name=“Roles”, value=str(len(guild.roles)), inline=True)
embed.add_field(name=“Boosts”, value=str(guild.premium_subscription_count), inline=True)
embed.add_field(name=“Created”, value=guild.created_at.strftime(”%d %b %Y”), inline=True)
await interaction.response.send_message(embed=embed)

@bot.tree.command(name=“avatar”, description=“Get a user avatar”)
@app_commands.describe(member=“Member to get avatar of”)
async def avatar(interaction, member: discord.Member = None):
member = member or interaction.user
embed = discord.Embed(title=member.display_name + “ Avatar”, color=member.color)
embed.set_image(url=member.display_avatar.url)
await interaction.response.send_message(embed=embed)

@bot.tree.command(name=“announce”, description=“Send an announcement embed”)
@app_commands.describe(channel=“Channel to announce in”, title=“Title”, message=“Message body”, ping=“Role to ping”)
@app_commands.checks.has_permissions(manage_messages=True)
async def announce(interaction, channel: discord.TextChannel, title: str, message: str, ping: discord.Role = None):
embed = discord.Embed(title=title, description=message, color=discord.Color.gold(), timestamp=datetime.now(timezone.utc))
embed.set_footer(text=“Announced by “ + str(interaction.user), icon_url=interaction.user.display_avatar.url)
content = ping.mention if ping else None
await channel.send(content=content, embed=embed)
await interaction.response.send_message(“Announcement sent to “ + channel.mention, ephemeral=True)

@bot.tree.command(name=“help”, description=“Show all commands”)
async def help_cmd(interaction):
embed = discord.Embed(title=“Bot Commands”, color=discord.Color.blurple())
embed.add_field(name=“Moderation”, value=”/ban /unban /kick /timeout /untimeout /warn /warnings /clearwarnings /purge /slowmode /lock /unlock /nick”, inline=False)
embed.add_field(name=“Tickets”, value=”/ticket setup - Configure\n/ticket panel - Post the panel”, inline=False)
embed.add_field(name=“Applications”, value=”/application create\n/application panel\n/application list\n/application delete”, inline=False)
embed.add_field(name=“Setup”, value=”/setup welcome\n/setup leave\n/setup autorole\n/setup logs”, inline=False)
embed.add_field(name=“Utility”, value=”/ping /userinfo /serverinfo /avatar /announce /help”, inline=False)
await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def setup_hook():
bot.add_view(TicketOpenView())
bot.add_view(TicketCloseView())

TOKEN = os.getenv(“DISCORD_TOKEN”)
if not TOKEN:
raise ValueError(“DISCORD_TOKEN environment variable not set!”)

bot.run(TOKEN)
