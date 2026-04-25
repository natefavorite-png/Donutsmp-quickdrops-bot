import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
from datetime import datetime, timedelta, timezone
import re

# ─────────────────────────────────────────────

# CONFIG FILE HELPERS

# ─────────────────────────────────────────────

CONFIG_FILE = “config.json”

def load_config():
if not os.path.exists(CONFIG_FILE):
return {}
with open(CONFIG_FILE, “r”) as f:
return json.load(f)

def save_config(data):
with open(CONFIG_FILE, “w”) as f:
json.dump(data, f, indent=4)

def get_guild_config(guild_id: int):
config = load_config()
gid = str(guild_id)
if gid not in config:
config[gid] = {}
return config, gid

# ─────────────────────────────────────────────

# BOT SETUP

# ─────────────────────────────────────────────

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=”!”, intents=intents)

# ─────────────────────────────────────────────

# READY EVENT

# ─────────────────────────────────────────────

@bot.event
async def on_ready():
print(f”✅ Logged in as {bot.user} (ID: {bot.user.id})”)
try:
synced = await bot.tree.sync()
print(f”✅ Synced {len(synced)} slash commands.”)
except Exception as e:
print(f”❌ Sync error: {e}”)
await bot.change_presence(activity=discord.Activity(
type=discord.ActivityType.watching, name=“your server 👀”
))

# ─────────────────────────────────────────────

# WELCOME SYSTEM

# ─────────────────────────────────────────────

@bot.event
async def on_member_join(member: discord.Member):
config, gid = get_guild_config(member.guild.id)
cfg = config.get(gid, {})

