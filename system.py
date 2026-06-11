import discord
from discord.ext import commands
from datetime import datetime, timezone

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

CATEGORY_ID = 1462863937652658419
open_tickets = {}  # { user_id: channel_id }

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def ticket(ctx):
    # check if user already has an open ticket
    if ctx.author.id in open_tickets:
        existing = ctx.guild.get_channel(open_tickets[ctx.author.id])
        if existing:
            await ctx.send(f"❌ You already have an open ticket: {existing.mention}", delete_after=5)
            return
        else:
            del open_tickets[ctx.author.id]

    embed = discord.Embed(
        title="🎫 Open a Ticket",
        description="What kind of ticket do you want to open?\n\n🛠️ React with **1️⃣** for **Support**\n🚨 React with **2️⃣** for **Report**",
        color=discord.Color.blurple(),
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("1️⃣")
    await msg.add_reaction("2️⃣")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["1️⃣", "2️⃣"] and reaction.message.id == msg.id

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=30.0, check=check)
    except:
        await msg.delete()
        await ctx.send("❌ Ticket creation timed out.", delete_after=5)
        return

    await msg.delete()

    ticket_type = "support" if str(reaction.emoji) == "1️⃣" else "report"
    emoji = "🛠️" if ticket_type == "support" else "🚨"

    category = ctx.guild.get_channel(CATEGORY_ID)
    if not category:
        await ctx.send("❌ Ticket category not found. Contact an admin.")
        return

    # set permissions — only the user and admins can see the ticket
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        ctx.author: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        ctx.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
    }

    # give access to all admins
    for role in ctx.guild.roles:
        if role.permissions.administrator:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

    channel = await category.create_text_channel(
        name=f"{ticket_type}-{ctx.author.name}",
        overwrites=overwrites,
        topic=f"{emoji} {ticket_type.capitalize()} ticket by {ctx.author} | ID: {ctx.author.id}"
    )

    open_tickets[ctx.author.id] = channel.id

    embed = discord.Embed(
        title=f"{emoji} {ticket_type.capitalize()} Ticket",
        description=f"Hey {ctx.author.mention}! Welcome to your ticket.\n\nPlease describe your issue and a staff member will be with you shortly.",
        color=discord.Color.green() if ticket_type == "support" else discord.Color.red(),
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text=f"Ticket by {ctx.author}", icon_url=ctx.author.display_avatar.url)
    embed.add_field(name="📋 Type", value=f"{emoji} {ticket_type.capitalize()}", inline=True)
    embed.add_field(name="👤 Opened by", value=ctx.author.mention, inline=True)
    embed.add_field(name="🔒 To close", value="Type `!close` to close this ticket", inline=False)

    await channel.send(embed=embed)
    await ctx.send(f"✅ Your ticket has been opened: {channel.mention}", delete_after=5)

@bot.command()
async def close(ctx):
    # check if this channel is a ticket
    user_id = None
    for uid, cid in open_tickets.items():
        if cid == ctx.channel.id:
            user_id = uid
            break

    if not user_id:
        await ctx.send("❌ This is not a ticket channel.", delete_after=5)
        return

    embed = discord.Embed(
        title="🔒 Ticket Closing",
        description="This ticket will be closed in **5 seconds**...",
        color=discord.Color.orange(),
        timestamp=datetime.now(timezone.utc)
    )
    await ctx.send(embed=embed)

    import asyncio
    await asyncio.sleep(5)

    del open_tickets[user_id]
    await ctx.channel.delete(reason=f"Ticket closed by {ctx.author}")

@bot.command()
@commands.has_permissions(administrator=True)
async def tickets(ctx):
    if not open_tickets:
        embed = discord.Embed(
            title="🎫 Open Tickets",
            description="✅ No open tickets right now!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(
        title="🎫 Open Tickets",
        description=f"Total open: **{len(open_tickets)}**",
        color=discord.Color.blurple(),
        timestamp=datetime.now(timezone.utc)
    )

    for user_id, channel_id in open_tickets.items():
        channel = ctx.guild.get_channel(channel_id)
        member = ctx.guild.get_member(user_id)
        if channel and member:
            embed.add_field(
                name=f"👤 {member.name}",
                value=f"📌 {channel.mention}",
                inline=False
            )

    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@tickets.error
async def tickets_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 You need to be an **administrator** to use this command.")

bot.run("MTUxNDc1MjAyNzQ3MTkwNDk2MA.GckHfQ.l9IPWU2nhmV0uwQkY5T-AgVX5KZLB1gWo4VM0o")

