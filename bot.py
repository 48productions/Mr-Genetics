#!/usr/bin/python

import asyncio
import discord
from discord.ext import commands
from discord.utils import get

import config_man
import playing_messages


intents = discord.Intents(guilds=True, members=True, emojis=True, messages=True, guild_reactions=True)  # Set our intents - Subscribes to certain types of events from discord

bot = commands.Bot(command_prefix='!', case_insensitive=True, intents=intents)

bot.remove_command('help')  # Remove the default help command, imma make my own lel

rolelist_messages = {}  # A list of rolelist messages to track, stored as {(channel id, message id), category}
for category, ids in config_man.categories.items():  # Let's initialize that list with the values stored in each category in the config
    id_list = ids.split(';')
    if id_list[0] != '-1':  # Only add valid category messages to the rolelist messages list: -1 means a category doesn't have a rolelist message
        rolelist_messages[(int(id_list[0]), int(id_list[1]))] = category

# Temporary tracking variables for the addrole command - Helps persist some data between the command being run and the emoji reaction to confirm it
addrole_message = [0, 0]
addrole_role = ""
addrole_dispname = ""
addrole_description = ""
addrole_category = ""
addrole_editing = False
addrole_assignable = False

# Also track stuff for the removerole command
removerole_message = [0, 0]
removerole_category = ""
removerole_role = ""

# ...and the "setadminrole" command...
setadmin_message = [0, 0]
setadmin_role = ""

@bot.event
async def on_ready():
    global admin_role
    print('Logged on as ', bot.user)
    bot.loop.create_task(change_status())  # Also start the "change status every so often" task, too


# Argument test commands
#@bot.command()
#async def hoi(ctx, arg): # Interprets first "arg" (up to first space)
#    await ctx.send('Bruh, ' + arg)


#@bot.command()
#async def boi(ctx, *, arg): # Interprets all remaining arguments as one ("keyword-only")
#    await ctx.send('Bruv, ' + arg)


# Adds a role to the config
# Usage: addrole <category in quotes> <role name in quotes> Role description (no quotes)
@bot.command()
async def addrole(ctx, category, role: discord.Role, *, desc=""): # argument: discord.XYZ converts this argument to this data type (i.e. turn a string into a role)
    if not isinstance(ctx.channel, discord.DMChannel) and isinstance(ctx.author, discord.Member) and authorize_admin(ctx.guild, ctx.author):  # First: Confirm that it's a member (of a guild) we're being given, and then authorize them as an admin
        roles = config_man.get_roles(category)  # First, let's do some sanity checks:
        if roles is not False:  # A valid dict of roles was returned, run some checks only if this is the case
            if len(roles) >= 20:  # Discord limits reactions to 20 per message (afaik), so prevent adding a 21st role to a category
                await ctx.send(embed=format_embed("Error: A category can't have more than 20 roles!\nThis is a discord reaction limitation, sorry :(", True))
                return

            if str(role.id) in roles.keys():  # Prevent having the same role pop up multiple times in the category (probably doesn't break anything tbh, it just sounds dumb)
                await ctx.send(embed=format_embed("Error: This role is already in this category!", True))
                return

        if role.id == config_man.get_admin_role():  # Prevent adding the admin role to a category (giving random users your admin role doesn't seem smart)
            await ctx.send(embed=format_embed("Error: " + role.name + " is this bot's config admin role - You cannot add it to the role list!", True))
            return

        permissions = role.permissions
        if permissions.administrator:  # Prevent adding any admin roles for the guild
            await ctx.send(embed=format_embed("Error: " + role.name + " is an admin role in this server - You cannot add it to the role list!", True))
            return

        global addrole_message, addrole_role, addrole_description, addrole_category, addrole_dispname, addrole_editing, addrole_assignable
        embed = discord.Embed(title="Will attempt to add a role", colour=0x4EDB23)
        msg_text = '\n**Role: **' + role.name
        msg_text += '\n**Category: **' + category
        msg_text += '\n**Description: **' + desc
        msg_text += '\n**Assignable: True** - Any user can obtain this role!'
        msg_text += '\n\nTo confirm add: React to this message with the emote to listen for!'
        addrole_role = str(role.id)
        addrole_dispname = role.name
        addrole_category = category
        addrole_description = desc
        addrole_editing = False
        addrole_assignable = True

        # Finally, warn against adding roles with potentially "dangerous" permissions at the bottom of the message
        if permissions.kick_members or permissions.ban_members or permissions.manage_channels or permissions.manage_guild or permissions.manage_messages or permissions.mute_members or permissions.deafen_members:
            msg_text += "\n\n⚠ **Warning: Role " + role.name + " has potentially dangerous permissions.**\nRoles and permissions added to the role list can be obtained by *ANY* user."

        embed.description = msg_text
        msg = await ctx.send(embed=embed)
        addrole_message[0] = msg.channel.id
        addrole_message[1] = msg.id
        print("Sent addrole message: ", msg.id)
        return


