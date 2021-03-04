import mmap

def get_num_lines(file_path):
    """
    Returns the number of lines in the file at the given path.
    """
    fp = open(file_path, "r+")
    buf = mmap.mmap(fp.fileno(), 0)
    lines = 0
    while buf.readline():
        lines += 1
    return lines
