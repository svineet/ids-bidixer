#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup

import argparse

IDS_URL = "http://lingweb.eva.mpg.de/cgi-bin/ids/ids.pl?"\
          "com=simple_browse&lg_id={}"


def combine(d1, d2):
    data = {}
    for (key, value) in d1.items():
        data[value] = d2[key]
    return data


def scrape_words(lg_id):
    print('Sending request to '+IDS_URL.format(lg_id))
    p = requests.get(IDS_URL.format(lg_id))
    print('Fetched resource.')
    soup = BeautifulSoup(p.text, 'lxml')

    data = {}
    for (en_word_out, lg_word_out) in zip(soup.select("#english"),
                                          soup.select("#data_1")):
        for (en_word, lg_word) in zip(en_word_out.select('tr > td'),
                                      lg_word_out.select('tr > td')):
            data[en_word.text] = lg_word.text
    return (data, soup.select('a')[0].text)


def bidix_output(data):
    content = """<?xml version="1.0" encoding="UTF-8"?>

<dictionary>
    <section id="main" type="standard">
"""

    for (key, value) in data.items():
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

    d1, lgc1 = scrape_words(args.lg_id1)
    d2, lgc2 = scrape_words(args.lg_id2)

    d3 = combine(d1, d2)

    if not args.file:
        file_name = "apertium-{}-{}.dix".format(lgc1, lgc2)
    else:
        file_name = args.file

    print("Writing to {}".format(file_name))
    with open(file_name, 'w') as fhandle:
        fhandle.write(bidix_output(d3))