# Adds a role to the config
# Usage: addrole <category in quotes> <role name in quotes> Role description (no quotes)
@bot.command()
async def adddisprole(ctx, category, role: discord.Role, *, desc=""): # argument: discord.XYZ converts this argument to this data type (i.e. turn a string into a role)
    if not isinstance(ctx.channel, discord.DMChannel) and isinstance(ctx.author, discord.Member) and authorize_admin(ctx.guild, ctx.author):  # First: Confirm that it's a member (of a guild) we're being given, and then authorize them as an admin
        roles = config_man.get_roles(category)  # First, let's do some sanity checks:
        if roles is not False:  # A valid dict of roles was returned, run some checks only if this is the case
            if len(roles) >= 20:  # Discord limits reactions to 20 per message (afaik), so prevent adding a 21st role to a category
                await ctx.send(embed=format_embed("Error: A category can't have more than 20 roles!\nThis is a discord reaction limitation, sorry :(", True))
                return

            if str(role.id) in roles.keys():  # Prevent having the same role pop up multiple times in the category (probably doesn't break anything tbh, it just sounds dumb)
                await ctx.send(embed=format_embed("Error: This role is already in this category!", True))
                return

        global addrole_message, addrole_role, addrole_description, addrole_category, addrole_dispname, addrole_editing, addrole_assignable
        embed = discord.Embed(title="Will attempt to add a display role", colour=0x4EDB23)
        msg_text = '\n**Role: **' + role.name
        msg_text += '\n**Category: **' + category
        msg_text += '\n**Description: **' + desc
        msg_text += '\n**Assignable: False**'
        msg_text += '\n\nTo confirm add: React with 🛡 to confirm!'
        addrole_role = str(role.id)
        addrole_dispname = role.name
        addrole_category = category
        addrole_description = desc
        addrole_editing = False
        addrole_assignable = False

        embed.description = msg_text
        msg = await ctx.send(embed=embed)
        addrole_message[0] = msg.channel.id
        addrole_message[1] = msg.id
        await msg.add_reaction('🛡')
        print("Sent adddisprole message: ", msg.id)
        return


# Edits a role in the config
@bot.command()
async def editrole(ctx, category, role: discord.Role, *, desc=""): # argument: discord.XYZ converts this argument to this data type (i.e. turn a string into a role)
    if not isinstance(ctx.channel, discord.DMChannel) and isinstance(ctx.author, discord.Member) and authorize_admin(ctx.guild, ctx.author):  # First: Confirm that it's a member (of a guild) we're being given, and then authorize them as an admin
        roles = config_man.get_roles(category)  # First, let's do some sanity checks:
        if roles is False:  # Confirm that our role list is valid (if it's false, the category is invalid)
            await ctx.send(embed=format_embed("Error getting roles for category \"" + category + "\" - does this category exist?", True))
            return

        if str(role.id) not in roles.keys():  # If our role list is correct, make sure the role we want to edit is valid, too
            await ctx.send(embed=format_embed("Error: Role \"" + role.name + "\" not found in category \"" + category + "\"!", True))
            return

        global addrole_message, addrole_role, addrole_description, addrole_category, addrole_dispname, addrole_editing, addrole_assignable
        addrole_assignable = config_man.is_role_assignable(category, role.id)
        embed = discord.Embed(title="Will attempt to edit a role", colour=0x4EDB23)
        msg_text = '\n**Role: **' + role.name
        msg_text += '\n**Category: **' + category
        msg_text += '\n**Description: **' + desc
        msg_text += '\n**Assignable: **' + str(addrole_assignable)
        msg_text += '\n\nRole will be removed and re-added with these values.'
        msg_text += '\nTo confirm: React to this message with ' + ('the emote to listen for!' if addrole_assignable else '🛡!')
        addrole_role = str(role.id)
        addrole_dispname = role.name
        addrole_category = category
        addrole_description = desc
        addrole_editing = True


        embed.description = msg_text
        msg = await ctx.send(embed=embed)
        addrole_message[0] = msg.channel.id
        addrole_message[1] = msg.id
        if not addrole_assignable:
            await msg.add_reaction('🛡')
        print("Sent editrole message: ", msg.id)
        return


