import os
import re
from dataclasses import dataclass

from click import group, argument
from requests import get
from bs4 import BeautifulSoup

from pandas import DataFrame

from .util import normalize
from .Section import Section


@group()
def main():
    pass

CACHE_PATH = 'assets/cache/{champion}.html'

LINK_TEMPLATE = re.compile(r'\s*Link▶️\s*')

TIMEOUT = 3600  # seconds


@main.command()
@argument('path', type = str, default = 'assets/pale.tsv')
def parse(path: str):
    # champions = ['kindred', 'jhin']
    # champions = ['jhin']
    champions = ['kindred']

    i = 0

    records = []
    src_index = set()

    for champion in champions:
        if os.path.exists(cache_path := CACHE_PATH.format(champion = champion)):
            with open(cache_path, 'r', encoding = 'utf-8') as file:
                page = file.read()
        else:
            response = get(f'https://leagueoflegends.fandom.com/wiki/{champion.capitalize()}/LoL/Audio', timeout = TIMEOUT)

            if (status := response.status_code) == 200:
                page = response.text

                with open(cache_path, 'w', encoding = 'utf-8') as file:
                    file.write(page)
            else:
                raise ValueError(f'Incorrect response status: {status}')

        # if response.status_code == 200:

        bs = BeautifulSoup(page, 'html.parser')

        # for heading in bs.find_all('span', {'class': 'mw-headline'}):

        # sections = []

        # headings = bs.select('h2 > span.mw-headline')
        # heading_index = set()

        # for heading in headings[::-1]:
        #     # print('-', heading.text)
        #     heading_index.add(heading)

        #     subheadings = heading.find_all_next('span', {'class': 'mw-headline'})

        #     n_subheadings = 0

        #     subsections = []

        #     def handle_subheadings():
        #         nonlocal subheadings, n_subheadings, heading_index

        #         for subheading in subheadings:

        #             if subheading in heading_index:
        #                 break

        #             # print('##', subheading.text)
        #             subsections.append(subheading)
        #             heading_index.add(subheading)

        #             n_subheadings += 1

        #     handle_subheadings()

        #     if n_subheadings < 1:
        #         subheadings = heading.find_all_next('dt')

        #         handle_subheadings()

        #     sections.append(Section(header = heading, elements = subsections))

        # sections = sections[::-1]

        sections = Section.from_separators(
            separators = bs.select('h2 > span.mw-headline'),
            find_next = lambda separator: separator.find_all_next('span', {'class': 'mw-headline'}),
            find_next_exclusions = lambda separator: separator.find_all_next('dt')
        )

        for section in sections:
            print('#', section.title)
            for item in section.items:
                print('##', item)

        # for audio in bs.find_all('audio', {'class': 'ext-audiobutton'}):
        #     if source := audio.find('source'):
        #         text = SPACE_TEMPLATE.sub(' ', LINK_TEMPLATE.sub('', audio.parent.parent.text))
        #         src = source['src']

        #         # print(source['src'])
        #         # print(text)
        #         # print()

        #         if src not in src_index:
        #             records.append({'text': text, 'sound': src, 'champion': champion})
        #             src_index.add(src)

        #         i += 1

        # else:
        #     raise ValueError(f'Cannot fetch data for {champion}')

    # print(f'found {i} records for {champion}')

    # df = DataFrame.from_records(records)
    # df.to_csv('assets/pale.tsv', sep = '\t', index = False)


if __name__ == '__main__':
    main()
