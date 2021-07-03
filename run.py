#!/usr/bin/env python3

from sys import exit, argv
from os import mkdir
from os.path import basename, getsize, join
from pdb import set_trace
from struct import pack, unpack

def round_size(size, word_size, up = True):
    remainder = size % word_size
    
    if remainder != 0:
        if up:
            size += word_size - remainder

        else:
            size -= remainder
        
    return size

def strip_bytes(buf, char = 0):
    for i in range(len(buf)):
        if buf[-i - 1] != char:
            break

    return buf[:-i]

def pad_file(path, word_size):
    with open(path, "ab") as handle:
        handle.seek(0, 2)
        size = handle.tell()
        remainder = size % word_size
        
        if remainder != 0:
            handle.write((0).to_bytes(word_size - remainder, "little"))

def pad_bytes(buf, word_size):
    remainder = len(buf) % word_size
    
    if remainder != 0:
        buf += (0).to_bytes(word_size - remainder, "little")

    return buf 

class Definitions:
    def __init__(self):
        self.decompile_directory = "decompile"
        self.recompile_directory = "recompile"
        self.dat_word_size = 4
        self.zib_word_size = 16
        self.zib_entry_size = 64

class File(Definitions):
    def __init__(self, path, read = True):
        super().__init__()

        self.path = path
        self.name = basename(path)
        self.read = read

        if self.read:
            self.size = getsize(self.path)

        else:
            self.size = 0
            
            with open(self.path, "wb"):
                pass

class Toc(File):
    def __init__(self, path, read = True):
        super().__init__(path, read)

        if self.read == True:
            self.entries = []

            with open(self.path, "r") as handle:
                for line in handle.readlines()[1:]:
                    self.entries.append(TocEntry(line))

        else:
            with open(self.path, "w") as handle:
                    handle.write("UT\n")

    def add_line(self, entry):
        if type(entry) == str:
            size = getsize(entry)
            name = basename(entry)

        else:
            last = entry.entries[-1]
            size = round_size(last.address + last.size, 16)
            name = basename(entry.name)

        name_size = len(name)
        size = hex(size).lstrip("0x").rjust(12)
        name_size = hex(name_size).lstrip("0x").rjust(3)
        line = f"{size}{name_size} {name}\n"

        with open(self.path, "a") as handle:
            handle.write(line)

class TocEntry:
    def __init__(self, line, read = True):
        self.read = read

        if self.read:
            size, name_size, self.name = line.split()
            self.size = int(size, base = 16)
            self.name_size = int(name_size, base = 16)

class Zib(Definitions):
    def __init__(self, *args, read = True):
        super().__init__()

        self.name = args[0]
        self.read = read
        self.entries = []

        if ".jpg" in self.name:
            self.name_size = 48
            self.struct_string = f">QQ{self.name_size}s"

        else:
            self.name_size = 56
            self.struct_string = f">LL{self.name_size}s"

        if self.read:
            cnt = 0
            while True:
                entry = args[1][cnt * self.zib_entry_size:((cnt + 1) * self.zib_entry_size)]

                if int.from_bytes(entry[:16], "big") == 0:
                    break

                address, size, name = unpack(self.struct_string, entry)
                address = round_size(address, self.zib_word_size, up = False)
                size = int(size)
                name = strip_bytes(name).decode("utf-8")
                self.entries.append(ZibEntry(address, size, name))
                cnt += 1

        else:
            self.entries = args[1]

class ZibEntry:
    def __init__(self, address, size, name):
        self.address = address
        self.size = size
        self.name = name