# Removes a role from the config
# Usage: removerole <role category in quotes> <role name in quotes>
@bot.command()
async def removerole(ctx, category, role: discord.Role):
    if not isinstance(ctx.channel, discord.DMChannel) and isinstance(ctx.author, discord.Member) and authorize_admin(ctx.guild, ctx.author):  # First: Confirm that it's a member (of a guild) we're being given, and then authorize them as an admin
        global removerole_message, removerole_category, removerole_role
        role_list = config_man.get_roles(category)
        if role_list is False:  # Sanity check we're being given a valid category
            await ctx.send(format_embed("Error: Category " + category + " not found!", True))
            return

        embed = discord.Embed(title="Will attempt to remove a role", colour=0xDB2323)
        msg_text = '\n**Category:** ' + category
        msg_text += '\n**Role: **' + role.name
        if len(role_list) <= 1:  # If this is the only role in the category, the category will be removed as well
            msg_text += '\n**This category will be empty (and thus removed) if this role is removed. It\'s rolelist message will be deleted if it exists, too.**'
        msg_text += '\n\nTo confirm removal: React with ❌'
        removerole_category = category
        removerole_role = str(role.id)

        embed.description = msg_text
        msg = await ctx.send(embed=embed)
        removerole_message[0] = msg.channel.id
        removerole_message[1] = msg.id
        await msg.add_reaction('❌')
        print("Sent removerole message: ", msg.id)
        return



# Updates the "role list" messages if they exist - Users can react to these messages for roles assignments
# Usage: rolelist
@bot.command()
async def rolelist(ctx):
    await generateRoleList(ctx, False)


# Sends new "role list" messages, deleting old ones in the process
@bot.command()
async def newrolelist(ctx):
    await generateRoleList(ctx, True)

