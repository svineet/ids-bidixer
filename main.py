#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup

import argparse
import re

IDS_URL = "http://lingweb.eva.mpg.de/cgi-bin/ids/ids.pl?"\
          "com=simple_browse&lg_id={}"


def combine(d1, d2):
    data = {}
    for (key, value) in d1.items():
        data[value] = d2[key]
    return data


def process_word(word):
    word = re.sub(r'\s', '<b/>', word)
    return word


def scrape_words(lg_id, lg_id2):
    print('Sending request to '+IDS_URL.format(lg_id))
    p = requests.get(IDS_URL.format(lg_id))
    p.encoding = 'utf-8'
    print('Fetched resource.')

    print('Sending request to '+IDS_URL.format(lg_id2))
    p2 = requests.get(IDS_URL.format(lg_id2))
    p2.encoding = 'utf-8'
    print('Fetched resource.')

    soupl = BeautifulSoup(p.text, 'lxml')
    soupr = BeautifulSoup(p2.text, 'lxml')

    data = []
    for (lword_out, rword_out) in zip(soupl.select("#data_1"),
                                      soupr.select("#data_1")):
        for (lword, rword) in zip(lword_out.select('tr > td'),
                                  rword_out.select('tr > td')):
            lwords = lword.text.strip().replace(',', ';').split(';')
            rwords = rword.text.strip().replace(',', ';').split(';')
            lwords = map(lambda x: x.strip(), lwords)
            rwords = map(lambda x: x.strip(), rwords)

            # Split multiple words in one definition by ';'
            for w in lwords:
                for w2 in rwords:
                    if w != '--' and w2 != '--' and all([w, w2]):
                        data.append((process_word(w),
                                     process_word(w2)))

    return (data, soupl.select('a')[0].text, soupr.select('a')[0].text)


def bidix_output(data):
    content = """<?xml version="1.0" encoding="UTF-8"?>
<!-- Data scraped from Intercontinental Dictionary Series -->

<dictionary>
    <section id="main" type="standard">
"""

    for (key, value) in data:
        content += """    <e><p><l>{}</l> <r>{}</r></p></e> \n""".format(key,
                                                                         value)

    content += """
    </section>
</dictionary>
    """

    return content


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "lg_id1", help="Language ID of the first language (left language)",
        type=int
        )
    parser.add_argument(
        "lg_id2", help="Language ID of the second language (right language)",
        type=int)
    parser.add_argument("--file", "-f", help="Output file name for bidix",
                        default=None)
    args = parser.parse_args()

    d_result, lgc1, lgc2 = scrape_words(args.lg_id1, args.lg_id2)

    if not args.file:
        file_name = "apertium-{}-{}.dix".format(lgc1, lgc2)
    else:
        file_name = args.file

    print("Writing to {}".format(file_name))
    with open(file_name, 'w') as fhandle:
        fhandle.write(bidix_output(d_result))
