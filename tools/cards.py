#!/usr/bin/env python3

from os import listdir
from sys import exit
from pdb import set_trace
import json

def pad_binary(buf, size):
    if len(buf) == size:
        return buf

    return "0" * (size - len(buf)) + buf

def space_binary(buf, offset, space = " "):
    return buf[: offset] + space + buf[offset :]

def round_up(number, base):
    remainder = number % base

    if remainder != 0:
        number += base - remainder

    return number

class Names:
    def __init__(self):
        self.list = []

        path = "../decompile/bin\\CARD_Name_E.bin"
        name = ""

        with open(path, "rb") as handle:
            """
            Skip "header"
            """
            handle.read(8)
    
            counter = 0
            while True:
                buf = handle.read(2)
                
                if len(buf) == 0:
                    break

                if buf[0] == 0:
                    if len(name) != 0:
                        self.list.append(name)
                        counter += 1
                    
                    name = ""
                    continue

                try:
                    name += buf[0].to_bytes(1, "big").decode("utf-8")

                except UnicodeDecodeError:
                    name += f"({hex(buf[0])})"

class ImagePaths:
    def __init__(self):
        dir_path_1 = "../decompile/cardcropHD400.jpg.zib"
        dir_path_2 = "../decompile/cardcropHD401.jpg.zib"

        self.list = list(
                        set(listdir(dir_path_1)).union(
                                                set(listdir(dir_path_2))))

        self.list = sorted(
                    self.list,
                    key = lambda path: int(path.split(".")[0]))

class Properties:
    def __init__(self):
        self.list = []

        path = "../decompile/bin\\CARD_Prop.bin"
        properties = ""

        with open(path, "rb") as handle:
            """
            Skip "header"
            """
            handle.read(8)
    
            counter = 0
            while True:
                buf = handle.read(8)
                
                if len(buf) == 0:
                    break

                self.list.append(buf)

class Card:
    def __init__(self, name, path, properties, cardlist, search = True):
        self.name = name
        self.path = path
        self.properties = properties
        self.info = None
        self.major_type = "None"
        self.minor_type = "None"
        self.attribute = "None"
        self.attack = "None"
        self.defence = "None"

        if search:
            for card in cardlist:
                if card["name"] == self.name:
                    self.info = card

                    """
                    Try to treat all cards like monsters
                    """
                    try:
                        self.major_type = card["type"]
                        self.minor_type = card["race"]
                        self.attribute = card["attribute"]
                        self.attack = str(card["atk"])
                        self.defence = str(card["def"])

                    except KeyError:
                        break

                    break

    def render(self):
        properties = pad_binary(bin(int.from_bytes(self.properties, "big")).lstrip("0b"), 64)

        """
        First we get the card id
        """
        ID = int(properties[10 : 16] + properties[0 : 8], base = 2)

        """
        Next the attack rounding and the attack value
        """
        attack_rounding = int(properties[9 : 10])

        if attack_rounding:
            attack = round_up_string(properties[17 : 24], 50)

        else:
            attack = round_up_string(properties[17 : 24], 100)

        """
        The same for defence
        """
        defence_rounding = int(properties[16 : 17])

        if defence_rounding:
            defence = int(50 * (int(properties[24 : 31], base = 2) // 50))

        else:
            defence = int(100 * (int(properties[24 : 31], base = 2) // 100))

        """
        Get the level
        """
        level = int(properties[41 : 45], base = 2)

        print(ID, attack, defence, level, )

class Cards:
    def __init__(self, names, image_paths, properties, search = True):
        self.list = []
        self.count = len(names.list)

        with open("cardinfo.json", "r") as handle:
            self.cardlist = json.load(handle)["data"]

        for counter in range(self.count):
            self.list.append(Card(
                                names.list[counter],
                                image_paths.list[counter],
                                properties.list[counter],
                                self.cardlist,
                                search = search))

        self.list = sorted(self.list, key = lambda label: int.from_bytes(label.properties[6 : 7], "big") & 0x7f)

    def print(self):
        property_splits = PropertySplits()
        property_splits.add_property_split(0, 8, "ID [0-8]")
        property_splits.add_property_split(8, 9, "Unknown")
        property_splits.add_property_split(9, 10, "Attack Round")
        property_splits.add_property_split(10, 16, "ID [8-12]")
        property_splits.add_property_split(16, 17, "Defence Round")
        property_splits.add_property_split(17, 24, "Attack")
        property_splits.add_property_split(24, 31, "Defence")
        property_splits.add_property_split(31, 33, "Unknown")
        property_splits.add_property_split(33, 39, "Major Type")
        
        """
        property_splits.add_property_split(31, 34, "Unknown")
        property_splits.add_property_split(34, 37, "Major Type")
        property_splits.add_property_split(37, 38, "Summoning")
        property_splits.add_property_split(38, 39, "Effect")
        """

        property_splits.add_property_split(39, 40, "None")
        property_splits.add_property_split(40, 41, "'E/Q-P/C'")
        property_splits.add_property_split(41, 45, "Level")
        property_splits.add_property_split(45, 48, "Attribute Partial")
        property_splits.add_property_split(48, 49, "Unknown")
        property_splits.add_property_split(49, 54, "'Minor Type'")
        property_splits.add_property_split(54, 56, "F/C/R")
        property_splits.add_property_split(56, 64, "Pendulum Scale")

        csvdata = CsvData(
                        "Name",
                        "Path",
                        "Attribute",
                        "Attack",
                        "Defence",
                        "'Major Type'",
                        "'Minor Type'",
                        property_splits)

        card = self.list[0]

        for card in self.list:
            try:
                csvdata.add_line(
                                card.name,
                                card.path,
                                card.attribute,
                                card.attack,
                                card.defence,
                                card.major_type,
                                card.minor_type,
                                card.properties)

            except TypeError:
                continue

            except AttributeError:
                continue

        csvdata.print()

class PropertySplit:
    def __init__(self, lower, upper, name):
        self.lower = lower
        self.upper = upper
        self.name = name

class PropertySplits:
    def __init__(self):
        self.list = []

    def add_property_split(self, lower, upper, name):
        self.list.append(PropertySplit(lower, upper, name))

class CsvLine:
    def __init__(self, headings, *args):
        self.list = []

        for heading, arg in zip(headings, args):
            if type(heading) == str:
                self.list.append(arg)

            elif type(heading) == PropertySplits:
                properties = pad_binary(bin(int.from_bytes(arg, "big")).lstrip("0b"), 64)

                for property_split in heading.list:
                    self.list.append(
                                properties[
                                    property_split.lower : 
                                    property_split.upper])

            else:
                raise TypeError

    def print(self):
        string = ""
        
        for item in self.list:
            pass

            string += item + "~"

        print(string)

class CsvData:
    def __init__(self, *args):
        self.headings = []
        self.lines = []
        self.headings_string = ""
        
        for arg in args:
            self.headings.append(arg)

            if type(arg) == str:
                self.headings_string += arg + "~"

            elif type(arg) == PropertySplits:
                for property_split in arg.list:
                    self.headings_string += property_split.name + "~"

            else:
                raise TypeError

    def add_line(self, *args):
        self.lines.append(CsvLine(self.headings, *args))

    def print(self):
        print(self.headings_string)
        
        for line in self.lines:
            line.print() 

def main():
    names = Names()
    image_paths = ImagePaths()
    properties = Properties()
    cards = Cards(names, image_paths, properties, search = True)

    cards.print()

if __name__ == "__main__":
    exit(main())