# Generates a role list, either deleting the old messages and sending new ones or updating the existing messages
async def generateRoleList(ctx, sendNew):
    if not isinstance(ctx.channel, discord.DMChannel) and isinstance(ctx.author, discord.Member) and authorize_admin(ctx.guild, ctx.author):  # First: Confirm that it's a member (of a guild) we're being given, and then authorize them as an admin
            if not config_man.categories:  # Are no categories loaded?
                await ctx.send(embed=format_embed("No role categories to display found! Add some roles to the rolelist with !addrole or !adddisprole.", True))
                return

            global rolelist_messages

            if sendNew:  # Generating a new role list? Delete the old messages we're tracking first
                # First, delete all the old rolelist messages we're tracking (if any) and clear the list of messages to track
                for message in rolelist_messages.keys():
                    # print(message)
                    try:
                        msg = await bot.get_channel(message[0]).fetch_message(message[1])
                        await msg.delete()
                    except discord.errors.NotFound:
                        print("Received 404 trying to delete message with ID " + str(message[1]) + ", was it already deleted?")
                rolelist_messages.clear()


            categorydescriptions = config_man.get_category_descriptions()
            for category, ids in config_man.categories.items():  # Send a rolelist message for each category
                embed = discord.Embed(title=category, colour=0xFF7D00)  # Create an embed, set it's title and color
                msg_text = categorydescriptions[category] if categorydescriptions[category] is not None else "React with these emotes to get roles!"  # Grab this category's description from the config (if there is one), otherwise use some placeholder text
                msg_text += "\n"
                emojis = config_man.get_roles_emoji(category)
                for role_id, desc in config_man.get_roles(category).items():  # Grab the roles from this category, and add their name/descriptions to the message to send
                    role = get(ctx.guild.roles, id=int(role_id))
                    msg_text += "\n "

                    if config_man.is_role_assignable(category, role_id):  # Is this role assignable? If so, add its emote!
                        if emojis[role_id][1] == 'True':  # Custom emoji - Find emoji in guild and then insert it
                            msg_text += str(get(ctx.guild.emojis, name=emojis[role_id][0]))
                        else:  # Unicode emoji - Print emoji normally (since it's just stored as a unicode string)
                            msg_text += emojis[role_id][0]
                    
                    if desc == '':
                        msg_text += "  **" + role.name + "**"
                    else:
                        msg_text += "  **" + role.name + "** - " + desc

                embed.description = msg_text  # Set the embed's description to our role list text

                msg = None
                updated_msg = False
                if not sendNew:  # Hol up, if we want to update the existing lists, check if this category already has a message
                    id_list = ids.split(';')
                    if id_list[0] != '-1' and id_list[1] != '-1':  # There's *probably* a valid message to update?
                        msg = await bot.get_channel(int(id_list[0])).fetch_message(int(id_list[1]))
                        await msg.edit(embed=embed)
                        print("Edited existing role list message for \"" + category + "\": ", msg.id)
                        updated_msg = True

                if not updated_msg:  # Wasn't able to edit an existing category message? That's cool just send a new one
                    msg = await ctx.send(embed=embed)
                    print("Sent role new list message for \"" + category + "\": ", msg.id)

                rolelist_messages[(msg.channel.id, msg.id)] = category  # Store this message's channel/message IDs for later - We'll use them to track these messages for reactions
                config_man.set_category_message(category, str(msg.channel.id), str(msg.id))  # Also save these values to the config as well

                cur_emoji_list = []
                if updated_msg:  # If we're updated an existing message, check if we should remove any (of our) reactions for roles that no longer exist:
                    new_emoji_list = []

                    for item in emojis.values():  # First, grab a list of all the emojis associated with roles in this category
                        new_emoji_list.append(item[0])

                    for reaction in msg.reactions:  # Now go through all of this message's reactions
                        if isinstance(reaction.emoji, discord.Emoji) or isinstance(reaction.emoji, discord.PartialEmoji):
                            emote = reaction.emoji.name
                        else:  # We're probably being given a unicode string as an emoji???
                            emote = reaction.emoji

                        if reaction.me:
                            if emote not in new_emoji_list:  # If we've used this reaction and that reaction no longer belongs to a role, remove our reaction to it!
                                await reaction.remove(bot.user)
                                await asyncio.sleep(0.5)
                            else:  # We've used this reaction and it does belong to a role, add it to the list of reactions we currently have
                                cur_emoji_list.append(emote)

                for role, emoji in emojis.items():  # React with the emotes for all assignable roles in this category

                    # Add this emote as a reaction if this role is assignable AND EITHER:
                    #    - We're sending a new role list OR
                    #    - We're updating a role list and we haven't reacted with this emote yet (it isn't in cur_emoji)list)
                    if config_man.is_role_assignable(category, role) and (not updated_msg or (updated_msg and emoji[0] not in cur_emoji_list)):
                        await asyncio.sleep(0.5)  # Wait a bit to appease rate limits (discordpy apparently does some stuff internally too, this prolly can't hurt tho
                        if emoji[1] == 'True':  # This is a custom emoji, grab an emoji instance before use
                            await msg.add_reaction(get(ctx.guild.emojis, name=emoji[0]))
                        else:  # No fancy emoji conversion needed otherwise, unicode emojis can be passed into add_reaction as-is
                            await msg.add_reaction(emoji[0])

                await asyncio.sleep(1)  # *bows down to discord api*

            config_man.save_config()  # We've updated some entries in the config for message IDs to listen for reactions on, don't forget to save these!
            return


