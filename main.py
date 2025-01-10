import os, youtube_search, yt_dlp, spotipy, discord
from asyncio import run_coroutine_threadsafe
from sys import exit
from discord.ext import commands
from spotipy.oauth2 import SpotifyOAuth
from random import shuffle

dirPath = os.path.realpath(__file__).split("main.py")[0]
ytdlp_format_options = {
   'format': 'bestaudio',
   'noplaylist': True,
   'outtmpl': f"{dirPath}Downloaded Music\\%(title)s - %(id)s.%(ext)s"
}
Fffmpeg_options = {
   'before_options': '-reconnect 1 -reconnected-streamed 1 -reconnect_delay_max 5',
   'options': '-vn'
}

ytdlp = yt_dlp.YoutubeDL(ytdlp_format_options)
spotifyPlaylistID = "REPLACE WITH SPOTIFY PLAYLIST ID"

#Checks for missing required files
if not os.path.exists(f"{dirPath}\\botsecret.txt") or not os.path.exists(f"{dirPath}\\spotifysecret.txt"):
   exit("ERROR - Missing discord bot secret or spotify client id/secret")

#Creates the downloaded music folder (if it doesn't exist)
if not os.path.exists(f"{dirPath}\\Downloaded Music"):
   os.makedirs(f"{dirPath}\\Downloaded Music")

#Reads previously downloaded songs
downloaded_songs = {}
for file in os.listdir(f"{dirPath}Downloaded Music"):
   downloaded_songs[file.split("- ")[-1][:-4]] = {"file":f"{dirPath}\\Downloaded Music\\{file}","title":file.split(" - " + file.split(" - ")[-1])[0]}
print(f"Found {len(downloaded_songs)} downloaded songs")

#Grab bot secret
with open(dirPath + "botsecret.txt", "r") as botFile:
   botSecret = botFile.readline() # Put Bot Secret on first line
   botFile.close()
#Grab spotify client id and secret
with open(dirPath + "spotifysecret.txt", "r") as spotifyFile:
   spotifyID = spotifyFile.readline()[:-1] # Put Spotify Client Secret on first line
   spotifySecret = spotifyFile.readline() # Put Spotify Client ID on second line
   spotifyFile.close()

#Connect with spotify api
scope = "user-library-read"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(spotifyID,spotifySecret,"http://localhost:8888/callback",scope=scope))

#Get all the songs in the specified spotify playlist
songQueue = []
for song in sp.playlist(spotifyPlaylistID,"tracks")["tracks"]["items"]:
   artists = ""
   for artist in song["track"]["artists"]:
      artists += artist["name"]+","
   artists = artists.removesuffix(",")
   video = youtube_search.YoutubeSearch(f"{song["track"]["name"]} - {artists}",max_results=1).to_dict()[0]
   videoID = video["id"]
   if not videoID in downloaded_songs.keys():
      info = ytdlp.extract_info(f"https://www.youtube.com/watch?v={videoID}",download=True)
      filename = ytdlp.prepare_filename(info)
      downloaded_songs[videoID] = {"file":filename,"title":info["title"]}
   print(f"{song["track"]["name"]} - {artists} [{videoID}]")
   songQueue.append(downloaded_songs[videoID])
currentSong = -1
shuffle(songQueue)

#Setup Discord Bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!',intents=intents)

#Discord IDs
discordServerID = "REPLACE WITH SERVER ID"
discordVoiceChannelID = "REPLACE WITH THE VOICE CHANNEL ID THAT THE BOT WILL BE IN"

@bot.event
async def on_ready():
   await start()

async def start():
   global currentSong
   voice = discord.utils.get(bot.voice_clients, guild=bot.get_guild(discordServerID))
   VoiceChannel = bot.get_channel(discordVoiceChannelID)
   #Join voice channel
   if not voice or not voice.is_connected():
      voice = await VoiceChannel.connect()
   currentSong += 1
   if currentSong >= len(songQueue):
      currentSong = 0
      shuffle(songQueue)
   source = discord.FFmpegOpusAudio(songQueue[currentSong]["file"],executable="C:/Program Files/ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe")
   voice.play(source,after=lambda e: run_coroutine_threadsafe(start(), bot.loop))
   await bot.change_presence(activity=discord.CustomActivity(f"Playing {songQueue[currentSong]["title"]}"))

bot.run(botSecret)
