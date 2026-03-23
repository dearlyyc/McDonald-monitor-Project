from apify_client import ApifyClient
import config

client = ApifyClient(config.APIFY_TOKEN)

TEST_NAMES = [
    "apify/facebook-posts-scraper",
    "apify/facebook-post-scraper",
    "danek/facebook-posts-scraper",
    "apify/instagram-posts-scraper",
    "apify/instagram-post-scraper",
    "perfectscrape/instagram-posts-scraper",
    "apify/google-maps-reviews-scraper",
    "blueorion/google-maps-reviews-scraper",
    "shanes/dcard-scraper",
    "ecomscrape/dcard-scraper",
    "dan.vavreck/dcard-scraper"
]

print("Verifying actors...")
for name in TEST_NAMES:
    try:
        actor = client.actor(name).get()
        if actor:
            print(f" [OK] {name}")
    except:
        pass
