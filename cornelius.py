import discord, random, asyncio, pprint
from aioconsole import ainput
from discord import embeds
import cornelius_storage

intents = discord.Intents.all()
client = discord.Client(intents=intents)

count_li = []

#On bot startup/ready
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

    await client.change_presence(activity=discord.Game(name=f"use {cornelius_storage.PREFIX}help for help!"))

    await harvest_loop()

@client.event
async def on_reaction_add(reaction, user):
    message = reaction.message
    emoji = reaction.emoji
    embed = message.embeds

    if user == client.user:
        return
    
    #Pagination for Leaderboard
    if embed and embed[0].title == "🌽 Corn Leaderboard 🌽":
        await handle_pagination(reaction, user)

@client.event
async def on_reaction_remove(reaction, user):
    message = reaction.message
    emoji = reaction.emoji
    embed = message.embeds

    if user == client.user:
        return
    
    #Pagination for Leaderboard
    if embed and embed[0].title == "🌽 Corn Leaderboard 🌽":
        await handle_pagination(reaction, user)

#Cycle through pages of embed in reaction.message based on reacted emoji
async def handle_pagination(reaction, user):
    message = reaction.message
    emoji = reaction.emoji
    embed = message.embeds

    properties = embed[0].to_dict()
    current_page = int(properties['footer']['text'].split(' ')[1])

    if emoji == "⬅️":
        new_page = current_page-1
    elif emoji == "➡️":
        new_page = current_page+1
    else:
        return
    
    new_embed = await get_harvest_embed(None, count_li, page=new_page)
    await message.edit(embed=new_embed)

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
    
    if cmd == "corncount" or cmd== "cc":
        global count_li

        #Sort dictionary entries into a k,v pair list

        emb = await get_harvest_embed(author, count_li)
        sent = await sendEmbed(emb, channel)
        await sent.add_reaction("⬅️")
        await sent.add_reaction("➡️")


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
    
    if cmd[0] == "forceharvest":
        await harvest_corn(cornelius_storage.CORN_FIELD_ID)

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
        sent = await channel.send(content=cntnt,embed=msg)
        print(f"Sent embed to {channel.name}: {msg.title}")
        return sent
    except:
        print(f"Error while attempting to send embed to {channel.name}")

#Sends a file from an absolute local path
async def sendFile(fp, channel, cntnt=None):
    imgFile = discord.File(fp)
    try:
        sent = await channel.send(content=cntnt,file=imgFile)
        print(f"Sent file to {channel.name}: {fp}")
        return sent
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

#Create a dict storing amount of :corn:s sent by each user
async def harvest_corn(channel):
    global count_li

    #initialize dict
    corn_counts = {}
    for memb in channel.guild.members:
        corn_counts[memb] = 0

    async for msg in channel.history(limit=999999):
        try:
            corn_counts[msg.author] += 1
        except KeyError:
            #Skip count if user not in dict; probably means user has left the server
            pass
    
    #Create sorted list based on the dictionary
    count_li = []
    for i in corn_counts.items():
        count_li.append(i)
    
    count_li.sort(key=lambda x: x[1], reverse=True)

async def harvest_loop(period_mins=180):
    field_chan = client.get_channel(cornelius_storage.CORN_FIELD_ID)

    while True:
        await harvest_corn(field_chan)
        await asyncio.sleep(period_mins*60)

#Construct a paginated leaderboard embed using sorted (userid,)
async def get_harvest_embed(author, li, page=1, page_len=10):

    if len(li)%page_len == 0:
        #edge cases (i.e. numplayers 20 length 10, we need 2 pages not 3)
        #this is probably bad way to handle it and im failing at easy math lol
        max_page = (len(li)//(page_len))
    else:
        max_page = (len(li)//(page_len)) +1

    #Page looparound for page>max_page
    if page>max_page:
        page %= max_page
    elif page<=0:
        page = max_page-page

    desc = f"Rank     Name       [Page {page}/{max_page}]\n"

    #Find index range for requested page
    start = (page-1)*page_len
    end = min(start+page_len,len(li))

    for i in range(start,end):
        #Add listing to desc for each user
        curr_user = li[i]
        name = curr_user[0].display_name
        #truncate usernames to 15 char
        if len(name)>15:
            name = name[:12] + "..."

        desc+= f"{i+1: <4}➤   {name: <15}  {curr_user[1]: 3} 🌽\n"
    desc+="____________________________________\n"

    #if author is in the member entry of a list item
    member_list = [x[0] for x in li]
    if author in member_list:
        author_ind = member_list.index(author)
        desc += f"Your Rank: {author_ind+1: <15}  {li[author_ind][1]: 3} 🌽"

    embed = discord.Embed(title="🌽 Corn Leaderboard 🌽", description=f"```{desc}```", color=discord.Colour(12745742))
    embed.set_thumbnail(url=cornelius_storage.CORNFIELD_IMG)
    embed.set_footer(text=f"Page {page}")
    return embed

client.run(cornelius_storage.TOKEN)
