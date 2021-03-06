#!/usr/bin/python

# --
# scoreboard_config_man.py - its like config-man but for events
# --


import os
import sys
from pyexpat import ExpatError
from xml.dom import minidom
from xml.dom.minidom import parse
import xml.dom.minidom
import codecs


# The scoreboard config is organized like this - each individual event has it's own config file so you can save old scoreboards for posterity.
# (Note: The event name is inferred from the config file's name)
# <scoreboard>
#   <display_name>name</display_name>
#   <description>event description</description> (Probably gonna get deprecated)
#   <activeplayers><player id="id" division="div" /></activeplayers>
#   <divisions>
#      <division name="", desc="", emote="">
#           <scoreboard_message channel="" message=""/>
#          <field name="Field name" type="Field type" emote="">
#              <entry verified_value=score, unverified_value=score2>Player id</role>
#              <entry>...
#          </field>
#           <field...>
#      </division>
#       <division...>
#   </divisions>
# </scoreboard>

class ScoreboardConfig:
    def __init__(self):
        print("Initializing scoreboard_config_man...")
        self.sc_dom = None
        self.sc_config = None
        self.sc_divisions = None
        self.sc_name = None

        # Create our scoreboard config directory if it doesn't exist
        if not os.path.exists("scoreboards"):
            try:
                os.mkdir("scoreboards")
            except Exception as e:
                print("Error creating scoreboard config directory: " + str(e))
                sys.exit(1)

    # Checks if a scoreboard config file exists
    def sc_config_exists(self, name):
        return os.path.exists("scoreboards/" + name + ".xml")



    # Attempts to load a scoreboard config with the given name, optionally creating a new one if it doesn't exist
    def load_sc_config(self, name, allow_create, desc=""):
        print("Attempting load of scoreboard config \"scoreboards/" + name + ".xml\"...")
        try:
            self.sc_dom = xml.dom.minidom.parse("scoreboards/" + name + ".xml")
            self.sc_config = self.sc_dom.documentElement
            self.sc_name = name

            divisions_elems = self.sc_config.getElementsByTagName("divisions")  # Grab the divisions element, or make a new one
            if len(divisions_elems) == 0:
                divisions = self.sc_dom.createElement("divisions")
                self.sc_config.appendChild(divisions)
            else:
                divisions = divisions_elems[0]

            self.sc_divisions = divisions  # Store the divisions element for quick reference

            print("Loaded!")
            return 0

        except FileNotFoundError:  # No config file? Make one boi
            if allow_create:
                print("Scoreboard config not found, but creation of a new config is enabled. Attempting creation...")
                self.sc_dom = minidom.Document()
                root = self.sc_dom.createElement("scoreboard")
                self.sc_dom.appendChild(root)
                self.sc_config = self.sc_dom.documentElement
                self.sc_name = name
                self.set_desc(desc)
                self.sc_divisions = self.sc_dom.createElement("divisions")
                self.sc_config.appendChild(self.sc_divisions)
                return 1

            else:
                print("Error: Scoreboard config file not found!")
                self.unload_sc_config()
                return -1



    # Unloads the current scoreboard config (so no config is currently loaded)
    # Note: DOES NOT SAVE THE CONFIG BEFORE UNLOADING!
    def unload_sc_config(self):
        if self.sc_config is not None:
            print("Unloading scoreboard config " + self.sc_name)
            self.sc_dom = None
            self.sc_config = None
            self.sc_name = None
        else:
            print("Tried to unload a config when no config was loaded!")



    def is_scoreboard_loaded(self):
        return self.sc_config is not None and self.sc_name is not None  # At a minimum our config object shouldn't be broken (our config name should match up with this too)



    # Saves the currently loaded scoreboard config to file
    def save_sc_config(self):
        if self.sc_config is not None:
            print("Saving scoreboard config \"scoreboards/" + self.sc_name + ".xml\"...")
            file = codecs.open("scoreboards/" + self.sc_name + ".xml", "w", "utf_8_sig")
            file.write(self.sc_config.toxml(encoding="utf-8").decode("utf-8"))
            #config.writexml(file, addindent="\t", newl="\n", encoding="utf-8")
            file.close()




    # Gets the scoreboard's display name, or it's filename if the display name isn't set
    def get_disp_name(self):
        if self.sc_config is not None:
            elements = self.sc_config.getElementsByTagName("display_name")
            if len(elements) >= 1 and elements[0].firstChild.nodeValue is not None:
                return elements[0].firstChild.nodeValue
            else:
                return self.sc_name
        return None



    # Sets the scoreboard's display name
    def set_disp_name(self, name):
        if self.sc_config is not None:
            disp_name_elems = self.sc_config.getElementsByTagName("display_name")  # Try to get the display_name element - if it doesn't exist, make one
            disp_name = None
            if len(disp_name_elems) == 0:
                disp_name = self.sc_dom.createElement("display_name")
                self.sc_config.appendChild(disp_name)
            else:
                disp_name = disp_name_elems[0]

            if disp_name.hasChildNodes():
                for child in disp_name.childNodes:
                    disp_name.removeChild(child)
            disp_name.appendChild(self.sc_dom.createTextNode(name))

            print("Set scoreboard display name to \"" + name + "\"")
            self.save_sc_config()



    # Gets the scoreboard's description
    def get_desc(self):
        if self.sc_config is not None:
            elements = self.sc_config.getElementsByTagName("description")
            if len(elements) >= 1 and elements[0].firstChild is not None:
                    return elements[0].firstChild.nodeValue
        return ""



    # Sets the scoreboard's description
    def set_desc(self, description):
        if self.sc_config is not None:
            desc_elems = self.sc_config.getElementsByTagName("description")  # Try to get the desc element - if it doesn't exist, make one
            desc = None
            if len(desc_elems) == 0:
                desc = self.sc_dom.createElement("description")
                self.sc_config.appendChild(desc)
            else:
                desc = desc_elems[0]

            if desc.hasChildNodes():
                for child in desc.childNodes:
                    desc.removeChild(child)
            desc.appendChild(self.sc_dom.createTextNode(description))

            print("Set scoreboard description to \"" + description + "\"")
            self.save_sc_config()


    # Returns a division element with name <name> if it exists, or None if it doesn't
    def get_division(self, name):
        if self.sc_config is not None:
            div_elems = self.sc_divisions.getElementsByTagName("division")
            for div_elem in div_elems:
                if div_elem.hasAttribute("name") and div_elem.getAttribute("name") == name:
                    return div_elem
        return None

    # Returns a list of divisions and their respective emojis
    def get_divisions(self):
        if self.sc_config is not None:
            div_elems = self.sc_divisions.getElementsByTagName("division")
            ret = {}
            for div_elem in div_elems:
                if div_elem.hasAttribute("name") and div_elem.hasAttribute("emote"):
                    ret[div_elem.getAttribute("emote")] = div_elem
                    #print(div_elem.getAttribute("emote") + "," + div_elem.getAttribute("name"))
            return ret
        return None


    # Returns a list of division names and descriptions
    def get_division_names(self):
        if self.sc_config is not None:
            div_elems = self.get_divisions()
            ret = {}
            for div_elem in div_elems.values():
                if div_elem.hasAttribute("description"):
                    ret[div_elem.getAttribute("name")] = div_elem.getAttribute("description")
                else:
                    ret[div_elem.getAttribute("name")] = "*No description available*"
            return ret
        return None


    # Returns a list of division emojis and names
    def get_division_emotes(self):
        if self.sc_config is not None:
            div_elems = self.get_divisions()
            ret = {}
            for div_elem in div_elems.values():
                if div_elem.hasAttribute("name") and div_elem.hasAttribute("emote"):
                    ret[div_elem.getAttribute("emote")] = div_elem.getAttribute("name")
            return ret

        return None


    # Creates a new scoreboard division
    def div_new(self, name, desc, emote):
        if self.sc_config is not None:  # Make sure we have a config loaded
            if self.get_division(name) is not None:  # Does a division with this name already exist?
                print("Error creating division \"" + name + "\" - a division with this name already exists!")
                return False

            divs_elems = self.sc_config.getElementsByTagName("divisions")  # Otherwise, go grab our divisions element
            if len(divs_elems) > 0:
                div = self.sc_dom.createElement("division")  # ...and add a new division element to it
                div.setAttribute("name", name)
                div.setAttribute("desc", desc)
                div.setAttribute("emote", emote)
                divs_elems[0].appendChild(div)
                print("Created scoreboard division \"" + name + "\".")
                self.save_sc_config()
                return True
            else:
                print("Unable to get divisions element to add a division")
                return None


    # Removes a scoreboard division
    def div_remove(self, name):
        if self.sc_config is not None:
            div = self.get_division(name)
            if div is not None:  # Does the division we want to remove exist?
                divs_elems = self.sc_config.getElementsByTagName("divisions")  # Grab our divisions element
                if len(divs_elems) > 0:
                    divs_elems[0].removeChild(div)  # And remove the division
                    print("Deleted scoreboard division \"" + name + "\"")
                    self.save_sc_config()
                    return True
                else:
                    print("Unable to get divisions element to remove a division")
                    return None

            else:  # Can't delete a division that doesn't exist
                print("Error deleting division \"" + name + "\" - division doesn't exist!")
                return False


    # Sets a division's description
    def div_desc(self, name, description):
        if self.sc_config is not None:
            div = self.get_division(name)
            if div is not None:  # Does the division we want to edit exist?
                div.setAttribute("description", description)
                self.save_sc_config()
                return True

            else:  # Can't delete a division that doesn't exist
                print("Error finding division \"" + name + "\" - division doesn't exist!")
                return False


    # Given a player's user id', gets a division
    def get_player_division(self, id):
        if self.sc_config is not None:
            id = str(id)
            aplr_elems = self.sc_config.getElementsByTagName("activeplayers")
            if aplr_elems is not None and len(aplr_elems) > 0:
                plr_elems = aplr_elems[0].getElementsByTagName("player")
                for plr_elem in plr_elems:
                    if plr_elem.hasAttribute("id") and plr_elem.getAttribute("id") == id and plr_elem.hasAttribute("division"):
                        return plr_elem.getAttribute("division")
        return None


    # Sets a player's division, given a player and a division
    def set_player_division(self, id, division):
        if self.sc_config is not None:
            id = str(id)
            plr_elems = self.sc_config.getElementsByTagName("player")
            for plr_elem in plr_elems:
                if plr_elem.hasAttribute("id") and plr_elem.getAttribute("id") == id:
                    plr_elem.setAttribute("division", division)
                    self.save_sc_config()
                    return True

            # Couldn't find an existing player entry, make a new one
            plr_elem = self.sc_dom.createElement("player")
            plr_elem.setAttribute("id", id)
            plr_elem.setAttribute("division", division)
            aplr_elems = self.sc_config.getElementsByTagName("activeplayers")
            if aplr_elems is not None and len(aplr_elems) > 0:
                aplr_elems[0].appendChild(plr_elem)
                self.save_sc_config()
                return True
            else:
                aplr_elem = self.sc_dom.createElement("activeplayers")
                self.sc_config.appendChild(aplr_elem)
                aplr_elem.appendChild(plr_elem)
                self.save_sc_config()
                return True

        return False


    # Gets the channel/message ID of the scoreboard message
    def get_scoreboard_msg(self):
        if self.sc_config is not None:
            msgs = self.sc_config.getElementsByTagName("scoreboard_message")
            if len(msgs) >= 1:
                msg = msgs[0]
                if msg.hasAttribute("channel") and msg.hasAttribute("message"):
                    return [int(msg.getAttribute("channel")), int(msg.getAttribute("message"))]
        return None


    # Sets the channel/message ID the scoreboard message is in
    def set_scoreboard_msg(self, channel, message):
        if self.sc_config is not None:
            msgs = self.sc_config.getElementsByTagName("scoreboard_message")
            msg = None
            if len(msgs) == 0:
                msg = self.sc_dom.createElement("scoreboard_message")
                self.sc_config.appendChild(msg)
            else:
                msg = msgs[0]

            msg.setAttribute("channel", str(channel))
            msg.setAttribute("message", str(message))
            print("Scoreboard message set to ID " + str(message))
            self.save_sc_config()


    # Gets a list of fields for the current scoreboard as an array of {field name,value}
    def get_fields(self, div):
        if self.sc_config is not None:
            fields = div.getElementsByTagName("field")
            ret = {}
            for field in fields:
                if field.hasAttribute("name") and field.hasAttribute("type"):
                    field_type = self.parse_field_type(field.getAttribute("type"))
                    if field_type is not None:
                        ret[field.getAttribute("name")] = field_type
            return ret

        return None


    # Gets a list of fields for the current scoreboard as an array of {emoji, field name}
    def get_fields_emoji(self, div):
        if self.sc_config is not None:
            # print(div.toprettyxml())
            fields = div.getElementsByTagName("field")
            ret = {}
            for field in fields:
                if field.hasAttribute("name") and field.hasAttribute("emote"):
                    ret[field.getAttribute("emote")] = field.getAttribute("name")
            return ret

        return None


    # Adds or edits a field in the config
    def update_field(self, div, name, type, emoji):
        if self.sc_config is not None:
            field_elems = div.getElementsByTagName("field")
            field = None
            for prelim_field in field_elems:
                if prelim_field.hasAttribute("name") and prelim_field.getAttribute("name") == name:
                    print("Update field")
                    field = prelim_field
                    break

            if field is None:  # Didn't find a field above, make a new one
                print("New field")
                field = self.sc_dom.createElement("field")
                div.appendChild(field)

            field.setAttribute("name", name)
            field.setAttribute("type", type)
            field.setAttribute("emote", emoji)

            self.save_sc_config()
            print("Updated field " + name + " (type: " + type + ", emote: " + emoji + ")")
            return True
        return None


    # Deletes a field in the config
    def remove_field(self, div, name):
        if self.sc_config is not None:
            field_elems = div.getElementsByTagName("field")
            for prelim_field in field_elems:
                if prelim_field.hasAttribute("name") and prelim_field.getAttribute("name") == name:
                    div.removeChild(prelim_field)
                    self.save_sc_config()
                    return True
            return False
        return None


    # Gets a field type, given a string
    def parse_field_type(self, field_type):
        try:
            field_type = int(field_type)
        except ValueError:
            return None

        if field_type >= 0 and field_type < 1:  # Todo: We only support one field type rn
            return field_type
        return None


    # Adds or updates a score entry
    def update_entry(self, div, field, user, score, verify):
        if self.sc_config is not None:
            field_elems = div.getElementsByTagName("field")  # Find the field to add to
            for field_elem in field_elems:
                if field_elem.hasAttribute("name") and field_elem.getAttribute("name") == field:

                    entry_elems = field_elem.getElementsByTagName("entry") # Now find the score entry to add to
                    entry = None
                    for entry_elem in entry_elems:
                        if entry_elem.firstChild.nodeValue == str(user):  # Found an existing score entry!
                            entry = entry_elem
                            break

                    if entry is None:  # Didn't find an existing entry for this user, create one
                        entry = self.sc_dom.createElement("entry")
                        entry.appendChild(self.sc_dom.createTextNode(str(user)))
                        field_elem.appendChild(entry)

                    # Finally: Set the entry's value
                    if verify:  # If we're verifying an entry, the unverified value is removed
                        entry.setAttribute("verified_value", str(score))
                        entry.setAttribute("unverified_value", "-1")

                    else:  # Unverified entries will only set the unverified value, keeping the verified one as a backup
                        entry.setAttribute("unverified_value", str(score))

                    print("Updated entry: " + field + ", " + str(user) + ", " + str(score), " (verified: " + str(verify) + ")")
                    self.save_sc_config()
                    return True

        return False


    # Gets a score entry
    def get_entry(self, div, field, user):
        if self.sc_config is not None:
            field_elems = div.getElementsByTagName("field")  # Find the field to read from
            for field_elem in field_elems:
                if field_elem.hasAttribute("name") and field_elem.getAttribute("name") == field:

                    entry_elems = field_elem.getElementsByTagName("entry")  # Now find the score entry to read from
                    for entry_elem in entry_elems:
                        if entry_elem.firstChild.nodeValue == str(user) and entry_elem.hasAttribute("unverified_value"):  # Found an existing score entry!
                            verified_val = entry_elem.getAttribute("verified_value") if entry_elem.hasAttribute("verified_value") else -1
                            try:
                                return [int(entry_elem.getAttribute("unverified_value")), int(verified_val)]
                            except ValueError:
                                print("Error getting entry " + field + ", " + user + ": Value is not an int!")
                                return False
        return False


    # Gets the entries for a field, returned as {username, (score, verified)}
    def get_entries(self, div, field, guild):
        if self.sc_config is not None:
            field_elems = div.getElementsByTagName("field")  # Find the field to read from
            for field_elem in field_elems:
                if field_elem.hasAttribute("name") and field_elem.getAttribute("name") == field:
                    entries = {}
                    entry_elems = field_elem.getElementsByTagName("entry")  # Now find the score entry to read from

                    for entry_elem in entry_elems:
                        user = guild.get_member(int(entry_elem.firstChild.nodeValue))  # Make sure we can find the member this entry is from!
                        if user is not None:
                            values = [-1, -1]  # Now get this entry's values
                            if entry_elem.hasAttribute("unverified_value"):
                                values[0] = int(entry_elem.getAttribute("unverified_value"))
                            if entry_elem.hasAttribute("verified_value"):
                                values[1] = int(entry_elem.getAttribute("verified_value"))

                            if values[0] != -1 or values[1] != -1:  # Found at least one valid value set
                                if values[0] > values[1]:  # If a user's unverified value is higher than their verified, that's what we should return
                                    ret_value = [values[0], False]
                                else:  # Else, return their verified value
                                    ret_value = [values[1], True]
                                entries[user.display_name] = ret_value

                    return entries
        return None


    # Adds or updates a score entry
    def remove_entry(self, div, field, user):
        if self.sc_config is not None:
            field_elems = div.getElementsByTagName("field")  # Find the field to remove from
            for field_elem in field_elems:
                if field_elem.hasAttribute("name") and field_elem.getAttribute("name") == field:

                    entry_elems = field_elem.getElementsByTagName("entry")  # Now find the score entry to remove
                    for entry_elem in entry_elems:
                        if entry_elem.firstChild.nodeValue == str(user):  # Found the field!
                            field_elem.removeChild(entry_elem)
                            print("Removed " + str(user) + "'s entry from " + field)
                            self.save_sc_config()
                            return True
        return False
