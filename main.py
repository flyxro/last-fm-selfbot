import json
import discord
import requests
import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Load the configuration from JSON
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_config(data):
    with open('config.json', 'w') as f:
        json.dump(data, f, indent=4)

config = load_config()

# Define your bot
client = discord.Client()

# Last.fm API setup
API_KEY = ""
LASTFM_API_URL = "http://ws.audioscrobbler.com/2.0/"

# Get the currently playing track
def get_lastfm_now_playing(username):
    payload = {
        'method': 'user.getRecentTracks',
        'user': username,
        'api_key': API_KEY,
        'format': 'json',
        'limit': 1
    }
    response = requests.get(LASTFM_API_URL, params=payload)
    if response.status_code == 200:
        data = response.json()
        recent_tracks = data['recenttracks']['track']
        if len(recent_tracks) > 0:
            return recent_tracks[0]
    return None

# Get the total scrobbles for the user
def get_lastfm_total_scrobbles(username):
    payload = {
        'method': 'user.getInfo',
        'user': username,
        'api_key': API_KEY,
        'format': 'json'
    }
    response = requests.get(LASTFM_API_URL, params=payload)
    if response.status_code == 200:
        data = response.json()
        total_scrobbles = data['user']['playcount']
        return total_scrobbles
    return 'Unknown'

# Get the top artists for the user
def get_lastfm_top_artists(username):
    payload = {
        'method': 'user.getTopArtists',
        'user': username,
        'api_key': API_KEY,
        'format': 'json',
        'limit': 5
    }
    response = requests.get(LASTFM_API_URL, params=payload)
    if response.status_code == 200:
        data = response.json()
        top_artists = data['topartists']['artist']
        return top_artists
    return []

# Get the top albums for the user
def get_lastfm_top_albums(username):
    payload = {
        'method': 'user.getTopAlbums',
        'user': username,
        'api_key': API_KEY,
        'format': 'json',
        'limit': 5
    }
    response = requests.get(LASTFM_API_URL, params=payload)
    if response.status_code == 200:
        data = response.json()
        top_albums = data['topalbums']['album']
        return top_albums
    return []

@client.event
async def on_message(message):
    if message.author != client.user:
        return

    if message.content.startswith('!set'):
            try:
                username = message.content.split(' ')[1]  # Get the username from the message
                config['lastfm_username'] = username  # Store the username in config
                save_config(config)  # Save the updated config
                await message.channel.send(f'Last.fm username set to: {username}')
            except IndexError:
                await message.channel.send("Please provide a valid Last.fm username. Usage: `!set <username>`")


    # Now playing command
    if message.content == '!np':
        username = config.get('lastfm_username')
        if not username:
            await message.channel.send("No Last.fm username set. Use `!setlastfm <username>`")
        else:
            # Get now playing track
            now_playing = get_lastfm_now_playing(username)
            total_scrobbles = get_lastfm_total_scrobbles(username)
            
            if now_playing:
                track = now_playing['name']
                artist = now_playing['artist']['#text']
                album = now_playing['album']['#text'] if now_playing['album']['#text'] else "N/A"

                # Construct the basic message with backticks
                now_playing_message = (
                    f"```\n"
                    f"🎶 Now Playing 🎶\n\n"
                    f"Song: {track}\n"
                    f"Artist: {artist}\n"
                    f"Album: {album}\n"
                    f"Total Scrobbles: {total_scrobbles}\n"
                    f" selfbot created by our king wonder```"
                )

                # Send the basic text message
                await message.channel.send(now_playing_message)

    # Top artists command
    elif message.content == '!ta':
        username = config.get('lastfm_username')
        if not username:
            await message.channel.send("No Last.fm username set. Use `!set <username>`")
        else:
            top_artists = get_lastfm_top_artists(username)
            if top_artists:
                top_artists_message = "🎤 Top 5 Artists 🎤\n\n"
                for i, artist in enumerate(top_artists, 1):
                    top_artists_message += f"{i}. {artist['name']} - {artist['playcount']} plays\n"

                await message.channel.send(f"```\n{top_artists_message}\n bot created by our king wonder```")
            else:
                await message.channel.send("Could not retrieve top artists.")

    # Top albums command
    elif message.content == '!tal':
        username = config.get('lastfm_username')
        if not username:
            await message.channel.send("No Last.fm username set. Use `!setlastfm <username>`")
        else:
            top_albums = get_lastfm_top_albums(username)
            if top_albums:
                top_albums_message = "🎶 Top 5 Albums 🎶\n\n"
                for i, album in enumerate(top_albums, 1):
                    top_albums_message += f"{i}. {album['name']} by {album['artist']['name']} - {album['playcount']} plays\n"

                await message.channel.send(f"```\n{top_albums_message}\n bot created by our king wonder```")
            else:
                await message.channel.send("Could not retrieve top albums.")

# Run background task to update the status
async def update_status():
    await client.wait_until_ready()
    username = config.get('lastfm_username')  # Fetch the username from the config
    while not client.is_closed():
        if username:
            track, artist = get_lastfm_now_playing(username)
            if track and artist:
                await client.change_presence(activity=discord.Activity(
                    type=discord.ActivityType.listening, name=f"{track} by {artist}"))
            else:
                await client.change_presence(activity=discord.Game(name="REEE"))
        else:
            await client.change_presence(activity=discord.Game(name="REEE"))
        await asyncio.sleep(60)  # Update every 60 seconds

# Use the new async setup hook for running background tasks
class MyClient(discord.Client):
    async def setup_hook(self):
        self.loop.create_task(update_status())

# Initialize the client
client = MyClient()

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

# Load your Discord token from the config JSON
client.run("")
