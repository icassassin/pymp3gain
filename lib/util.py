from scandir import scandir


def get_paths(directory, extensions=None, recursive=False):
    if extensions is None:
        extensions = ""

    if recursive:
        file_list = [x.path for x in scantree(directory) if
                     x.name.lower().endswith(extensions)]
    else:
        file_list = [x.path for x in scandir(directory) if
                     x.name.lower().endswith(extensions)]

    return file_list


def scantree(path):
    for entry in scandir(path):
        if entry.is_dir(follow_symlinks=False):
            yield from scantree(entry.path)
        else:
            yield entry


def clip_text(text, max_length):
    if len(text) > max_length:
        length = max_length//2 - 3
        if length < 1:
            return ""

        result_text = text[0:length] + "..." + text[-length:]
    else:
        result_text = text

    return result_text


def split_list(input_list, size):
    if len(input_list) < size:
        return [input_list]

    num_lists = len(input_list)//size

    lists = []

    for idx in range(num_lists):
        lists.append(input_list[idx*size:idx*size + size])

    if size % len(input_list) != 0:
        lists.append(input_list[num_lists*size:])

    return lists


def time_as_display(msec):
    h = int(msec // 3600)
    m = int((msec - h * 3600) // 60)
    s = int(msec - h * 3600 - m * 60)

    return "{:02d}:{:02d}:{:02d}".format(h, m, s)
