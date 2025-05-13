import requests
from bs4 import BeautifulSoup
import time

system_headers = {
    "User-Agent": "Mozilla/5.0"
}

subreddits = ["privacy", "hacking", "netsec", "scams", "socialengineering"]

for subreddit in subreddits:
    print(f"Getting Posts from r/{subreddit}")
    url = f"https://old.reddit.com/r/{subreddit}/hot/" # we are using old reddit and filtering them on hot posts
    response = requests.get(url, headers=system_headers)

    if response.status_code != 200:
        print(f"Failed to fetch data from r/{subreddit}")
        continue
    
    soup = BeautifulSoup(response.text, "html.parser")
    # cause in old reddit the posts are in divs with class "thing" and the title is in a span with class "title"
    # and user posts are in divs with class "usertext-body" (you can check it in dev tools and ctrl + f search those class ids)
    posts = soup.find_all("div", {"class": "thing"})

    post_count = 0

    for post in posts:
        if post_count >= 5:
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
            post_response = requests.get(post_url, headers=system_headers)
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

            # Output the post details
            print(f"[{flair}] {title}")
            print(f"🔗 {post_url}")
            print(f"📝 Body: {body_text[:300]}{'...' if len(body_text) > 300 else ''}\n")  # Truncate for preview

            post_count += 1
            time.sleep(2)  # Respect Reddit’s rate limits
