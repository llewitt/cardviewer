#!/usr/bin/env python3

from sys import exit, argv
from os import mkdir
from os.path import basename, getsize, join
from struct import pack

def pad_string(string, length):
    return ((length - len(string)) * " ") + string

def pad_bytes(buf, word_size):
    if (len(buf) % word_size) != 0:
        if type(buf) == str:
            buf += str((0).to_bytes(word_size - (len(buf) % word_size), "little"))

        else:
            buf += (0).to_bytes(word_size - (len(buf) % word_size), "little")

    return buf

def pad_size(size, word_size):
    if (size % word_size) != 0:
        size += word_size - (size % word_size)

    return size

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

        if self.read:
            self.entries = []

            with open(self.path, "r") as handle:
                for line in handle.readlines()[1:]:
                    self.entries.append(TocEntry(line))
        else:
            with open(self.path, "w") as handle:
                handle.write("UT\n")

    def add(self, entry):
        if type(entry) == str:
            size = pad_size(getsize(entry), 4)
            name = basename(entry)
            name_size = len(name)

        if type(entry) == Zib:
            size = entry.size
            name = basename(entry.name)
            name_size = len(name)

        with open(self.path, "a") as handle:
            handle.write(f"\t{hex(size)[2:]}\t{hex(name_size)[2:]}\t{name}\n")

class TocEntry:
    def __init__(self, line):
        size, name_size, self.name = line.split()
        self.size = pad_size(int(size, base = 16), 4)
        self.name_size = int(name_size, base = 16)

class Zib:
    def __init__(self, *args, read = True):
        self.read = read
        self.entry_size = 64
        if self.read:
            buf = args[0]
            self.name = args[1]
            self.entries = []

            if ".jpg" in self.name:
                field_size = 8
                address_zero_correction = 0

            else:
                field_size = 4
                address_zero_correction = -1

            entry_cnt = (int.from_bytes(buf[0:field_size], "big") - 16 + address_zero_correction) // self.entry_size

            for cnt in range(entry_cnt):
                entry = buf[cnt * self.entry_size:((cnt + 1) * self.entry_size) - 1]

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

                    name += str(byte.to_bytes(1, "little").decode("utf-8"))

                self.entries.append(ZibEntry(address, size, name))

        else:
            self.name = args[0]
            self.entries = args[1]
            final = self.entries[-1]
            self.size = final.address + pad_size(final.size, 4)

    def recompile(self, dest_handle, cursor):
        if ".jpg" in self.name:
            struct_string = ">QQ48s"
            name_size = 48
        else:
            struct_string = ">LL56s"
            name_size = 56

        for cnt, entry in enumerate(self.entries):
            path = join(self.name, entry.name)
            dest_handle.seek(cursor + (self.entry_size * cnt))
            dest_handle.write(pack(
                            struct_string, 
                            entry.address, 
                            entry.size, 
                            bytes(entry.name, "utf-8")))
           
            dest_handle.seek(cursor + entry.address)

            with open(path, "rb") as src_handle:
                dest_handle.write(src_handle.read())
    
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

        if not read:
            with open(self.path, "wb") as handle:
                pass
    
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

    def recompile_file(self, path, dest_handle):
        dest_handle.seek(self.cursor)

        with open(path, "rb") as src_handle:
            dest_handle.write(pad_bytes(src_handle.read(), 4))

        self.increment_cursor(pad_size(getsize(path), 4))

    def recompile_zib(self, entry, dest_handle):
        entry.recompile(dest_handle, self.cursor)
        self.increment_cursor(entry.size)

    """
    Ensure the cursor is always a multiple of the word size
    """
    def increment_cursor(self, size):
        self.cursor += pad_size(size, self.word_size)

class Order(File):
    def __init__(self, path, read = True):
        super().__init__(path, read)
        self.entry_size = 64

        if self.read:
            self.entries = []

            with open(self.path, "r") as handle:
                lines = iter(handle.readlines())
                for line in lines:
                    line = line.strip()

                    if ".zib" in line:
                        word_size = 16
                        zib_entries = []
                        entry_cnt = int(next(lines))

                        address = self.entry_size * entry_cnt
                        address += 16

                        for cnt in range(entry_cnt):
                            name = next(lines).strip()
                            size = getsize(join(line, name))
                            zib_entries.append(ZibEntry(address, size, name))
                            address += pad_size(size, word_size)

                        self.entries.append(Zib(
                                                line, 
                                                zib_entries, 
                                                read = False))

                    else:
                        self.entries.append(line)
    
    def add_entry(self, string):
        with open(self.path, "ab") as handle:
            handle.write(string.encode("utf-8"))
            handle.write((0x0A).to_bytes(1, "big"))

class Files:
    def __init__(self, mode):
        self.mode = mode
        if self.mode == "decompile":
            self.toc = Toc("reference/YGO_DATA.toc")
            self.dat = Dat("reference/YGO_DATA.dat")
            self.order = Order("reference/YGO_DAT.ord", read = False)
        if self.mode == "recompile":
            self.toc = Toc("recompile/YGO_DATA.toc", read = False)
            self.dat = Dat("recompile/YGO_DATA.dat", read = False)
            self.order = Order("reference/YGO_DAT.ord")
        if (self.mode != "decompile") and (self.mode != "recompile"):
            print(f"Error: Bad mode string passed to files.start({self.mode})")
            raise ValueError

        self.decompile_directory = "decompile"
        self.recompile_directory = "recompile"

        try:
            mkdir(self.decompile_directory)
        except:
            pass

        try:
            mkdir(self.recompile_directory)
        except:
            pass

    def start(self):
        if self.mode == "decompile":
            self.decompile()
        if self.mode == "recompile":
            self.recompile()

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

    def recompile(self):
        with open(self.dat.path, "wb") as handle:
            for entry in self.order.entries:
                if type(entry) == str:
                    self.dat.recompile_file(entry, handle)
                if type(entry) == Zib:
                    self.dat.recompile_zib(entry, handle)

                self.toc.add(entry)

def main():
    try:
        files = Files(argv[1])
    except ValueError:
        return -1

    files.start()

    return 0

if __name__ == "__main__":
    exit(main())

