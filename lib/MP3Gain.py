import subprocess
import queue
import threading

from lib.util import *

ENCODING = 'utf8'
MP3_GAIN_BIN = "/usr/bin/mp3gain"
MP3_GAIN_SUGGESTED_VOLUME = 89.0
QUEUE_SIZE = 8192


class MP3Gain(object):
    def __init__(self, mp3gain_bin=None, max_files=None):
        if mp3gain_bin is None:
            self.mp3gain = MP3_GAIN_BIN
        else:
            self.mp3gain = mp3gain_bin

        if max_files is None:
            self.max_files = 99
        else:
            self.max_files = max_files

        self.processing_done = threading.Event()
        self.processing_done.set()

        self.process_results = queue.Queue(QUEUE_SIZE)

    def set_mp3gain_bin(self, mp3gain_bin):
        self.mp3gain = mp3gain_bin

    def set_max_files(self, max_files):
        self.max_files = max_files

    def get_version(self):
        cmd = [self.mp3gain, '-v']
        try:
            console_process = subprocess.Popen(cmd,
                                               stdin=subprocess.DEVNULL,
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE,
                                               encoding='utf8')
        except FileNotFoundError:
            return "not found"

        process_result, result_code = console_process.communicate()
        line = result_code
        if line.startswith("{} version ".format(self.mp3gain)):
            return line.lstrip("{} version ".format(self.mp3gain))

        return "not found"

    def get_file_analysis(self, src, stored_only=False, album_analysis=False, block=False):
        cmd = [self.mp3gain, '-q', '-o']

        if not album_analysis:
            cmd.append('-e')

        if stored_only:
            cmd.extend(['-s', 'c'])

        return self.process_mp3gain_cmd(cmd, src, block=block)

    def set_volume(self, src, volume, use_album_gain, block=False):
        cmd = [self.mp3gain, '-c', '-q', '-o', '-d', str(int(volume - MP3_GAIN_SUGGESTED_VOLUME))]

        if use_album_gain:
            cmd.append('-a')
        else:
            cmd.append('-r')

        return self.process_mp3gain_cmd(cmd, src, block=block)

    def undo_gain(self, src, block=False):
        cmd = [self.mp3gain, '-q', '-o', '-u']
        return self.process_mp3gain_cmd(cmd, src, block=block)

    def delete_tags(self, src, block=False):
        cmd = [self.mp3gain, '-q', '-o', '-s', 'd']
        return self.process_mp3gain_cmd(cmd, src, block=block)

    def process_mp3gain_cmd(self, cmd, input_files, block=False):
        self.processing_done.wait()

        max_files = self.max_files

        if isinstance(input_files, str):
            input_files = [input_files]

        mp3_lists = split_list(input_files, max_files)

        cmd_list = []
        expected_results = 0

        for mp3_list in mp3_lists:
            cmd_tmp = cmd.copy()
            cmd_tmp.extend(mp3_list)
            cmd_list.append([cmd_tmp, len(mp3_list)])
            expected_results = expected_results + len(mp3_list)

        if block:
            return self.process_mp3gain_cmd_block(cmd_list)

        self.processing_done.clear()
        process_thread = threading.Thread(target=lambda: self.process_mp3gain_cmd_thread(cmd_list))
        process_thread.start()

        return expected_results

    def process_mp3gain_cmd_block(self, cmd_list):
        results = []

        for cmd_info in cmd_list:
            cmd = cmd_info[0]
            num_files = cmd_info[1]
            console_process = subprocess.Popen(cmd,
                                               stdin=subprocess.DEVNULL,
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.DEVNULL,
                                               encoding='utf8')

            process_result, result_code = console_process.communicate()
            lines = process_result.splitlines()

            headers = lines[0].split('\t')

            for idx in range(1, num_files + 1):
                result = self.get_result(tag_line=[headers, lines[idx]])
                results.append(result)

        return results

    def process_mp3gain_cmd_thread(self, cmd_list):
        self.processing_done.clear()

        while not self.process_results.empty():
            try:
                _ = self.process_results.get(block=False)
            except queue.Empty:
                pass

        for cmd_info in cmd_list:
            cmd = cmd_info[0]
            num_files = cmd_info[1]
            console_process = subprocess.Popen(cmd,
                                               stdin=subprocess.DEVNULL,
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.DEVNULL,
                                               encoding='utf8',
                                               bufsize=32768)

            line = console_process.stdout.readline()
            line = line.rstrip('\n')
            headers = line.split('\t')

            while True:
                line = console_process.stdout.readline()

                if line != "":
                    try:
                        self.process_results.put([headers, line], block=False)
                    except queue.Full:
                        pass
                else:
                    if console_process.poll() is not None:
                        break

                console_process.stdout.flush()

        self.processing_done.set()

    def get_result(self, block=True, timeout=0.01, tag_line=None, debug_output=False):
        ints = ["MP3 gain", "Max global_gain", "Min global_gain", "Album gain",
                "Album Max global_gain", "Album Min global_gain"]
        floats = ["dB gain", "Max Amplitude", "Album dB gain", "Album Max Amplitude"]

        if tag_line is None:
            while tag_line is None:
                tag_line = self.process_results.get(block=block, timeout=timeout)
                line = tag_line[1][0:7]
                # Parsing is pretty weird here. Just sorta brute-forcing my way through this.
                if line in ["Applyin", "No chan", "\"Album\"", "\n", "...but "]:
                    tag_line = None

        headers = tag_line[0]
        line = tag_line[1]

        mp3 = line.rstrip('\n')
        if debug_output:
            print("Result: {}".format(mp3))

        entry = dict()
        entry["tag_exists"] = False

        for idx, value in enumerate(mp3.split('\t')):
            if value != "NA":
                entry[headers[idx]] = value

        for param in entry:
            if param in ints:
                entry["tag_exists"] = True
                entry[param] = int(entry[param])
            elif param in floats:
                entry["tag_exists"] = True
                entry[param] = float(entry[param])

        return entry

    def is_running(self):
        return not self.processing_done.is_set() or not self.process_results.empty()
