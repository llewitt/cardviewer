#!/usr/bin/env python3

import tkinter as tk
from tkinter.ttk import Treeview
from PIL import ImageTk, Image, ImageDraw, ImageFont
from os import path

class Application(tk.Frame):
    def __init__(self, root= None):
        super().__init__(root)
        self.cards = Cards()
        self.root = root
        self.pack()
        self.build_toolbar_menu()
        self.build_card_canvas()
        self.build_card_treeview()

    def build_toolbar_menu(self):
        self.toolbar_menu = tk.Menu(self)
        self.file_menu = tk.Menu(self.toolbar_menu)
        self.file_menu.add_command(label = "Open", command = self.open)
        self.file_menu.add_separator()
        self.file_menu.add_command(label = "Exit", command = self.quit)
        self.toolbar_menu.add_cascade(label = "File", menu = self.file_menu)
        self.root.config(menu = self.toolbar_menu)
        
        """
        self.card_image = ImageTk.PhotoImage(Image.open("reference.png"))
        self.card_image_label = tk.Label(self, image = self.card_image)
        self.card_image_label.grid(row = 1, column = 1)
        """

    def build_card_canvas(self):
        self.card_canvas = tk.Canvas(self)
        self.card_canvas.grid(row = 0, column = 0)
        
        self.card_name_label = tk.Label(self.card_canvas)
        self.card_name_label.grid(row = 0, column = 0)
        self.card_name_label.config(text = "Name")
        self.card_name_entry_var = tk.StringVar()
        self.card_name_entry = tk.Entry(self.card_canvas)
        self.card_name_entry.grid(row = 0, column = 1)
        self.card_name_entry.config(textvariable = self.card_name_entry_var)

        self.card_id_label = tk.Label(self.card_canvas)
        self.card_id_label.grid(row = 1, column = 0)
        self.card_id_label.config(text = "Id")
        self.card_id_entry_var = tk.StringVar()
        self.card_id_entry = tk.Entry(self.card_canvas)
        self.card_id_entry.grid(row = 1, column = 1)
        self.card_id_entry.config(textvariable = self.card_id_entry_var)

        self.card_attribute_label = tk.Label(self.card_canvas)
        self.card_attribute_label.grid(row = 2, column = 0)
        self.card_attribute_label.config(text = "Attribute")
        self.card_attribute_entry_var = tk.StringVar()
        self.card_attribute_entry = tk.Entry(self.card_canvas)
        self.card_attribute_entry.grid(row = 2, column = 1)
        self.card_attribute_entry.config(textvariable = self.card_attribute_entry_var)

        self.card_major_type_label = tk.Label(self.card_canvas)
        self.card_major_type_label.grid(row = 3, column = 0)
        self.card_major_type_label.config(text = "Major Type")
        self.card_major_type_entry_var = tk.StringVar()
        self.card_major_type_entry = tk.Entry(self.card_canvas)
        self.card_major_type_entry.grid(row = 3, column = 1)
        self.card_major_type_entry.config(textvariable = self.card_major_type_entry_var)

        self.card_minor_type_label = tk.Label(self.card_canvas)
        self.card_minor_type_label.grid(row = 4, column = 0)
        self.card_minor_type_label.config(text = "Minor Type")
        self.card_minor_type_entry_var = tk.StringVar()
        self.card_minor_type_entry = tk.Entry(self.card_canvas)
        self.card_minor_type_entry.grid(row = 4, column = 1)
        self.card_minor_type_entry.config(textvariable = self.card_minor_type_entry_var)

    def build_card_treeview(self):
        self.card_treeview = tk.ttk.Treeview(self, columns = ("Name", "Id"))
        self.card_treeview.grid(row = 0, column = 1)
        self.card_treeview.column("#0", minwidth = 0, width = 0, stretch = 0)
        self.card_treeview.bind("<Button-1>", self.card_treeview_onclick)

        for card in self.cards:
            self.card_treeview.insert("", "end", values = (card.name, card.id), iid = str(card.id))

    def card_treeview_onclick(self, event):
        row_itemid = self.card_treeview.identify_row(event.y)
        card = [card for card in self.cards if card.id == row_itemid][0]

        self.card_name_entry_var.set(card.name)
        self.card_id_entry_var.set(card.id)
        self.card_attribute_entry_var.set(card.attribute)
        self.card_major_type_entry_var.set(card.major_type)
        self.card_minor_type_entry_var.set(card.minor_type)

    def open(self):
        pass

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
                
                if (buf[0] == 0) and (buf[1] == 0):
                    if len(string) == 0:
                        continue
                
                    else:
                        self.cursor = handle.tell()
                        return string

                string += buf.decode("utf-16")

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
        self.renderer = Renderer()
        name_file = TextFile("../decompile/bin\\CARD_Name_E.bin")
        description_file = TextFile("../decompile/bin\\CARD_Desc_E.bin")
        properties_file = PropertiesFile("../decompile/bin\\CARD_Prop.bin")

        for name, description, properties in zip(
                                                name_file, 
                                                description_file, 
                                                properties_file):

            self.append(Card(name, description, properties))