```
# Welcome message
welcome_channel_id = cfg.get("welcome_channel")
if welcome_channel_id:
    channel = member.guild.get_channel(int(welcome_channel_id))
    if channel:
        welcome_msg = cfg.get(
            "welcome_message",
            "👋 Welcome to **{server}**, {user}! You are member #{count}."
        )
        welcome_msg = welcome_msg.replace("{user}", member.mention)
        welcome_msg = welcome_msg.replace("{username}", member.display_name)
        welcome_msg = welcome_msg.replace("{server}", member.guild.name)
        welcome_msg = welcome_msg.replace("{count}", str(member.guild.member_count))

        embed = discord.Embed(
            description=welcome_msg,
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=member.guild.name, icon_url=member.guild.icon.url if member.guild.icon else None)
        await channel.send(embed=embed)

# Auto-role
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
async def on_member_remove(member: discord.Member):
config, gid = get_guild_config(member.guild.id)
cfg = config.get(gid, {})
leave_channel_id = cfg.get(“leave_channel”)
if leave_channel_id:
channel = member.guild.get_channel(int(leave_channel_id))
if channel:
leave_msg = cfg.get(
“leave_message”,
“👋 **{username}** has left the server. We now have {count} members.”
)
leave_msg = leave_msg.replace(”{username}”, member.display_name)
leave_msg = leave_msg.replace(”{server}”, member.guild.name)
leave_msg = leave_msg.replace(”{count}”, str(member.guild.member_count))
embed = discord.Embed(description=leave_msg, color=discord.Color.red(), timestamp=datetime.now(timezone.utc))
embed.set_thumbnail(url=member.display_avatar.url)
await channel.send(embed=embed)

# ─────────────────────────────────────────────

# SETUP COMMANDS — WELCOME

# ─────────────────────────────────────────────

setup_group = app_commands.Group(name=“setup”, description=“Configure bot systems”)

@setup_group.command(name=“welcome”, description=“Set the welcome channel and message”)
@app_commands.describe(
channel=“Channel to send welcome messages in”,
message=“Welcome message. Use {user}, {username}, {server}, {count}”
)
@app_commands.checks.has_permissions(administrator=True)
async def setup_welcome(interaction: discord.Interaction, channel: discord.TextChannel, message: str = None):
config, gid = get_guild_config(interaction.guild.id)
config[gid][“welcome_channel”] = str(channel.id)
if message:
config[gid][“welcome_message”] = message
save_config(config)
await interaction.response.send_message(
f”✅ Welcome channel set to {channel.mention}.” +
(f”\nMessage: `{message}`” if message else “\nUsing default message.”),
ephemeral=True
)

@setup_group.command(name=“leave”, description=“Set the leave channel and message”)
@app_commands.describe(
channel=“Channel to send leave messages in”,
message=“Leave message. Use {username}, {server}, {count}”
)
@app_commands.checks.has_permissions(administrator=True)
async def setup_leave(interaction: discord.Interaction, channel: discord.TextChannel, message: str = None):
config, gid = get_guild_config(interaction.guild.id)
config[gid][“leave_channel”] = str(channel.id)
if message:
config[gid][“leave_message”] = message
save_config(config)
await interaction.response.send_message(
f”✅ Leave channel set to {channel.mention}.” +
(f”\nMessage: `{message}`” if message else “\nUsing default message.”),
ephemeral=True
)

@setup_group.command(name=“autorole”, description=“Set a role to give new members automatically”)
@app_commands.describe(role=“Role to assign on join”)
@app_commands.checks.has_permissions(administrator=True)
async def setup_autorole(interaction: discord.Interaction, role: discord.Role):
config, gid = get_guild_config(interaction.guild.id)
config[gid][“auto_role”] = str(role.id)
save_config(config)
await interaction.response.send_message(f”✅ Auto-role set to {role.mention}.”, ephemeral=True)

@setup_group.command(name=“logs”, description=“Set a channel for moderation logs”)
@app_commands.describe(channel=“Channel to send mod logs”)
@app_commands.checks.has_permissions(administrator=True)
async def setup_logs(interaction: discord.Interaction, channel: discord.TextChannel):
config, gid = get_guild_config(interaction.guild.id)
config[gid][“log_channel”] = str(channel.id)
save_config(config)
await interaction.response.send_message(f”✅ Log channel set to {channel.mention}.”, ephemeral=True)

bot.tree.add_command(setup_group)

# ─────────────────────────────────────────────

# TICKET SYSTEM

# ─────────────────────────────────────────────

class TicketCloseView(discord.ui.View):
def **init**(self):
super().**init**(timeout=None)

```
@discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("❌ You don't have permission to close tickets.", ephemeral=True)
        return
    await interaction.response.send_message("🔒 Closing ticket in 5 seconds...")
    await asyncio.sleep(5)
    await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
```

class TicketOpenView(discord.ui.View):
def **init**(self):
super().**init**(timeout=None)

```
@discord.ui.button(label="🎫 Open a Ticket", style=discord.ButtonStyle.primary, custom_id="open_ticket")
async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
    guild = interaction.guild
    config, gid = get_guild_config(guild.id)
    cfg = config.get(gid, {})

    # Check for existing ticket
    for channel in guild.text_channels:
        if channel.name == f"ticket-{interaction.user.name.lower().replace(' ', '-')}":
            await interaction.response.send_message(
                f"❌ You already have an open ticket: {channel.mention}", ephemeral=True
            )
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
        name=f"ticket-{interaction.user.name.lower().replace(' ', '-')}",
        category=category,
        overwrites=overwrites,
        reason=f"Ticket opened by {interaction.user}"
    )

    embed = discord.Embed(
        title="🎫 Support Ticket",
        description=(
            f"Welcome {interaction.user.mention}!\n\n"
            f"A staff member will be with you shortly.\n"
            f"Please describe your issue in detail."
        ),
        color=discord.Color.blurple(),
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="Click the button below to close this ticket when resolved.")

    await channel.send(
        content=interaction.user.mention + (f" | {support_role.mention}" if support_role else ""),
        embed=embed,
        view=TicketCloseView()
    )
    await interaction.response.send_message(f"✅ Your ticket has been created: {channel.mention}", ephemeral=True)