# Sets the admin role in the config
@bot.command()
async def setadminrole(ctx, role: discord.Role):
    if not isinstance(ctx.channel, discord.DMChannel) and isinstance(ctx.author, discord.Member) and authorize_admin(ctx.guild, ctx.author):  # First: Authorize an admin is running this command
        global setadmin_message, setadmin_role
        if role is not None:
            embed = discord.Embed(title="Will set the admin role", colour=0xFF7D00)  # Create an embed, set it's title and color
            embed.description = "**Role:** " + role.name + "\n\nUsers without this role can't edit or send the role list, and can only react to it for roles.\n\n**Ensure you have this role and react with 🔒 to confirm!**"
            msg = await ctx.send(embed=embed)
            setadmin_message[0] = msg.channel.id
            setadmin_message[1] = msg.id
            setadmin_role = str(role.id)
            await msg.add_reaction('🔒')
            print("Sent setadminrole message: ", msg.id)
        else:
            await ctx.send(embed=format_embed("Invalid role given!", True))  # This might not even get reached, on_command_error() might intercept things first


# Sorts the roles in a category by alphabetical order
@bot.command()
async def sortcategory(ctx, category):
    if not isinstance(ctx.channel, discord.DMChannel) and isinstance(ctx.author, discord.Member) and authorize_admin(ctx.guild, ctx.author):  # First: Authorize an admin is running this command
        msg = config_man.sort_category(category)
        await ctx.send(embed=format_embed(msg, False))


# Sets the description of a category
@bot.command()
async def setcategorydescription(ctx, category, *, description=""):
    if not isinstance(ctx.channel, discord.DMChannel) and isinstance(ctx.author, discord.Member) and authorize_admin(ctx.guild, ctx.author):  # First: Authorize an admin is running this command
        msg = config_man.set_category_description(category, description)
        await ctx.send(embed=format_embed(msg, False))


# Sends an introduction message, da-don!
@bot.command()
async def introduction(ctx):
    if not isinstance(ctx.channel, discord.DMChannel) and isinstance(ctx.author, discord.Member) and authorize_admin(ctx.guild, ctx.author):  # First: Authorize an admin is running this command
        await ctx.send("*Musical quack*, da-don 🦆")


# A help command that DMs the sender with command info
@bot.command()
async def help(ctx):
    if not isinstance(ctx.channel, discord.DMChannel) and isinstance(ctx.author, discord.Member) and authorize_admin(ctx.guild, ctx.author):  # First: Authorize an admin is running this command
        embed = discord.Embed(title="Command Help", colour=0xFF7D00)  # Create an embed, set it's title and color
        embed.description = "\n`help:` Get sent this list\n\n" \
                            "`addrole \"Category\" \"Role\" Description:`  Adds an assignable role to the role list\n\n" \
                            "`adddisprole \"Category\" \"Role\" Description:`  Adds a non-assignable role to the role list\n\n" \
                            "`editrole \"Category\" \"Role\" Description:`  Removes and re-adds a role to the role list\n\n" \
                            "`removerole \"Category\" \"Role\":`  Removes a role from the role list\n\n" \
                            "`rolelist:`  Sends/updates the role list messages to the current channel\n\n" \
                            "`newrolelist:`  Deletes the old role list and sends a new one to the current channel\n\n" \
                            "`setadminrole \"Role\":`  Sets a role as this bot's \"admin\" role\n\n" \
                            "`sortcategory \"Category\":`  Sorts the roles in a category (alphabetical order)\n\n" \
                            "`setcategorydescription \"Category\" Description:` Sets a category's description (optional)\n\n" \
                            "Note:  If an admin role is set, you'll need that role to run ANY commands!"
        await ctx.author.send(embed=embed)
        await ctx.send(embed=format_embed("DM'd ya fam 😉", False))


@bot.event
async def on_raw_reaction_add(payload):
    await handle_reaction(payload, True)


@bot.event
async def on_raw_reaction_remove(payload):
    await handle_reaction(payload, False)