class Dat(File):
    def __init__(self, path, read = True):
        super().__init__(path, read)
        self.cursor = 0;
    
    def decompile_file(self, entry):
        with open(self.path, "rb") as src_handle:
            src_handle.seek(self.cursor)

            with open(join(self.decompile_directory, entry.name), "wb") as dest_handle:
                dest_handle.write(src_handle.read(entry.size))

    def decompile_zib(self, entry):
        with open(self.path, "rb") as src_handle:
            src_handle.seek(self.cursor)
            self.zib = Zib(entry.name, src_handle.read(entry.size))
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

    def recompile_file(self, entry):
        with open(self.path, "ab") as dest_handle:
            with open(entry, "rb") as src_handle:
                buf = src_handle.read()
                dest_handle.write(buf)

    def recompile_zib(self, entry):
        for zib_entry in entry.entries:
            buf = pack(
                    entry.struct_string, 
                    zib_entry.address,
                    zib_entry.size,
                    basename(zib_entry.name.encode("utf-8")))
            with open(self.path, "ab") as handle:
                handle.write(buf)

        with open(self.path, "ab") as handle:
            handle.write((0).to_bytes(self.zib_word_size, "little"))

        for zib_entry in entry.entries:
            with open(self.path, "ab") as dest_handle:
                with open(zib_entry.name, "rb") as src_handle:
                    buf = src_handle.read()
                    buf = pad_bytes(buf, self.zib_word_size)
                    dest_handle.write(buf)

class Order(File):
    def __init__(self, path, read = True):
        super().__init__(path, read)
    
        if read:
            self.entries = []

            with open(self.path, "r") as handle:
                for line in handle:
                    if ".zib" not in line:
                        self.entries.append(line.strip())

                    else:
                        zib_name = line.strip()
                        zib_cnt = int(next(handle))
                        address = \
                                (zib_cnt * self.zib_entry_size) + \
                                self.zib_word_size

                        if ".jpg" not in zib_name:
                            address += 1

                        zib_entries = []
                        
                        for cnt in range(zib_cnt):
                            path = next(handle).strip()
                            size = getsize(path)
                            zib_entries.append(ZibEntry(address, size, path))
                            address = round_size(address + size, self.zib_word_size)
                        
                        self.entries.append(Zib(zib_name, zib_entries, read = False))

    def add_line(self, line):
        with open(self.path, "a") as handle:
            handle.write(f"{line}\n")

class Files(Definitions):
    def __init__(self):
        super().__init__()

        self.mode = argv[1]

        if self.mode == "decompile":
            self.toc = Toc("reference/YGO_DATA.toc")
            self.dat = Dat("reference/YGO_DATA.dat")
            self.order = Order("reference/YGO_DAT.ord", read = False)

        else:
            self.toc = Toc("recompile/YGO_DATA.toc", read = False)
            self.dat = Dat("recompile/YGO_DATA.dat", read = False)
            self.order = Order("reference/YGO_DAT.ord")

    def decompile(self):
        for entry in self.toc.entries:
            path = join(self.decompile_directory, entry.name)
            self.order.add_line(join(self.decompile_directory, entry.name))

            if ".zib" in entry.name:
                self.dat.decompile_zib(entry)
                self.order.add_line(str(len(self.dat.zib.entries)))

                for zib_entry in self.dat.zib.entries:
                    path = join(self.decompile_directory, entry.name, zib_entry.name)
                    self.order.add_line(path)

            else:
                self.dat.decompile_file(entry)

            self.dat.cursor += round_size(entry.size, self.dat_word_size)

    def recompile(self):
        for entry in self.order.entries:
            if type(entry) == str:
                self.dat.recompile_file(entry)
        
            else:
                self.dat.recompile_zib(entry)

            self.toc.add_line(entry)
            pad_file(self.dat.path, self.dat_word_size)

    def start(self):
        if self.mode == "recompile":
            self.recompile()

        else:
            self.decompile()

def main():
    if \
            (len(argv) != 2) and \
            (argv[1] != "decompile") and \
            (argv[1] != "recompile"):
        print(f"Useage: {argv[0]} [decompile, recompile]")
        return -1

    files = Files()
    files.start()

    return 0

if __name__ == "__main__":
    exit(main())

