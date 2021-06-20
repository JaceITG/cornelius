import discord, random
from aioconsole import ainput
import cornelius_storage

intents = discord.Intents.all()
client = discord.Client(intents=intents)

#On bot startup/ready
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

    await client.change_presence(activity=discord.Game(name=f"use {cornelius_storage.PREFIX}help for help!"))

#On message received
@client.event
async def on_message(message):
    if message.author == client.user or message.content == None:
        return

    if message.guild == None:
        #Message is a dm
        print(f"DM received from {message.author}")

        #If not from dev, forward to dev
        if message.author.id != cornelius_storage.ADMIN_ID[0]:
            dmForward = f"Message from {message.author.name} (ID: {message.author.id}): {message.content}"
            dev = client.get_user(int(cornelius_storage.ADMIN_ID[0]))
            await sendMsg(dmForward,dev)

    #Check if admin command
    if message.author.id in cornelius_storage.ADMIN_ID:
        await adminCmd(message)

    #Check if prefixed command
    if message.content.startswith(cornelius_storage.PREFIX):
        await prefixed(message)
    else:
        await implicit(message)

#Prefixed commands
async def prefixed(message):
    #### Message property variables ####
    cmd = message.content[len(cornelius_storage.PREFIX):]
    args = cmd.split(' ')
    lower = cmd.lower()
    argsLower = lower.split(' ')
    author = message.author
    channel = message.channel
    guild = message.guild
    ####################################

    if cmd == "help":
        await sendEmbed(cornelius_storage.HELP_EMBED, channel)

    if cmd == "cornfact" or cmd == "cf":
        fact = random.choice(cornelius_storage.CORN_FACTS)
        await sendEmbed(discord.Embed(title="Corn Fact",description=fact, color=discord.Colour(12745742)), channel)

#Implicit commands
async def implicit(message):
    #### Message property variables ####
    text = message.content
    lower = text.lower()
    channel = message.channel
    author = message.author
    ####################################

    if lower == "ping":
        await sendMsg("pong", channel)

    if channel.id == cornelius_storage.CORN_FIELD_ID:
        await check_corn(message)
    elif text.strip() == "🌽":
        #25% chance to respond to corn outside of corn-field
        if random.randint(1,4)==1:
            corn_resps = ["🌽","God I fucking love corn!!","Yum","hmmm yes I think this is corn..","🌽"]

            await sendMsg(random.choice(corn_resps),channel)
    

#Admin commands
async def adminCmd(message):
    text = message.content
    channel = message.channel
    lower = text.lower()
    guild = message.guild
    #Implicits

    #Prefixed
    if text == '' or text[0] != cornelius_storage.PREFIX:
        return
    cmd = text[1:].split(" ")


    if cmd[0]=='dm':
        #Intended recipient ID
        dmUser = client.get_user(int(cmd[1]))
        dmMsg = ' '.join(cmd[2:])
        await sendMsg(dmMsg,dmUser)

#######################################################
################## Utility Functions ##################
#######################################################

#Sends text to given channel
async def sendMsg(msg, channel):
    try:
        print(f"Sending message to {channel.name}: \n\t-\"{msg}\"")
        return await channel.send(msg)
    except:
        print(f"Error while attempting to send message to {channel.name}")

#Sends embed to given channel, Optional: pass content to go with it
async def sendEmbed(msg, channel, cntnt=None):
    try:
        await channel.send(content=cntnt,embed=msg)
        print(f"Sent embed to {channel.name}: {msg.title}")
    except:
        print(f"Error while attempting to send embed to {channel.name}")

#Sends a file from an absolute local path
async def sendFile(fp, channel, cntnt=None):
    imgFile = discord.File(fp)
    try:
        await channel.send(content=cntnt,file=imgFile)
        print(f"Sent file to {channel.name}: {fp}")
    except:
        print(f"Error while attempting to send {fp} to {channel.name}")

#Return url string of most recently posted image
async def getLastImg(chan):
    async for message in chan.history(limit=100):
        if len(message.attachments) >= 1:
            return message.attachments[0].url
    return None

async def check_corn(message):
    if message.content.strip() != "🌽":
        #PUNISH THE HERETIC
        heretic = message.guild.get_role(cornelius_storage.HERETIC_ROLE_ID)
        await message.author.add_roles(heretic)
        
        #Display offending message
        shame_embed = discord.Embed(title=f"⚠️ WARNING: CRIMES AGAINST CORN COMMITTED BY {message.author.display_name} ⚠️", color=discord.Colour(15158332))
        shame_embed.set_thumbnail(url=message.author.avatar_url)
        shame_embed.add_field(name="Instead of posting 🌽 in #corn-field as the Corn Gods intended, they posted:", value=f"\"{message.content}\"")
        shame_embed.set_footer(text="Shame on them!")

        #send to general chat
        main_chat = message.guild.get_channel(cornelius_storage.MAIN_CHAT_ID)
        await sendEmbed(shame_embed,main_chat)
        await message.delete()

client.run(cornelius_storage.TOKEN)