# Handles the add and remove reaction events for ALL messages on servers the bot is in
async def handle_reaction(payload, reaction_added):
    if payload.user_id == bot.user.id or payload.guild_id is None:  # Don't process reactions we've added ourselves or aren't in a guild (probably in DMs?)
        return
    global addrole_message, addrole_role, addrole_description, addrole_category, addrole_dispname, addrole_editing, addrole_assignable, removerole_message, removerole_category, removerole_role, setadmin_message, setadmin_role

    guild = bot.get_guild(payload.guild_id)  # Grab the guild we're in and the member that reacted for later
    member = guild.get_member(payload.user_id)

    # Reaction processing 1: ROLELIST MESSAGES (available to all server users)
    for tracked_message in rolelist_messages:
        if payload.channel_id == tracked_message[0] and payload.message_id == tracked_message[1]:  # Only process messages that we are listening for reactions on. Here, we'll process reactions on the role list messages
            # print("\nRolelist reaction!\nUser: ", payload.user_id, "\nChannel: ", payload.channel_id, "\nMessage: ", payload.message_id, "\nEmoji: ", payload.emoji.name, "\nEvent: ", payload.event_type)

            for category, category_message in config_man.categories.items():  # Next, let's find the category of the message we just reacted to:
                category_ids = category_message.split(';')
                if payload.channel_id == int(category_ids[0]) and payload.message_id == int(category_ids[1]):  # Did we find the category?
                    roles = config_man.get_roles_emoji(category)  # Grab the roles in the category message the member reacted on

                    for role_id, role_emoji in roles.items():  # Now find the role to add - Go through each role until we find the one with the emoji the member reacted with
                        # print(payload.emoji.name, ", ", role_emoji)
                        if payload.emoji.name == role_emoji[0]:  # Once we find it, toggle this role on the user!
                            role = get(guild.roles, id=int(role_id))

                            if config_man.is_role_assignable(category, str(role.id)):  # Check to make sure we are allowed to assign this role to regular users!
                                if not reaction_added:  # Member removed this reaction, take the role away!
                                    print("Removing role " + role.name + " from member " + member.display_name)
                                    await member.remove_roles(role, reason="Self-removed via bot (by reaction)")
                                    # print("Removed role")
                                else:  # Member added the reaction, add the role!
                                    print("Adding role " + role.name + " to member " + member.display_name)
                                    await member.add_roles(role, reason="Self-assigned via bot (by reaction)")
                                    # print("Added role ")
                                return  # Done adding this role, don't process anything else

    # Reaction processing 2: Add/remove role reactions - Only available to admins!
    if authorize_admin(guild, member):
        if payload.channel_id == addrole_message[0] and payload.message_id == addrole_message[1]:  # Check for reactions on the latest "addrole" message
            print("\nAdd/edit role reaction!\nID: ", payload.message_id, "Emoji: ", payload.emoji.name)

            if addrole_assignable:  # Run some sanity checks depending on whether we're adding an assignable role or not
                if payload.emoji.is_custom_emoji():  # Using a custom emoji? Make sure the bot can actually use it, too
                    emoji = get(guild.emojis, id=payload.emoji.id)
                    if emoji is None or emoji.available is False:
                        await bot.get_channel(payload.channel_id).send(embed=format_embed("Error: I can't use that custom emoji, try reacting with a different emote.", True))
                        return

            else:  # Not an assignable role, only process if the added reaction is the confirmation shield
                if payload.emoji.name != '🛡' and payload.emoji.name != '🛡️':  # wth why are there two shields???
                    return

            if addrole_editing:  # If we're editing a role, we want to remove the existing role before we add a new one with the new parameters
                remove_result = config_man.remove_role(addrole_category, addrole_role)
                if remove_result is False:
                    await bot.get_channel(payload.channel_id).send(embed=format_embed("Role edit macro failed!\n" + remove_result, True))
                    addrole_message = [0, 0]
                    return

            add_result = config_man.add_role(addrole_category, addrole_role, addrole_dispname, payload.emoji.name, addrole_description, payload.emoji.is_custom_emoji(), addrole_assignable)
            if add_result is True:
                msg = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
                await msg.add_reaction('\N{THUMBS UP SIGN}')
            else:
                await bot.get_channel(payload.channel_id).send(embed=format_embed(add_result, True))
            addrole_message = [0, 0]  # Don't forget to blank out the addrole message so we stop listening for reactions on the message we just reacted on!

        if payload.channel_id == removerole_message[0] and payload.message_id == removerole_message[1] and payload.emoji.name == '❌':  # Check for reactions on the latest "removerole" message
            remove_result = config_man.remove_role(removerole_category, removerole_role)
            if remove_result is True or isinstance(remove_result, list):
                msg = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
                await msg.add_reaction('\N{THUMBS UP SIGN}')

                if isinstance(remove_result, list) and remove_result[0] != -1:  # If we got returned a list, it means this category is now empty. If list[0] isn't -1, it means we should delete the old rolelist message for that category, too
                    msg = await bot.get_channel(remove_result[0]).fetch_message(remove_result[1])
                    await msg.delete()
                    await bot.get_channel(payload.channel_id).send(embed=format_embed("This category is now empty! Removed category and deleted its role list message", False))

            else:
                await bot.get_channel(payload.channel_id).send(embed=format_embed(remove_result, True))
            removerole_message = [0, 0]  # Don't forget to blank out the removerole message so we stop listening for reactions on the message we just reacted on!

        if payload.channel_id == setadmin_message[0] and payload.message_id == setadmin_message[1] and payload.emoji.name == '🔒':  # Check for reactions on the latest "setadminrole" message
            set_result = config_man.set_admin_role(setadmin_role)
            if set_result is True:
                msg = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
                await msg.add_reaction('\N{THUMBS UP SIGN}')
            else:
                await bot.get_channel(payload.channel_id).send(embed=format_embed(set_result, True))
            setadmin_message = [0, 0]  # Don't forget to blank out the addrole message so we stop listening for reactions on the message we just reacted on!


    # Endif: Admin auth


