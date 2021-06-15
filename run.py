#!/usr/bin/env python3

from sys import exit
from os import mkdir
from os.path import basename, getsize, join
from pdb import set_trace

def pad_string(string, length):
    return ((length - len(string)) * " ") + string

class File:
    def __init__(self, path, read = True):
        self.path = path
        self.name = basename(path)
        self.read = read
        self.decompile_directory = "decompile"

        if self.read:
            self.size = getsize(self.path)
        else:
            self.size = 0
            
            with open(self.path, "wb"):
                pass

class Toc(File):
    def __init__(self, path, read = True):
        super().__init__(path, read)
        self.entries = []

        with open(self.path, "r") as handle:
            for line in handle.readlines()[1:]:
                self.entries.append(TocEntry(line))
        
class TocEntry:
    def __init__(self, line):
        size, name_size, self.name = line.split()
        self.size = int(size, base = 16)
        self.name_size = int(name_size, base = 16)

class Zib:
    def __init__(self, buf, name):
        self.name = name
        self.entries = []

        if ".jpg" in self.name:
            field_size = 8
            address_zero_correction = 0
        else:
            field_size = 4
            address_zero_correction = -1

        entry_size = 64
        entry_cnt = (int.from_bytes(buf[0:field_size], "big") - 16 + address_zero_correction) // entry_size

        tmp = ""
        for cnt, byte in enumerate(buf[0:field_size]):
            tmp += hex(byte)

            if cnt != field_size - 1:
                tmp += " "

        for cnt in range(entry_cnt):
            entry = buf[cnt * entry_size:((cnt + 1) * entry_size) - 1]

            """
            Numbers inside zib files are stored in big endian. Presumably
            the developer used a tool written in a language where that was
            standard, maybe java
            """
            address = int.from_bytes(entry[0:field_size], "big")

            if cnt == 0:
                address += address_zero_correction
            size = int.from_bytes(entry[field_size:2 * field_size], "big")

            name = ""
            for byte in entry[2 * field_size:64]:
                if byte == 0:
                    break

                try:
                    name += str(byte.to_bytes(1, "little").decode("utf-8"))
                except ValueError:
                    pass
                    #set_trace()

            self.entries.append(ZibEntry(address, size, name))

class ZibEntry:
    def __init__(self, address, size, name):
        self.address = address
        self.size = size
        self.name = name

class Dat(File):
    def __init__(self, path, read = True):
        super().__init__(path, read)
        self.cursor = 0;
        self.word_size = 4
    
    def decompile_file(self, entry):
        with open(self.path, "rb") as src_handle:
            src_handle.seek(self.cursor)

            with open(join(self.decompile_directory, entry.name), "wb") as dest_handle:
                dest_handle.write(src_handle.read(entry.size))

    def decompile_zib(self, entry):
        with open(self.path, "rb") as src_handle:
            src_handle.seek(self.cursor)
            self.zib = Zib(src_handle.read(entry.size), entry.name)

            dir_path = join(self.decompile_directory, self.zib.name)
            try:
                mkdir(dir_path)
            except FileExistsError:
                pass
            
            for entry in self.zib.entries:
                path = join(dir_path, entry.name)
                src_handle.seek(self.cursor + entry.address)

                with open(path, "wb") as dest_handle:
                    dest_handle.write(src_handle.read(entry.size))

    """
    Ensure the cursor is always a multiple of the word size
    """
    def increment_cursor(self, length):
        self.cursor += length
        overshoot = length % self.word_size

        if overshoot != 0:
            self.cursor += self.word_size - overshoot

class Order(File):
    def __init__(self, path, read = True):
        super().__init__(path, read)
    
    def add_entry(self, string):
        with open(self.path, "ab") as handle:
            handle.write(string.encode("utf-8"))
            handle.write((0x000A).to_bytes(2, "big"))

class Files:
    def __init__(self):
        self.toc = Toc("reference/YGO_DATA.toc")
        self.dat = Dat("reference/YGO_DATA.dat")
        self.order = Order("reference/YGO_DAT.ord", read = False)
        self.recompile_directory = "recompile"
        self.decompile_directory = "decompile"

    def decompile(self):
        for entry in self.toc.entries:
            self.order.add_entry(join(self.decompile_directory, entry.name))

            if ".zib" in entry.name:
                self.dat.decompile_zib(entry)
                self.order.add_entry(str(len(self.dat.zib.entries)))

                for zib_entry in self.dat.zib.entries:
                    self.order.add_entry(zib_entry.name)

            else:
                self.dat.decompile_file(entry)

            self.dat.increment_cursor(entry.size)

def main():
    files = Files()
    files.decompile()

    return 0

if __name__ == "__main__":
    exit(main())

