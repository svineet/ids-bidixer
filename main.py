#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup

import argparse
import re

IDS_URL = "http://lingweb.eva.mpg.de/cgi-bin/ids/ids.pl?"\
          "com=simple_browse&lg_id={}"
EXTRA_BRACKET_INFO = re.compile(r'(.*)\s?\((.*)\)')


def process_word(word):
    commenting = EXTRA_BRACKET_INFO.match(word)
    com = ""
    if commenting:
        word, com = commenting.groups()

    word = re.sub(r'\s', '<b/>', word)
    return (com, word)


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
    selector2 = selector1 = "#data_1"
    lg1 = soupl.select('a')[0].text
    lg2 = soupr.select('a')[0].text

    if lg1 == 'rus':
        selector1 = '#russian'
    if lg1 == 'por':
        selector1 = '#portugese'
    if lg1 == 'fra':
        selector1 = '#french'
    if lg1 == 'spa':
        selector1 = '#spanish'

    if lg2 == 'rus':
        selector2 = '#russian'
    if lg2 == 'por':
        selector2 = '#portugese'
    if lg2 == 'fra':
        selector2 = '#french'
    if lg2 == 'spa':
        selector2 = '#spanish'

    for (lword_out, rword_out, english) in zip(soupl.select(selector1),
                                               soupr.select(selector2),
                                               soupr.select("#english")):
        for (lword, rword, eng_word) in zip(lword_out.select('tr > td'),
                                            rword_out.select('tr > td'),
                                            english.select('tr > td')):
            lwords = lword.text.strip().replace('/', ';')\
                                       .replace(',', ';')\
                                       .split(';')
            rwords = rword.text.strip().replace('/', ';')\
                                       .replace(',', ';')\
                                       .split(';')
            lwords = map(lambda x: x.strip(), lwords)
            rwords = map(lambda x: x.strip(), rwords)

            grammar_info = ""
            if 'noun' in eng_word.text:
                grammar_info += '<s n="n"/>'
            if 'vb' in eng_word.text:
                grammar_info += '<s n="vblex"/>'
            if 'trans' in eng_word.text:
                grammar_info += '<s n="tv"/>'
            if 'intrans' in eng_word.text:
                grammar_info += '<s n="iv"/>'

            # Split multiple words in one definition by ';'
            for w in lwords:
                for w2 in rwords:
                    if w != '--' and w2 != '--' and all([w, w2]):
                        comment1, p1 = process_word(w)
                        comment2, p2 = process_word(w2)
                        data.append((p1+grammar_info,
                                     p2+grammar_info,
                                     comment1+comment2))

    return (data, lg1, lg2)


def bidix_output(data):
    content = """<?xml version="1.0" encoding="UTF-8"?>
<!-- Data scraped from Intercontinental Dictionary Series -->

<dictionary>
    <section id="main" type="standard">
"""

    for (key, value, comment) in data:
        if '(' in key or '(' in value:
            content += "    <!-- gave up on: "
            content += """    <e><p><l>{}</l> <r>{}</r></p></e> -->"""\
                .format(key,
                        value)
        else:
            content += """    <e><p><l>{}</l> <r>{}</r></p></e>""".format(key,
                                                                          value)
        if comment:
            content += """  <!-- {} --> \n""".format(comment)
        else:
            content += "\n"

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
