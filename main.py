import asyncio
import httpx
from bs4 import BeautifulSoup
import json
import time
from fastapi import FastAPI

system_headers = {
    "User-Agent": "Mozilla/5.0"
}

subreddits = ["privacy", "hacking", "netsec", "scams", "socialengineering"]


app = FastAPI()

@app.get("/")
async def root():
    return {
        "App": "WraithWatch", 
        "Version": "0.0.1",
        "Author": "Michael Ygana (Totem)"
        }

#Get Hot posts from subreddits
@app.get("/get_hot_posts")
async def getHotPosts():
    scraped_results = []


    async with httpx.AsyncClient(timeout=10, headers=system_headers) as client:
        for subreddit in subreddits:
            url = f"https://old.reddit.com/r/{subreddit}/hot/" # we are using old reddit and filtering them on hot posts
            response = await client.get(url)
            if response.status_code != 200:
                return {"error": f"Failed to fetch data from r/{subreddit}"}
                continue
        
            soup = BeautifulSoup(response.text, "html.parser")
            # getiing basic posts details first
            posts = soup.find_all("div", {"class": "thing"})
            post_count = 0

            for post in posts:
                if post_count >= 5:
                    print(f"Done fetching posts from r/{subreddit}")
                    break

                post_title = post.find("a", {"class": "title"}) # get the post title
                flair = post.find("span", {"class": "linkflairlabel"}) # get the flair (i'll use this for filtering laters)

                if post_title:
                    title = post_title.text.strip()
                    post_url = post_title["href"]

                    # skip links that are not actual post URLs (e.g. user profiles, external links, etc.)
                    if not post_url.startswith("/r/"):
                        continue
                    
                    post_url = "https://old.reddit.com" + post_url  # convert relative URL to full URL

                    flair = flair.text.strip() if flair else "No Flair"

                    # get the post content
                    post_response = await client.get(post_url)
                    post_soup = BeautifulSoup(post_response.text, "html.parser")
                    
                    # scope only the actual post area and exclude comment bodies
                    site_table = post_soup.find("div", id="siteTable")
                    if site_table:
                        usertexts = site_table.find_all("div", class_="usertext-body")
                        if len(usertexts) >= 1:
                            body_text = usertexts[0].text.strip()
                        else:
                            continue  # skip this post if there's no body
                    else:
                        continue  # skip this post if siteTable is not found

                    if not body_text:
                        continue  # filter out empty body posts
                    
                    scraped_results.append({
                        "title": title,
                        "url": post_url,
                        "flair": flair,
                        "body": body_text
                    })
                
                post_count += 1

    return {"Status": "Success", "Results": scraped_results}
                    