```

ticket_group = app_commands.Group(name=“ticket”, description=“Ticket system commands”)

@ticket_group.command(name=“panel”, description=“Send the ticket panel to a channel”)
@app_commands.describe(
channel=“Channel to send the panel in”,
title=“Panel title”,
description=“Panel description”
)
@app_commands.checks.has_permissions(administrator=True)
async def ticket_panel(
interaction: discord.Interaction,
channel: discord.TextChannel,
title: str = “🎫 Support Tickets”,
description: str = “Click the button below to open a support ticket. A staff member will assist you shortly.”
):
embed = discord.Embed(title=title, description=description, color=discord.Color.blurple())
embed.set_footer(text=interaction.guild.name, icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
await channel.send(embed=embed, view=TicketOpenView())
await interaction.response.send_message(f”✅ Ticket panel sent to {channel.mention}!”, ephemeral=True)

@ticket_group.command(name=“setup”, description=“Configure ticket system settings”)
@app_commands.describe(
category=“Category where ticket channels will be created”,
support_role=“Role that can see all tickets”
)
@app_commands.checks.has_permissions(administrator=True)
async def ticket_setup(
interaction: discord.Interaction,
category: discord.CategoryChannel,
support_role: discord.Role = None
):
config, gid = get_guild_config(interaction.guild.id)
config[gid][“ticket_category”] = str(category.id)
if support_role:
config[gid][“ticket_support_role”] = str(support_role.id)
save_config(config)
await interaction.response.send_message(
f”✅ Ticket category set to **{category.name}**.” +
(f”\n✅ Support role set to {support_role.mention}.” if support_role else “”),
ephemeral=True
)

bot.tree.add_command(ticket_group)

# ─────────────────────────────────────────────

# APPLICATION SYSTEM

# ─────────────────────────────────────────────

class ApplicationModal(discord.ui.Modal):
def **init**(self, app_name: str, questions: list[str]):
super().**init**(title=f”Application: {app_name}”)
self.app_name = app_name
self.questions = questions
self.fields = []
for i, q in enumerate(questions[:5]):  # Discord max 5 fields
field = discord.ui.TextInput(
label=q[:45],
style=discord.TextStyle.paragraph if i > 0 else discord.TextStyle.short,
required=True,
max_length=1000
)
self.add_item(field)
self.fields.append(field)

```
async def on_submit(self, interaction: discord.Interaction):
    config, gid = get_guild_config(interaction.guild.id)
    cfg = config.get(gid, {})
    apps = cfg.get("applications", {})
    app_cfg = apps.get(self.app_name, {})
    results_channel_id = app_cfg.get("results_channel")

    embed = discord.Embed(
        title=f"📋 New Application — {self.app_name}",
        color=discord.Color.gold(),
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
    embed.add_field(name="Applicant", value=interaction.user.mention, inline=False)

    for i, field in enumerate(self.fields):
        q = self.questions[i] if i < len(self.questions) else f"Question {i+1}"
        embed.add_field(name=q, value=field.value or "No answer", inline=False)

    embed.set_footer(text=f"User ID: {interaction.user.id}")

    if results_channel_id:
        results_channel = interaction.guild.get_channel(int(results_channel_id))
        if results_channel:
            await results_channel.send(embed=embed, view=ApplicationReviewView(interaction.user.id))
            await interaction.response.send_message(
                "✅ Your application has been submitted! Staff will review it soon.", ephemeral=True
            )
            return

    await interaction.response.send_message(
        "✅ Your application has been submitted!\n*(No results channel configured — contact an admin.)*",
        ephemeral=True
    )
```

class ApplicationReviewView(discord.ui.View):
def **init**(self, applicant_id: int):
super().**init**(timeout=None)
self.applicant_id = applicant_id

```
@discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.success, custom_id="app_accept")
async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ No permission.", ephemeral=True)
        return
    member = interaction.guild.get_member(self.applicant_id)
    embed = interaction.message.embeds[0]
    embed.color = discord.Color.green()
    embed.set_footer(text=f"✅ Accepted by {interaction.user} • User ID: {self.applicant_id}")
    await interaction.message.edit(embed=embed, view=None)
    if member:
        try:
            await member.send(f"✅ Your application in **{interaction.guild.name}** has been **accepted**! Congratulations!")
        except Exception:
            pass
    await interaction.response.send_message(f"✅ Application accepted.", ephemeral=True)

