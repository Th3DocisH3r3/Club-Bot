import os
import discord
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import youtube_search
import random
import yt_dlp
import asyncio

dirPath = os.path.realpath(__file__).split("main.py")[0]

print(dirPath)

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

spotifyPlaylistID = "3H3Dfcb6BtIFP0imQzi8fY"

#Reads previously downloaded songs
downloaded_songs = {}
for file in os.listdir(f"{dirPath}Downloaded Music"):
   downloaded_songs[file.split("- ")[-1][:-4]] = {"file":f"{dirPath}\\Downloaded Music\\{file}","title":file.split(" - " + file.split(" - ")[-1])[0]}

print(f"Found {len(downloaded_songs)} downloaded songs")
#Opens file in same folder named secret.txt to read bot secret
with open(dirPath + "botsecret.txt", "r") as botFile:
   botSecret = botFile.readline() # Put Bot Secret on first line
   botFile.close()
with open(dirPath + "spotifysecret.txt", "r") as spotifyFile:
   spotifyID = spotifyFile.readline()[:-1] # Put Spotify Client Secret on first line
   spotifySecret = spotifyFile.readline() # Put Spotify Client ID on second line
   spotifyFile.close()

scope = "user-library-read"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(spotifyID,spotifySecret,"http://localhost:8888/callback",scope=scope))

songQueue = []

for song in sp.playlist(spotifyPlaylistID,"tracks")["tracks"]["items"]:
   artists = ""
   for artist in song["track"]["artists"]:
      artists += artist["name"]+","
   artists = artists.removesuffix(",")
   video = youtube_search.YoutubeSearch(f"{song["track"]["name"]} - {artists}",max_results=1).to_dict()[0]
   videoID = video["id"]
   if videoID in downloaded_songs.keys():
      pass
   else:
      info = ytdlp.extract_info(f"https://www.youtube.com/watch?v={videoID}",download=True)
      filename = ytdlp.prepare_filename(info)
      downloaded_songs[videoID] = {"file":filename,"title":info["title"]}
   
   print(f"{song["track"]["name"]} - {artists} [{videoID}]")
   songQueue.append(downloaded_songs[videoID])

#Discord Bot
intents = discord.Intents.default()

bot = commands.Bot(command_prefix='!',intents=intents)

#Discord IDs
discordServerID = "REPLACE WITH SERVER ID"
discordVoiceChannelID = "REPLACE WITH THE VOICE CHANNEL ID THAT THE BOT WILL BE IN"

@bot.event
async def on_ready():
   await start()

#Index in the queue
currentSong = -1
random.shuffle(songQueue)

async def start():
   global currentSong
   voice = discord.utils.get(bot.voice_clients, guild=bot.get_guild(discordServerID))
   VoiceChannel = bot.get_channel(discordVoiceChannelID)
   print(voice)
   print(VoiceChannel)
   #Join voice channel
   if not voice or not voice.is_connected():
      voice = await VoiceChannel.connect()
   print(voice)
   currentSong += 1
   if currentSong >= len(songQueue):
      currentSong = 0
      random.shuffle(songQueue)
   source = discord.FFmpegOpusAudio(songQueue[currentSong]["file"],executable="C:/Program Files/ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe")
   voice.play(source,after=lambda e: asyncio.run_coroutine_threadsafe(start(), bot.loop))
   await bot.change_presence(activity=discord.CustomActivity(f"Playing {song["title"]}"))

bot.run(botSecret)
