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
from urllib.parse import urlparse, parse_qs, unquote

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


def search_duckduckgo(query):
    search_url = "https://html.duckduckgo.com/html/"
    parameters = {"q": query}
    response = requests.get(search_url, headers=system_headers, params=parameters)
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.text, 'html.parser')

    results = []
    for result in soup.select('.result__title a')[:5]:
        title = result.text.strip()
        link = result['href']
        
        # Handle DuckDuckGo's redirect URLs
        if link.startswith('//'):
            link = 'https:' + link
        
        # Extract the actual URL from DuckDuckGo's redirect
        try:
            if 'duckduckgo.com/l/?uddg=' in link:
                # Extract and decode the actual URL from the 'uddg' parameter
                parsed = urlparse(link)
                actual_url = parse_qs(parsed.query)['uddg'][0]
                link = unquote(actual_url)
        except Exception as e:
            print(f"Error processing URL {link}: {e}")
            continue

        results.append((title, link))
    return results

#extract the main post from the url and return the content
def extract_main_post(url):
    try:
        res = requests.get(url, headers=system_headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        paragraphs = soup.find_all('p')
        content = "\n".join(p.get_text() for p in paragraphs)
        return content.strip()
    except Exception as e:
        print(f"Error in extract_main_post: {e}")
        return None

#summarize the combined text from the search results
def summarize_combined_text(full_text):
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that provides concise summaries. Create a brief summary in 3-4 sentences with proper spacing. Focus on the most important points only. Keep the total length under 800 characters. Only return the summary, no other text or titles."
                },
                {
                    "role": "user",
                    "content": f"Please summarize the following text: {full_text}"
                }
            ],
            model="llama-3.3-70b-versatile",
            max_tokens=1000
        )
        summary = response.choices[0].message.content
        return summary.strip()
    except Exception as e:
        print(f"Error in summarize_combined_text: {e}")
        return None


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
        # app_commands.Choice(name="netsec", value="netsec"),
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
        

#command to ask questions and get summarized answers
@bot.tree.command(name="ask", description="Ask a question and get a summarized answer from web searches")
async def ask(interaction: discord.Interaction, question: str):
    try:
        await interaction.response.defer()
        
        # Search for relevant results
        search_results = search_duckduckgo(question)
        if not search_results:
            await interaction.followup.send("❌ Sorry, I couldn't find any relevant results for your question.")
            return

        # Extract and combine content from the first 3 results
        combined_content = []
        for title, url in search_results[:3]:
            content = extract_main_post(url)
            if content:
                combined_content.append(f"From {title}:\n{content}")

        if not combined_content:
            await interaction.followup.send("❌ Sorry, I couldn't extract content from the search results.")
            return

        # Combine all content and summarize
        full_text = "\n\n".join(combined_content)
        summary = summarize_combined_text(full_text)

        if not summary:
            await interaction.followup.send("❌ Sorry, I couldn't generate a summary of the results.")
            return

        # Create an embed for the response
        embed = discord.Embed(
            title="🤔 Answer to your question",
            description=f"**Question:** {question}",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Answer", value=summary, inline=False)
        
        # Add sources
        sources = "\n".join([f"[{title}]({url})" for title, url in search_results[:3]])
        if len(sources) > 1024:
            sources = sources[:1021] + "..."
        embed.add_field(name="Sources", value=sources, inline=False)

        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"Error in ask command: {e}")
        await interaction.followup.send("❌ An error occurred while processing your question.")

bot.run(discord_token)
    
