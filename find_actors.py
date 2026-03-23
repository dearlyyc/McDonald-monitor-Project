from apify_client import ApifyClient
import config

client = ApifyClient(config.APIFY_TOKEN)

def search_actor(query):
    print(f"\nSearching for '{query}':")
    results = client.store().list(search=query)
    for a in results.items[:3]:
        uname = a.get("username")
        name = a.get("name")
        print(f" - {uname}/{name} (ID: {a.get('id')})")

search_actor("facebook posts")
search_actor("instagram posts")
search_actor("google maps reviews")
search_actor("dcard")