class Card:
    def __init__(self, name, description, properties):
        self.name = name
        self.description = description
        self.properties_string = self.pad_binary_string(
                bin(int.from_bytes(properties, "big")).lstrip("0b"),
                64)

        self.id = self.decode_id()
        self.attribute = self.decode_attribute()
        self.major_type = self.decode_major_type()
        self.minor_type = self.decode_minor_type()

    def decode_id(self):
        return str(int(
                    self.properties_string[10 : 16] +
                    self.properties_string[0 : 8],
                    base = 2))

    def decode_attribute(self):
        type_code = int(
                            self.properties_string[32 : 33] +
                            self.properties_string[45 : 48],
                            base = 2)
        
        if type_code == 0x00:
            return "None"

        if type_code == 0x01:
            return "Dark"
        
        if type_code == 0x02:
            return "Fire"
        
        if type_code == 0x03:
            return "Wind"
        
        if type_code == 0x04:
            return "Spell"
        
        if type_code == 0x08:
            return "Light"
        
        if type_code == 0x09:
            return "Water"
        
        if type_code == 0x0A:
            return "Earth"
        
        if type_code == 0x0B:
            return "Divine"

        if type_code == 0x0C:
            return "Trap"

    def decode_major_type(self):
        type_code = int(self.properties_string[33 : 39], base = 2)

        if type_code == 0x00:
            return "Normal Monster"

        if type_code == 0x01:
            return "Effect Monster"
        
        if type_code == 0x02:
            return "Fusion Monster"
        
        if type_code == 0x03:
            return "Fusion Effect Monster"

        if type_code == 0x04:
            return "Ritual Monster"

        if type_code == 0x05:
            return "Ritual Effect Monster"

        if type_code == 0x06:
            return "Toon Monster"

        if type_code == 0x07:
            return "Spirit Monster"

        if type_code == 0x08:
            return "Union Effect Monster"

        if type_code == 0x09:
            return "Gemini Monster"

        if type_code == 0x0A:
            return "Token"

        if type_code == 0x0D:
            return "Spell Card"

        if type_code == 0x0E:
            return "Trap Card"
        
        if type_code == 0x0F:
            return "Tuner Monster"

        if type_code == 0x10:
            return "Tuner Effect Monster"
        
        if type_code == 0x11:
            return "Synchro Monster"
        
        if type_code == 0x12:
            return "Synchro Effect Monster"
        
        if type_code == 0x13:
            return "Synchro Tuner Monster"
        
        if type_code == 0x16:
            return "XYZ Monster"

        if type_code == 0x17:
            return "XYZ Effect Monster"

        if type_code == 0x18:
            return "Flip Effect Monster"

        if type_code == 0x19:
            return "Pendulum Monster"
        
        if type_code == 0x1A:
            return "Pendulum Effect Monster"

        if type_code == 0x1B:
            return "Effect Monster"

        if type_code == 0x1C:
            return "Toon Monster"

        if type_code == 0x1D:
            return "Spirit Monster"
        
        if type_code == 0x1E:
            return "Tuner Effect Monster"
        
        if type_code == 0x20:
            return "Flip Tuner Effect Monster"

        if type_code == 0x21:
            return "Pendulum Tuner Effect Monster"

        
        if type_code == 0x22:
            return "XYZ Pendulum Effect Monster"

        if type_code == 0x22:
            return "Pendulum Flip Effect Monster"

    def decode_minor_type(self):
        type_code = int(self.properties_string[49 : 54], base = 2)

        if type_code == 0x00:
            return "Token"
        
        if type_code == 0x01:
            return "Dragon"
        
        if type_code == 0x02:
            return "Zombie"

        if type_code == 0x03:
            return "Fiend"
        
        if type_code == 0x04:
            return "Pyro"

        if type_code == 0x05:
            return "Sea Serpent"

        if type_code == 0x06:
            return "Rock"

        if type_code == 0x07:
            return "Machine"

        if type_code == 0x08:
            return "Fish"

        if type_code == 0x09:
            return "Dinosaur"

        if type_code == 0x0A:
            return "Insect"

        if type_code == 0x0B:
            return "Beast"

        if type_code == 0x0C:
            return "Beast-Warrior"

        if type_code == 0x0D:
            return "Plant"

        if type_code == 0x0E:
            return "Aqua"

        if type_code == 0x0F:
            return "Warrior"

        if type_code == 0x10:
            return "Winged Beast"

        if type_code == 0x11:
            return "Fairy"

        if type_code == 0x12:
            return "Spellcaster"

        if type_code == 0x13:
            return "Thunder"

        if type_code == 0x14:
            return "Reptile"

        if type_code == 0x15:
            return "Psychic"

        if type_code == 0x16:
            return "Wrym"

        if type_code == 0x17:
            return "Divine-Beast"

        if type_code == 0x19:
            return "Spell"

        if type_code == 0x1A:
            return "Trap"

    def summarise(self):
        print(f"Name:\t\t{self.name}")
        print(f"Attribute:\t{self.attribute}")
        print(f"Major Type:\t{self.major_type}")

    def pad_binary_string(self, string, size):
        if len(string) == size:
            return string

        return "0" * (size - len(string)) + string

