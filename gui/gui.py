#!/usr/bin/env python3

from tkinter import *
from PIL import ImageTk, Image
from os import path

class Gui:
    def __init__(self):
        root = Tk()
        app = Frame(root)
        root.wm_title("test")
        root.grid()

        image = ImageTk.PhotoImage(Image.open("10000.jpg"))
        widget = Label(root, image = image)
        widget.grid()

        root.mainloop()

class File:
    def __init__(self, path):
        self.path = path

class TextFile(File):
    def __iter__(self):
        self.cursor = 0

        return self

    def __next__(self):
        string = ""
        
        with open(self.path, "rb") as handle:
            handle.seek(self.cursor)

            while True:
                buf = handle.read(2)

                if len(buf) == 0:
                    raise StopIteration
                
                if buf[0] == 0:
                    if len(string) == 0:
                        continue
                
                    else:
                        self.cursor = handle.tell()
                        return string

                try:
                    string += buf[0].to_bytes(1, "big").decode("utf-8")

                except UnicodeDecodeError:
                    string += f"({hex(buf[0])})"

class PropertiesFile(File):
    def __iter__(self):
        self.cursor = 8
    
        return self

    def __next__(self):
        with open(self.path, "rb") as handle:
            handle.seek(self.cursor)
            buf = handle.read(8)
        
            if len(buf) != 0:
                self.cursor += 8
                return buf
            
            else:
                raise StopIteration

class Cards(list):
    def __init__(self):
        super().__init__(self)

class Card:
    def __init__(self, name, description, properties):
        self.name = name
        self.description = description
        self.properties_string = self.pad_binary_string(
                bin(int.from_bytes(properties, "big")).lstrip("0b"),
                64)

        self.id = self.decode_id()
        self.major_type = self.decode_major_type()

    def decode_id(self):
        return str(int(
                    self.properties_string[10 : 16] +
                    self.properties_string[0 : 8],
                    base = 2))

    def decode_major_type(self):
        major_type_code = int(self.properties_string[33 : 39], base = 2)

        if major_type_code == 0x00:
            return "Normal Monster"

        if major_type_code == 0x01:
            return "Effect Monster"
        
        if major_type_code == 0x02:
            return "Fusion Monster"
        
        if major_type_code == 0x03:
            return "Fusion Effect Monster"

        if major_type_code == 0x04:
            return "Ritual Monster"

        if major_type_code == 0x05:
            return "Ritual Effect Monster"

        if major_type_code == 0x06:
            return "Toon Monster"

        if major_type_code == 0x07:
            return "Spirit Monster"

        if major_type_code == 0x08:
            return "Union Effect Monster"

        if major_type_code == 0x09:
            return "Gemini Monster"

        if major_type_code == 0x0A:
            return "Token"

        if major_type_code == 0x0D:
            return "Spell Card"

        if major_type_code == 0x0E:
            return "Trap Card"
        
        if major_type_code == 0x0F:
            return "Tuner Monster"

        if major_type_code == 0x10:
            return "Tuner Effect Monster"
        
        if major_type_code == 0x11:
            return "Synchro Monster"
        
        if major_type_code == 0x12:
            return "Synchro Effect Monster"
        
        if major_type_code == 0x13:
            return "Synchro Tuner Monster"
        
        if major_type_code == 0x16:
            return "XYZ Monster"

        if major_type_code == 0x17:
            return "XYZ Effect Monster"

        if major_type_code == 0x18:
            return "Flip Effect Monster"

        if major_type_code == 0x19:
            return "Pendulum Monster"
        
        if major_type_code == 0x1A:
            return "Pendulum Effect Monster"

        if major_type_code == 0x1B:
            return "Effect Monster"

        if major_type_code == 0x1C:
            return "Toon Monster"

        if major_type_code == 0x1D:
            return "Spirit Monster"
        
        if major_type_code == 0x1E:
            return "Tuner Effect Monster"
        
        if major_type_code == 0x20:
            return "Flip Tuner Effect Monster"

        if major_type_code == 0x21:
            return "Pendulum Tuner Effect Monster"

        
        if major_type_code == 0x22:
            return "XYZ Pendulum Effect Monster"

        if major_type_code == 0x22:
            return "Pendulum Flip Effect Monster"

    def summarise(self):
        print(f"Name: {self.name}")
        print(f"Major Type: {self.major_type}")

    def pad_binary_string(self, string, size):
        if len(string) == size:
            return string

        return "0" * (size - len(string)) + string