@discord.ui.button(label="❌ Deny", style=discord.ButtonStyle.danger, custom_id="app_deny")
async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ No permission.", ephemeral=True)
        return
    member = interaction.guild.get_member(self.applicant_id)
    embed = interaction.message.embeds[0]
    embed.color = discord.Color.red()
    embed.set_footer(text=f"❌ Denied by {interaction.user} • User ID: {self.applicant_id}")
    await interaction.message.edit(embed=embed, view=None)
    if member:
        try:
            await member.send(f"❌ Your application in **{interaction.guild.name}** has been **denied**. Better luck next time!")
        except Exception:
            pass
    await interaction.response.send_message(f"❌ Application denied.", ephemeral=True)
```

class ApplicationButtonView(discord.ui.View):
def **init**(self, app_name: str, questions: list[str]):
super().**init**(timeout=None)
self.app_name = app_name
self.questions = questions
btn = discord.ui.Button(
label=f”Apply for {app_name}”,
style=discord.ButtonStyle.primary,
custom_id=f”apply_{app_name}”
)
btn.callback = self.apply_callback
self.add_item(btn)

```
async def apply_callback(self, interaction: discord.Interaction):
    modal = ApplicationModal(self.app_name, self.questions)
    await interaction.response.send_modal(modal)
```

app_group = app_commands.Group(name=“application”, description=“Application system commands”)

@app_group.command(name=“create”, description=“Create a new application with questions”)
@app_commands.describe(
name=“Name of the application (e.g. Staff, Moderator)”,
results_channel=“Channel where applications are sent for review”,
q1=“Question 1”, q2=“Question 2”, q3=“Question 3”,
q4=“Question 4”, q5=“Question 5”
)
@app_commands.checks.has_permissions(administrator=True)
async def application_create(
interaction: discord.Interaction,
name: str,
results_channel: discord.TextChannel,
q1: str,
q2: str = None,
q3: str = None,
q4: str = None,
q5: str = None
):
questions = [q for q in [q1, q2, q3, q4, q5] if q]
config, gid = get_guild_config(interaction.guild.id)
if “applications” not in config[gid]:
config[gid][“applications”] = {}
config[gid][“applications”][name] = {
“questions”: questions,
“results_channel”: str(results_channel.id)
}
save_config(config)
await interaction.response.send_message(
f”✅ Application **{name}** created with {len(questions)} question(s).\nResults go to {results_channel.mention}.\n”
f”Now use `/application panel` to post the apply button!”,
ephemeral=True
)

@app_group.command(name=“panel”, description=“Send an application panel button to a channel”)
@app_commands.describe(
name=“Name of the application to post”,
channel=“Channel to post the panel in”,
title=“Panel embed title”,
description=“Panel embed description”
)
@app_commands.checks.has_permissions(administrator=True)
async def application_panel(
interaction: discord.Interaction,
name: str,
channel: discord.TextChannel,
title: str = None,
description: str = None
):
config, gid = get_guild_config(interaction.guild.id)
apps = config.get(gid, {}).get(“applications”, {})
if name not in apps:
await interaction.response.send_message(f”❌ No application named **{name}** found. Use `/application create` first.”, ephemeral=True)
return
questions = apps[name][“questions”]
embed = discord.Embed(
title=title or f”📋 {name} Application”,
description=description or f”Click the button below to apply for **{name}**.”,
color=discord.Color.blue()
)
embed.set_footer(text=interaction.guild.name)
await channel.send(embed=embed, view=ApplicationButtonView(name, questions))
await interaction.response.send_message(f”✅ Application panel for **{name}** sent to {channel.mention}!”, ephemeral=True)

@app_group.command(name=“list”, description=“List all created applications”)
@app_commands.checks.has_permissions(administrator=True)
async def application_list(interaction: discord.Interaction):
config, gid = get_guild_config(interaction.guild.id)
apps = config.get(gid, {}).get(“applications”, {})
if not apps:
await interaction.response.send_message(“❌ No applications created yet. Use `/application create`.”, ephemeral=True)
return
embed = discord.Embed(title=“📋 Applications”, color=discord.Color.blue())
for name, data in apps.items():
qs = “\n”.join(f”{i+1}. {q}” for i, q in enumerate(data[“questions”]))
embed.add_field(name=name, value=qs or “No questions”, inline=False)
await interaction.response.send_message(embed=embed, ephemeral=True)

@app_group.command(name=“delete”, description=“Delete an application”)
@app_commands.describe(name=“Name of the application to delete”)
@app_commands.checks.has_permissions(administrator=True)
async def application_delete(interaction: discord.Interaction, name: str):
config, gid = get_guild_config(interaction.guild.id)
apps = config.get(gid, {}).get(“applications”, {})
if name not in apps:
await interaction.response.send_message(f”❌ No application named **{name}**.”, ephemeral=True)
return
del config[gid][“applications”][name]
save_config(config)
await interaction.response.send_message(f”✅ Application **{name}** deleted.”, ephemeral=True)

bot.tree.add_command(app_group)

# ─────────────────────────────────────────────

# MODERATION COMMANDS

# ─────────────────────────────────────────────

async def log_action(guild: discord.Guild, action: str, moderator: discord.Member, target, reason: str):
config, gid = get_guild_config(guild.id)
log_channel_id = config.get(gid, {}).get(“log_channel”)
if not log_channel_id:
return
channel = guild.get_channel(int(log_channel_id))
if not channel:
return
embed = discord.Embed(
title=f”🔨 Moderation — {action}”,
color=discord.Color.orange(),
timestamp=datetime.now(timezone.utc)
)
embed.add_field(name=“Target”, value=f”{target} (`{target.id}`)”, inline=True)
embed.add_field(name=“Moderator”, value=f”{moderator} (`{moderator.id}`)”, inline=True)
embed.add_field(name=“Reason”, value=reason or “No reason provided”, inline=False)
await channel.send(embed=embed)

@bot.tree.command(name=“ban”, description=“Ban a member from the server”)
@app_commands.describe(member=“Member to ban”, reason=“Reason for ban”, delete_days=“Days of messages to delete (0-7)”)
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = “No reason provided”, delete_days: int = 0):
if member.top_role >= interaction.user.top_role:
await interaction.response.send_message(“❌ You cannot ban someone with equal or higher roles.”, ephemeral=True)
return
try:
await member.send(f”🔨 You have been **banned** from **{interaction.guild.name}**.\nReason: {reason}”)
except Exception:
pass
await member.ban(reason=f”{interaction.user}: {reason}”, delete_message_days=min(delete_days, 7))
await interaction.response.send_message(f”✅ **{member}** has been banned.\nReason: {reason}”)
await log_action(interaction.guild, “Ban”, interaction.user, member, reason)

@bot.tree.command(name=“unban”, description=“Unban a user by their ID”)
@app_commands.describe(user_id=“User ID to unban”, reason=“Reason for unban”)
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str, reason: str = “No reason provided”):
try:
user = await bot.fetch_user(int(user_id))
await interaction.guild.unban(user, reason=reason)
await interaction.response.send_message(f”✅ **{user}** has been unbanned.”)
await log_action(interaction.guild, “Unban”, interaction.user, user, reason)
except Exception as e:
await interaction.response.send_message(f”❌ Could not unban: {e}”, ephemeral=True)

@bot.tree.command(name=“kick”, description=“Kick a member from the server”)
@app_commands.describe(member=“Member to kick”, reason=“Reason for kick”)
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = “No reason provided”):
if member.top_role >= interaction.user.top_role:
await interaction.response.send_message(“❌ You cannot kick someone with equal or higher roles.”, ephemeral=True)
return
try:
await member.send(f”👢 You have been **kicked** from **{interaction.guild.name}**.\nReason: {reason}”)
except Exception:
pass
await member.kick(reason=f”{interaction.user}: {reason}”)
await interaction.response.send_message(f”✅ **{member}** has been kicked.\nReason: {reason}”)
await log_action(interaction.guild, “Kick”, interaction.user, member, reason)

@bot.tree.command(name=“timeout”, description=“Timeout (mute) a member temporarily”)
@app_commands.describe(member=“Member to timeout”, minutes=“Duration in minutes”, reason=“Reason”)
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout_cmd(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = “No reason provided”):
if member.top_role >= interaction.user.top_role:
await interaction.response.send_message(“❌ You cannot timeout someone with equal or higher roles.”, ephemeral=True)
return
until = datetime.now(timezone.utc) + timedelta(minutes=minutes)
await member.timeout(until, reason=reason)
await interaction.response.send_message(f”✅ **{member}** has been timed out for **{minutes}** minute(s).\nReason: {reason}”)
await log_action(interaction.guild, f”Timeout ({minutes}m)”, interaction.user, member, reason)

@bot.tree.command(name=“untimeout”, description=“Remove a timeout from a member”)
@app_commands.describe(member=“Member to untimeout”)
@app_commands.checks.has_permissions(moderate_members=True)
async def untimeout_cmd(interaction: discord.Interaction, member: discord.Member):
await member.timeout(None)
await interaction.response.send_message(f”✅ Timeout removed from **{member}**.”)
await log_action(interaction.guild, “Untimeout”, interaction.user, member, “Timeout removed”)

@bot.tree.command(name=“warn”, description=“Warn a member”)
@app_commands.describe(member=“Member to warn”, reason=“Reason for warning”)
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
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
await member.send(f”⚠️ You have been **warned** in **{interaction.guild.name}**.\nReason: {reason}\nWarnings: {count}”)
except Exception:
pass
await interaction.response.send_message(f”⚠️ **{member}** has been warned. They now have **{count}** warning(s).\nReason: {reason}”)
await log_action(interaction.guild, f”Warn (#{count})”, interaction.user, member, reason)

@bot.tree.command(name=“warnings”, description=“View warnings for a member”)
@app_commands.describe(member=“Member to check warnings for”)
@app_commands.checks.has_permissions(manage_messages=True)
async def warnings(interaction: discord.Interaction, member: discord.Member):
config, gid = get_guild_config(interaction.guild.id)
warns = config.get(gid, {}).get(“warnings”, {}).get(str(member.id), [])
if not warns:
await interaction.response.send_message(f”✅ **{member}** has no warnings.”, ephemeral=True)
return
embed = discord.Embed(title=f”⚠️ Warnings for {member}”, color=discord.Color.orange())
for i, w in enumerate(warns):
embed.add_field(
name=f”Warning #{i+1}”,
value=f”**Reason:** {w[‘reason’]}\n**By:** {w[‘moderator’]}\n**Date:** {w[‘timestamp’][:10]}”,
inline=False
)
await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name=“clearwarnings”, description=“Clear all warnings for a member”)
@app_commands.describe(member=“Member to clear warnings for”)
@app_commands.checks.has_permissions(administrator=True)
async def clearwarnings(interaction: discord.Interaction, member: discord.Member):
config, gid = get_guild_config(interaction.guild.id)
if “warnings” in config[gid]:
config[gid][“warnings”][str(member.id)] = []
save_config(config)
await interaction.response.send_message(f”✅ Cleared all warnings for **{member}**.”, ephemeral=True)

@bot.tree.command(name=“purge”, description=“Delete a number of messages in this channel”)
@app_commands.describe(amount=“Number of messages to delete (1-100)”)
@app_commands.checks.has_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction, amount: int):
if amount < 1 or amount > 100:
await interaction.response.send_message(“❌ Amount must be between 1 and 100.”, ephemeral=True)
return
await interaction.response.defer(ephemeral=True)
deleted = await interaction.channel.purge(limit=amount)
await interaction.followup.send(f”✅ Deleted **{len(deleted)}** message(s).”, ephemeral=True)

@bot.tree.command(name=“slowmode”, description=“Set slowmode for a channel”)
@app_commands.describe(seconds=“Slowmode in seconds (0 to disable)”, channel=“Channel to set slowmode in”)
@app_commands.checks.has_permissions(manage_channels=True)
async def slowmode(interaction: discord.Interaction, seconds: int, channel: discord.TextChannel = None):
target = channel or interaction.channel
await target.edit(slowmode_delay=seconds)
if seconds == 0:
await interaction.response.send_message(f”✅ Slowmode disabled in {target.mention}.”)
else:
await interaction.response.send_message(f”✅ Slowmode set to **{seconds}s** in {target.mention}.”)

@bot.tree.command(name=“lock”, description=“Lock a channel so members cannot send messages”)
@app_commands.describe(channel=“Channel to lock (defaults to current)”)
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction, channel: discord.TextChannel = None):
target = channel or interaction.channel
await target.set_permissions(interaction.guild.default_role, send_messages=False)
await interaction.response.send_message(f”🔒 {target.mention} has been **locked**.”)

@bot.tree.command(name=“unlock”, description=“Unlock a channel”)
@app_commands.describe(channel=“Channel to unlock (defaults to current)”)
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction, channel: discord.TextChannel = None):
target = channel or interaction.channel
await target.set_permissions(interaction.guild.default_role, send_messages=True)
await interaction.response.send_message(f”🔓 {target.mention} has been **unlocked**.”)

@bot.tree.command(name=“nick”, description=“Change a member’s nickname”)
@app_commands.describe(member=“Member to rename”, nickname=“New nickname (leave blank to reset)”)
@app_commands.checks.has_permissions(manage_nicknames=True)
async def nick(interaction: discord.Interaction, member: discord.Member, nickname: str = None):
await member.edit(nick=nickname)
if nickname:
await interaction.response.send_message(f”✅ Changed **{member.name}**’s nickname to **{nickname}**.”)
else:
await interaction.response.send_message(f”✅ Reset **{member.name}**’s nickname.”)

# ─────────────────────────────────────────────

# UTILITY COMMANDS

# ─────────────────────────────────────────────

@bot.tree.command(name=“ping”, description=“Check the bot’s latency”)
async def ping(interaction: discord.Interaction):
latency = round(bot.latency * 1000)
await interaction.response.send_message(f”🏓 Pong! Latency: **{latency}ms**”)

@bot.tree.command(name=“userinfo”, description=“Get information about a user”)
@app_commands.describe(member=“Member to get info on”)
async def userinfo(interaction: discord.Interaction, member: discord.Member = None):
member = member or interaction.user
embed = discord.Embed(title=f”👤 {member}”, color=member.color, timestamp=datetime.now(timezone.utc))
embed.set_thumbnail(url=member.display_avatar.url)
embed.add_field(name=“ID”, value=member.id, inline=True)
embed.add_field(name=“Nickname”, value=member.nick or “None”, inline=True)
embed.add_field(name=“Top Role”, value=member.top_role.mention, inline=True)
embed.add_field(name=“Account Created”, value=member.created_at.strftime(”%d %b %Y”), inline=True)
embed.add_field(name=“Joined Server”, value=member.joined_at.strftime(”%d %b %Y”) if member.joined_at else “Unknown”, inline=True)
roles = [r.mention for r in member.roles if r != interaction.guild.default_role]
embed.add_field(name=f”Roles ({len(roles)})”, value=” “.join(roles) if roles else “None”, inline=False)
await interaction.response.send_message(embed=embed)

@bot.tree.command(name=“serverinfo”, description=“Get information about the server”)
async def serverinfo(interaction: discord.Interaction):
guild = interaction.guild
embed = discord.Embed(title=f”🏠 {guild.name}”, color=discord.Color.blurple(), timestamp=datetime.now(timezone.utc))
if guild.icon:
embed.set_thumbnail(url=guild.icon.url)
embed.add_field(name=“Owner”, value=guild.owner.mention if guild.owner else “Unknown”, inline=True)
embed.add_field(name=“Members”, value=guild.member_count, inline=True)
embed.add_field(name=“Channels”, value=len(guild.channels), inline=True)
embed.add_field(name=“Roles”, value=len(guild.roles), inline=True)
embed.add_field(name=“Boosts”, value=guild.premium_subscription_count, inline=True)
embed.add_field(name=“Created”, value=guild.created_at.strftime(”%d %b %Y”), inline=True)
await interaction.response.send_message(embed=embed)

@bot.tree.command(name=“avatar”, description=“Get a user’s avatar”)
@app_commands.describe(member=“Member to get avatar of”)
async def avatar(interaction: discord.Interaction, member: discord.Member = None):
member = member or interaction.user
embed = discord.Embed(title=f”🖼️ {member.display_name}’s Avatar”, color=member.color)
embed.set_image(url=member.display_avatar.url)
await interaction.response.send_message(embed=embed)

@bot.tree.command(name=“announce”, description=“Send an announcement embed to a channel”)
@app_commands.describe(channel=“Channel to announce in”, title=“Announcement title”, message=“Announcement body”, ping=“Role to ping”)
@app_commands.checks.has_permissions(manage_messages=True)
async def announce(interaction: discord.Interaction, channel: discord.TextChannel, title: str, message: str, ping: discord.Role = None):
embed = discord.Embed(title=f”📢 {title}”, description=message, color=discord.Color.gold(), timestamp=datetime.now(timezone.utc))
embed.set_footer(text=f”Announced by {interaction.user}”, icon_url=interaction.user.display_avatar.url)
content = ping.mention if ping else None
await channel.send(content=content, embed=embed)
await interaction.response.send_message(f”✅ Announcement sent to {channel.mention}!”, ephemeral=True)

@bot.tree.command(name=“help”, description=“Show all available commands”)
async def help_cmd(interaction: discord.Interaction):
embed = discord.Embed(
title=“📖 Bot Commands”,
description=“Here is a list of all available commands:”,
color=discord.Color.blurple()
)
embed.add_field(name=“🔨 Moderation”, value=(
“`/ban` `/unban` `/kick` `/timeout` `/untimeout`\n”
“`/warn` `/warnings` `/clearwarnings`\n”
“`/purge` `/slowmode` `/lock` `/unlock` `/nick`”
), inline=False)
embed.add_field(name=“🎫 Tickets”, value=(
“`/ticket setup` — Configure category & support role\n”
“`/ticket panel` — Post the open-ticket button”
), inline=False)
embed.add_field(name=“📋 Applications”, value=(
“`/application create` — Create an application with questions\n”
“`/application panel` — Post the apply button\n”
“`/application list` — List all applications\n”
“`/application delete` — Delete an application”
), inline=False)
embed.add_field(name=“⚙️ Setup”, value=(
“`/setup welcome` — Set welcome channel & message\n”
“`/setup leave` — Set leave channel & message\n”
“`/setup autorole` — Set auto-role on join\n”
“`/setup logs` — Set mod log channel”
), inline=False)
embed.add_field(name=“🔧 Utility”, value=(
“`/ping` `/userinfo` `/serverinfo` `/avatar` `/announce` `/help`”
), inline=False)
embed.set_footer(text=interaction.guild.name)
await interaction.response.send_message(embed=embed, ephemeral=True)

# ─────────────────────────────────────────────

# PERSISTENT VIEWS ON STARTUP

# ─────────────────────────────────────────────

@bot.event
async def setup_hook():
bot.add_view(TicketOpenView())
bot.add_view(TicketCloseView())

# ─────────────────────────────────────────────

# RUN

# ─────────────────────────────────────────────

TOKEN = os.getenv(“DISCORD_TOKEN”)
if not TOKEN:
raise ValueError(“❌ DISCORD_TOKEN environment variable not set!”)

bot.run(TOKEN)
