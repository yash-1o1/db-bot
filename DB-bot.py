## Importing the libraries needed
import config
import discord
import asyncio
from discord.ext import commands 

bot = commands.Bot(command_prefix='/', intents = discord.Intents.all())

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

@bot.tree.command(
    name="moveto", 
    description="Move to a user's channel"
)
async def moveto(interactions, user: discord.Member):
    target_user = user
    command_user = interactions.user

    # Preliminary checks for errors
    if target_user.voice is None or target_user.voice.channel is None:
        await interactions.response.send_message(f"{target_user.mention} is not in a voice channel.", ephemeral=True)
        return
    elif command_user.voice is None or command_user.voice.channel is None:
        await interactions.response.send_message("You are not in a voice channel.", ephemeral=True)
        return

    target_channel = target_user.voice.channel
    command_channel = command_user.voice.channel

    # Check if the target user is in the same channel as the command user
    if target_channel == command_channel:
        await interactions.response.send_message(f"You are already in the target user's channel.", ephemeral=True)
        return

    # Send an approval message to the target user
    await interactions.response.send_message(f"Waiting for approval", ephemeral=True)
    approval_message = await interactions.channel.send(f"{target_user.mention}, {command_user.mention} wants to move to your channel. Do you approve?")
    await approval_message.add_reaction('✅')
    await approval_message.add_reaction('❌')

    # Define a check function for the reaction event
    def check(reaction, user):
        return user == target_user and str(reaction.emoji) in ['✅', '❌'] and reaction.message.id == approval_message.id

    try:
        # Wait for the target user's reaction
        reaction, _ = await bot.wait_for('reaction_add', timeout=60, check=check)
    except asyncio.TimeoutError:
        # If no reaction within the timeout, abort the move request
        await interactions.edit_original_response(content=f"The move request timed out. Aborting.")
        return

    if str(reaction.emoji) == '❌':
        # If the target user denies the move request
        await interactions.edit_original_response(content=f"{target_user.mention} denied the move request.")
    elif reaction.emoji == "✅":
        try:
            # Attempt to move the command user to the target user's channel
            await interactions.edit_original_response(content=f"Moved {command_user.mention} to {target_user.mention}'s channel.")
            await command_user.move_to(target_channel)
        except discord.errors.HTTPException:
            # If an error occurs while moving the user
            await interactions.edit_original_response(content=f"Failed to move the user.")

bot.run(config.TOKEN)