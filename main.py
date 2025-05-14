# ==================================================
# Application: WraithWatch
# Description: A discord bot that scrapes reddit (r/privacy, r/hacking, r/netsec, r/scams, r/socialengineering) 
# for posts that contain certain keywords.
# Author: @totenem
# Version: 1.0.0
# ==================================================
import discord 
from discord.ext import commands
import json
from groq import Groq
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import time
import os
import requests
from discord import app_commands

load_dotenv()

discord_token = os.getenv("DISCORD_BOT_TOKEN")
groq_key = os.getenv("GROQ_API_KEY")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

system_headers = {
    "User-Agent": "Mozilla/5.0"
}

client = Groq(
    api_key=groq_key
)

# Custom button class to handle clicks
class PostSelectView(discord.ui.View):
    def __init__(self, posts):
        super().__init__(timeout=60)
        self.posts = posts
        for i in range(len(posts)):
            self.add_item(PostButton(label=str(i + 1), index=i))

class PostButton(discord.ui.Button):
    def __init__(self, label, index):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            await self.ai_summary(interaction)
        except Exception as e:
            print(f"Error in button callback: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred while generating the summary.", ephemeral=True)
            else:
                await interaction.followup.send("❌ An error occurred while generating the summary.", ephemeral=True)

    async def ai_summary(self, interaction: discord.Interaction):
        try:
            post = self.view.posts[self.index]
            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that summarizes reddit posts."
                    },
                    {
                        "role": "user",
                        "content": f"Please summarize the following reddit post: {post['url']}. The summary should be concise and to the point. If its story summarize on what happened. If its an experience ofa comapny or someone, add tips on how to avoid it. make  it 5-10 sentences with proper spacing and paragraphs. Only return the summary, no other text. "
                    }
                ],
                model="llama-3.1-8b-instant",
                max_tokens=1000
            )
            summary = response.choices[0].message.content
            await interaction.followup.send(
                f"🧠 AI Summary: \n{summary}\nURL: {post['url']}", 
                ephemeral=True
            )
        except Exception as e:
            print(f"Error in AI summary: {e}")
            await interaction.followup.send("❌ Failed to generate AI summary for this post.", ephemeral=True)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s)")
        print(f"✅ Bot is ready! Logged in as {bot.user}")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

@bot.command()
async def hello(ctx):
    await ctx.send("Hello!")

#commamd to check ping
@bot.tree.command(name="ping", description="Check the bot's latency")
async def ping(interaction: discord.Interaction):
    try:
        latency = round(bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong! Latency: {latency}ms")
    except Exception as e:
        print(f"Error in ping command: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ An error occurred while processing the command.")

#command to scrape 5 latest posts in a specific subreddit
@bot.tree.command(name="latest", description="Scrape 5 latest posts in a specific subreddit")
@app_commands.choices(
    subreddit=[
        app_commands.Choice(name="privacy", value="privacy"),
        app_commands.Choice(name="hacking", value="hacking"),
        app_commands.Choice(name="netsec", value="netsec"),
        app_commands.Choice(name="scams", value="scams"),
        # app_commands.Choice(name="socialengineering", value="socialengineering")
    ]
)
async def scrape(interaction: discord.Interaction, subreddit: app_commands.Choice[str]):
    post_count = 0
    posts = []
    try:
        await interaction.response.defer()
        subredit_url = f"https://old.reddit.com/r/{subreddit.value}/rising/"
        response = requests.get(subredit_url, headers=system_headers)

        if response.status_code != 200:
            await interaction.followup.send("❌ Failed to fetch data from the subreddit.")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        posts_scraped = soup.find_all("div", {"class": "thing"})

        for post in posts_scraped:
            if post_count >= 5:
                break

            post_title = post.find("a", {"class": "title"})
            flair = post.find("span", {"class": "linkflairlabel"})
            if post_title and flair:
                title = post_title.text.strip()
                post_url = post_title["href"]

                if not post_url.startswith("/r/"):
                    continue

                post_data = {
                    "title": title,
                    "url": f"https://old.reddit.com{post_url}",
                    "flair": flair.text.strip()
                }

                posts.append(post_data)
                post_count += 1

        if posts:
            embed = discord.Embed(
                title=f"📬 Latest posts from r/{subreddit.value}",
                color=discord.Color.blue()
            )
            for i, post in enumerate(posts):
                embed.add_field(
                    name=f"{i + 1}. {post['title']}",
                    value=f"**Flair:** {post['flair']}\n🔗 [Link]({post['url']})",
                    inline=False
                )
            view = PostSelectView(posts)
            await interaction.followup.send(embed=embed, view=view)
        else:
            await interaction.followup.send("❌ No posts found in the subreddit.")
    except Exception as e:
        print(f"Error in scrape command: {e}")
        await interaction.followup.send("❌ An error occurred while processing the command.")

bot.run(discord_token)
    
