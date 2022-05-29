import linecache

path = "text.txt"
with open(path, "w") as f:
    f.write("aa\nbb\ncc\n")

line = linecache.getline(path, 2)
print(line)

with open(path, "a") as f:
    f.write("aa\nbb\ncc\n")

linecache.clearcache()
line = linecache.getline(path, 5)
print(line)