class Renderer:
    def __init__(self):
        self.src_dir_path = "../decompile"
        self.dest_dir_path = "rendered"

        self.card_width = 400
        self.card_height = 580
        self.card_size = (self.card_width, self.card_height)
        
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

        self.extras_path = "pdui\\STEAM_icons.png"
        self.attribute_icon_dark_coordinates = (1299, 1, 1340, 42)
        self.attribute_icon_fire_coordinates = (1341, 1, 1382, 42)
        self.attribute_icon_light_coordinates = (1383, 1, 1424, 42)
        self.attribute_icon_trap_coordinates = (1425, 1, 1466, 42)
        self.attribute_icon_wind_coordinates = (1467, 1, 1508, 42)
        self.attribute_icon_earth_coordinates = (1299, 43, 1340, 84)
        self.attribute_icon_divine_coordinates = (13443, 43, 1382, 84)
        self.attribute_icon_spell_coordinates = (1383, 43, 1424, 84)
        self.attribute_icon_water_coordinates = (1425, 43, 1466, 84)
        self.attribute_icon_coordinate = (329, 27, 370, 68)

        self.art_dir_path = "cardcropHD400.jpg.zib"

        self.name_font_path = "font\\MatrixRegularSmallCaps.otf"
        self.name_font_size = 36

        self.text_fill = (0, 0, 0)

    def render_card(self, card):
        canvas = Image.new("RGB", self.card_size)
        frame = Image.open(path.join(
                            self.src_dir_path,
                            self.choose_frame_path(card.major_type)))

        attribute_icon = self.load_attribute_icon(card)
        art_path = path.join(
                            self.src_dir_path, 
                            self.art_dir_path, 
                            card.id + ".jpg")

        art = Image.open(art_path)
        canvas.paste(art, (49, 107))
        canvas.paste(frame, (0, 0), frame)
        
        if attribute_icon != None:
            canvas.paste(
                    attribute_icon, 
                    self.attribute_icon_coordinate, 
                    attribute_icon)

        name_font = ImageFont.truetype(
                    path.join(self.src_dir_path, self.name_font_path),
                    size = self.name_font_size)

        draw = ImageDraw.Draw(canvas)
        draw.text(
                (36, 57), 
                card.name, 
                font = name_font, 
                fill = (0, 255, 0),
                anchor = "ls")

        draw.rectangle(
                draw.textbbox(
                    (36, 57), 
                    card.name, 
                    font = name_font,
                    anchor = "ls"),
                outline = (255, 0, 0))

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

    def load_attribute_icon(self, card):
        extras_path = path.join(self.src_dir_path, self.extras_path)

        if "None" in card.attribute:
            return None

        if "Dark" in card.attribute:
            with Image.open(extras_path) as image:
                return image.crop(self.attribute_icon_dark_coordinates)
        
        if "Fire" in card.attribute:
            with Image.open(extras_path) as image:
                return image.crop(self.attribute_icon_fire_coordinates)
        
        if "Wind" in card.attribute:
            with Image.open(extras_path) as image:
                return image.crop(self.attribute_icon_wind_coordinates)
        
        if "Spell" in card.attribute:
            with Image.open(extras_path) as image:
                return image.crop(self.attribute_icon_spell_coordinates)
        
        if "Light" in card.attribute:
            with Image.open(extras_path) as image:
                return image.crop(self.attribute_icon_light_coordinates)
        
        if "Water" in card.attribute:
            with Image.open(extras_path) as image:
                return image.crop(self.attribute_icon_water_coordinates)
        
        if "Earth" in card.attribute:
            with Image.open(extras_path) as image:
                return image.crop(self.attribute_icon_earth_coordinates)
        
        if "Divine" in card.attribute:
            with Image.open(extras_path) as image:
                return image.crop(self.attribute_icon_divine_coordinates)

        if "Trap" in card.attribute:
            with Image.open(extras_path) as image:
                return image.crop(self.attribute_icon_trap_coordinates)

def main():
    root = tk.Tk()
    application = Application(root = root)
    application.mainloop()
    
if __name__ == "__main__":
    exit(main())

