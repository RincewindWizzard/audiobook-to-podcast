import sys
import os
import os.path
import re
import pprint
import eyed3
from collections import namedtuple
from pydub import AudioSegment
from feedgen.feed import FeedGenerator

pp = pprint.PrettyPrinter(indent=4)
title_regex = re.compile("Kapitel (?P<chapter_num>\d*): \"(?P<chapter_title>[^\"]*)\", Teil (?P<part_num>\d*)")

MP3 = namedtuple('MP3', ['chapter_num', 'chapter_title', 'chapter_part', 'path'])

def feed():
    fg = FeedGenerator()
    fg.id('http://lernfunk.de/media/654321')
    fg.title('Some Testfeed')
    fg.author( {'name':'John Doe','email':'john@example.de'} )
    fg.link( href='http://example.com', rel='alternate' )
    fg.logo('http://ex.com/logo.jpg')
    fg.subtitle('This is a cool feed!')
    fg.link( href='http://larskiesow.de/test.atom', rel='self' )
    fg.language('en')
    rssfeed  = fg.rss_str(pretty=True)
    print(rssfeed.decode("utf-8"))

def read_mp3(mp3):
    tags = eyed3.load(mp3).tag
    m = title_regex.match(tags.title)
    if m:
        return MP3(int(m.group("chapter_num")), m.group("chapter_title"), int(m.group("part_num")), mp3)
    elif tags.title == 'Ansage':
        return MP3(0, tags.title, 0, mp3)
    else:
        raise IOError("Could not parse mp3! {}\n{}".format(tags.title, mp3))

def get_audiofiles(path):
    for disk in os.listdir(path):
        if disk.find('CD') == 0:
            disk = os.path.join(path, disk)
            for mp3 in os.listdir(disk):
                yield read_mp3(os.path.join(disk, mp3))

def concat_mp3(audiofiles, dst):
    chapter = AudioSegment.from_mp3(audiofiles[0])
    for track in audiofiles[1:]:
        chapter + AudioSegment.from_mp3(track)
    print(dst)
    chapter.export(dst, format="mp3")

def audiolength(mp3):
    audio = AudioSegment.from_mp3(mp3)
    return audio.duration_seconds

def main(argv):
    root_dir = argv[1]
    dst = argv[2]

    audiofiles = list(get_audiofiles(root_dir))
    audiofiles.sort(key=lambda x: (x.chapter_num, x.chapter_part))
    chapters = [[]]
    for mp3 in audiofiles:
        if len(chapters[-1]) > 0 and not chapters[-1][-1].chapter_num == mp3.chapter_num:
            chapters.append([])
        chapters[-1].append(mp3)

    cur_timestamp = 0
    chapter_marks = []
    for chapter in chapters:
        #concat_mp3([ c.path for c in chapter ], os.path.join(dst, '{:02d}-{}.mp3'.format(chapter[0].chapter_num, chapter[0].chapter_title)))
        print(cur_timestamp, chapter[0].chapter_title)
        chapter_marks.append((cur_timestamp, chapter[0].chapter_title))
        cur_timestamp += sum([ audiolength(mp3.path) for mp3 in chapter ])
    pprint.pprint(chapter_marks)


if __name__ == '__main__':
    #main(sys.argv)
    feed()