@bot.event
async def on_command_error(ctx, error):
    if isinstance(ctx.author, discord.Member) and authorize_admin(ctx.guild, ctx.author):  # Invalid commands run by non-admins can still display error messages - Prevent that here
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=format_embed('Missing arguments!', True))
            return
        if isinstance(error, commands.BadArgument):
            await ctx.send(embed=format_embed('Bad argument given!', True))
            return
        raise error


# Checks if member has the admin role specified in the config. If no admin role is in the config, note that this ALWAYS returns true
def authorize_admin(guild, member):
    role_id = config_man.get_admin_role()  # Try grabbing the admin role from the config, check if it's None
    if role_id is not None:
        role = get(guild.roles, id=int(role_id))

        if role is not None:  # Now try checking if we can grab a role based on this id
            if role in member.roles:  # If the role exists, now see if the member we're checking has this role
                return True  # At this point the user is confirmed to be an admin! Return true!

        else:  # Couldn't turn the role id into the role
            print("\nWarning: Unable to grab the guild's admin role from the role id in the config!\nAdmin commands won't be authorized until you remove the 'admin_role' entry from the config\n")
            return False

    else:  # role_id is none - it probably isn't in the config?
        print("\nWarning: Admin command authorized for a potentially non-admin user - No admin role id is specified in the config!\nRun 'setAdminRole' to set this!\n")
        return True


# Returns a discord.Embed for use in sending status messages
def format_embed(text, is_error):
    return discord.Embed(title=text, colour=0xDB2323 if is_error else 0xFF7D00)


# Change the "playing" message every 6 hours (4 changes a day)
async def change_status():
    while True:
        await bot.change_presence(activity=discord.Game(playing_messages.get_status()))
        await asyncio.sleep(21600)  # 60 seconds * 60 minutes * 6 hours

# Now to actually run the bot:
secret = open("secret-token.txt", "r").read(59)  # Load our spooper secret token from file
if len(secret) == 59:  # Basic length check for invalid secrets (are secrets always 59 characters lnog???? I DUNNO BRUH!!!1!
    bot.run(secret)
else:
    print("Invalid secret? Place this bot's access token in secret-token.txt to run!")