class Renderer:
    def __init__(self):
        self.src_dir_path = "../decompile"
        self.dest_dir_path = "rendered"
        
        self.frame_ritual_path = "duel\\frame\\card_gisiki.png"
        self.frame_effect_path = "duel\\frame\\card_kouka.png"
        self.frame_spell_path = "duel\\frame\\card_mahou.png"
        self.frame_normal_path = "duel\\frame\\card_nomal.png"
        self.frame_pendulum_normal_path = "duel\\frame\\card_pendulum_n.png"
        self.frame_pendulum_effect_path = "duel\\frame\\card_pendulum.png"
        self.frame_pendulum_synchro_path = \
                                    "duel\\frame\\card_sync_pendulum.png"

        self.frame_synchro_path = "duel\\frame\\card_sync.png"
        self.frame_token_path = "duel\\frame\\card_token.png"
        self.frame_trap_path = "duel\\frame\\card_wana.png"
        self.frame_xyz_pendulum_path = "duel\\frame\\card_xyz_pendulum.png"
        self.frame_xyz_path = "duel\\frame\\card_xyz.png"
        self.frame_fusion_path = "duel\\frame\\card_yugo.png"

        self.art_dir_path = "cardcropHD400.jpg.zib"

    def render_card(self, card):
        """
        Load the frame
        """
        frame_path = path.join(
                            self.src_dir_path,
                            self.choose_frame_path(card.major_type))

        frame = Image.open(frame_path)

        """
        Create the canvas which we'll paste things into
        """
        canvas = Image.new("RGB", frame.size)

        """
        Load the card artwork
        """
        art_path = path.join(
                            self.src_dir_path, 
                            self.art_dir_path, 
                            card.id + ".jpg")

        art = Image.open(art_path)


        """
        Paste everything into the canvas
        """
        canvas.paste(art, (49, 107))
        canvas.paste(frame, (0, 0), frame)
        canvas.save(
                    path.join(self.dest_dir_path, card.name + ".png"),
                    "PNG")

    def choose_frame_path(self, major_type):
        if ("Pendulum" in major_type) and ("Effect" in major_type):
            return self.frame_pendulum_effect_path

        if ("Pendulum" in major_type) and ("Synchro" in major_type):
            return self.frame_pendulum_synchro_path

        if ("XYZ" in major_type) and ("Pendulum" in major_type):
            return self.frame_XYZ_pendulum_path

        if "Pendulum" in major_type:
            return self.frame_pendulum_normal_path

        if "XYZ" in major_type:
            return self.frame_xyz_path

        if "Ritual" in major_type:
            return self.frame_ritual_path
        
        if "Effect" in major_type:
            return self.frame_effect_path
        
        if "Spell" in major_type:
            return self.frame_spell_path
        
        if "Synchro" in major_type:
            return self.frame_synchro_path

        if "Token" in major_type:
            return self.frame_token_path

        if "Trap" in major_type:
            return self.frame_trap_path

        if "Fusion" in major_type:
            return self.frame_fusion_path

name_file = TextFile("../decompile/bin\\CARD_Name_E.bin")
description_file = TextFile("../decompile/bin\\CARD_Desc_E.bin")
properties_file = PropertiesFile("../decompile/bin\\CARD_Prop.bin")
renderer = Renderer()

for name, description, properties in zip(
                                        name_file, 
                                        description_file, 
                                        properties_file):

    card = Card(name, description, properties)
    renderer.render_card(card)
    break

