import discord
from discord import app_commands
from discord.ext import tasks
import random
import json
import os

# =========================
# 🔑 HIER EINSETZEN
# =========================
import os
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = 836287891403047013

# =========================
# SAVE / LOAD SYSTEM
# =========================
SAVE_FILE = "data.json"

def save_data():
    data = {
        "users": users,
        "stocks": stocks,
        "admin_influence": admin_influence,
        "stock_history": stock_history
    }

    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)

def load_data():
    global users, stocks, admin_influence, stock_history

    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)

            users = data["users"]
            stocks = data["stocks"]
            admin_influence = data["admin_influence"]
            stock_history = data["stock_history"]

# =========================
# BOT SETUP
# =========================
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# =========================
# USER SYSTEM
# =========================
users = {}

def get_user(user_id):

    user_id = str(user_id)

    if user_id not in users:
        users[user_id] = {
            "coins": 0,
            "portfolio": {}
        }

    return users[user_id]

# =========================
# STOCKS
# =========================
stocks = {
    "PIXEL": 5,
    "BLOCKY": 10,
    "BLOX": 25,
    "ROBX": 35,
    "NEON": 50,
    "VERTEX": 80,
    "GAMECORE": 130,
    "MEGACORP": 200,
    "GLITCH": 450,
    "CHAOS": 1000
}

stock_history = {s: [p] for s, p in stocks.items()}
admin_influence = {s: 0 for s in stocks}

# =========================
# LOAD DATA
# =========================
load_data()

# =========================
# MARKET UPDATE
# =========================
@tasks.loop(minutes=5)
async def update_market():

    for stock in stocks:

        random_change = random.randint(-5, 5)

        total_change = random_change + admin_influence[stock]

        current_price = stocks[stock]

        new_price = int(
            current_price * (1 + total_change / 100)
        )

        stocks[stock] = max(1, new_price)

        stock_history[stock].append(stocks[stock])

        if len(stock_history[stock]) > 50:
            stock_history[stock].pop(0)

    save_data()

# =========================
# READY EVENT
# =========================
@client.event
async def on_ready():

    try:
        await tree.sync()
        print("Slash commands synced")
    except Exception as e:
        print("Sync error:", e)

    if not update_market.is_running():
        update_market.start()

    print(f"Bot online as {client.user}")

# =========================
# TEST
# =========================
@tree.command(name="test", description="Test bot")
async def test(interaction: discord.Interaction):

    await interaction.response.send_message(
        "Bot works!"
    )

# =========================
# BALANCE
# =========================
@tree.command(name="balance", description="Check balance")
async def balance(interaction: discord.Interaction):

    user = get_user(interaction.user.id)

    await interaction.response.send_message(
        f"💰 Coins: {user['coins']}"
    )

# =========================
# MARKET
# =========================
@tree.command(name="market", description="View stocks")
async def market(interaction: discord.Interaction):

    text = "📈 Vertex Market\n\n"

    for stock, price in stocks.items():
        text += f"{stock} = {price} Coins\n"

    await interaction.response.send_message(text)

# =========================
# PRICE
# =========================
@tree.command(name="price", description="Check stock price")
async def price(interaction: discord.Interaction, stock: str):

    stock = stock.upper()

    if stock not in stocks:
        return await interaction.response.send_message(
            "❌ Stock not found"
        )

    await interaction.response.send_message(
        f"📈 {stock} = {stocks[stock]} Coins"
    )

# =========================
# BUY
# =========================
@tree.command(name="buy", description="Buy stock")
async def buy(
    interaction: discord.Interaction,
    stock: str,
    amount: int
):

    user = get_user(interaction.user.id)

    stock = stock.upper()

    if stock not in stocks:
        return await interaction.response.send_message(
            "❌ Stock not found"
        )

    cost = stocks[stock] * amount

    if user["coins"] < cost:
        return await interaction.response.send_message(
            "❌ Not enough coins"
        )

    user["coins"] -= cost

    user["portfolio"][stock] = (
        user["portfolio"].get(stock, 0) + amount
    )

    save_data()

    await interaction.response.send_message(
        f"✅ Bought {amount} {stock}"
    )

# =========================
# SELL
# =========================
@tree.command(name="sell", description="Sell stock")
async def sell(
    interaction: discord.Interaction,
    stock: str,
    amount: int
):

    user = get_user(interaction.user.id)

    stock = stock.upper()

    if stock not in user["portfolio"]:
        return await interaction.response.send_message(
            "❌ You don't own this stock"
        )

    if user["portfolio"][stock] < amount:
        return await interaction.response.send_message(
            "❌ Not enough shares"
        )

    gain = stocks[stock] * amount

    user["coins"] += gain

    user["portfolio"][stock] -= amount

    save_data()

    await interaction.response.send_message(
        f"💸 Sold for {gain} Coins"
    )

# =========================
# PORTFOLIO
# =========================
@tree.command(name="portfolio", description="View portfolio")
async def portfolio(interaction: discord.Interaction):

    user = get_user(interaction.user.id)

    if not user["portfolio"]:
        return await interaction.response.send_message(
            "📂 Portfolio empty"
        )

    text = "📂 Your Portfolio\n\n"

    for stock, amount in user["portfolio"].items():
        text += f"{stock}: {amount}\n"

    await interaction.response.send_message(text)

# =========================
# ADMIN - ADD COINS
# =========================
@tree.command(name="addcoins", description="Owner only")
async def addcoins(
    interaction: discord.Interaction,
    user: discord.Member,
    amount: int
):

    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message(
            "❌ No permission"
        )

    target = get_user(user.id)

    target["coins"] += amount

    save_data()

    await interaction.response.send_message(
        f"✅ Added {amount} coins to {user.name}"
    )

# =========================
# ADMIN - SET CHANGE
# =========================
@tree.command(name="setchange", description="Owner only")
async def setchange(
    interaction: discord.Interaction,
    stock: str,
    percent: int
):

    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message(
            "❌ No permission"
        )

    stock = stock.upper()

    if stock not in stocks:
        return await interaction.response.send_message(
            "❌ Stock not found"
        )

    admin_influence[stock] = percent

    current_price = stocks[stock]

    new_price = int(
        current_price * (1 + percent / 100)
    )

    stocks[stock] = max(1, new_price)

    save_data()

    await interaction.response.send_message(
        f"📈 {stock} changed by {percent}%"
    )

# =========================
# ADMIN - RESET MARKET
# =========================
@tree.command(name="resetmarket", description="Owner only")
async def resetmarket(interaction: discord.Interaction):

    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message(
            "❌ No permission"
        )

    for stock in admin_influence:
        admin_influence[stock] = 0

    save_data()

    await interaction.response.send_message(
        "🔄 Market reset"
    )

# =========================
# RUN BOT
# =========================
client.run(TOKEN)
