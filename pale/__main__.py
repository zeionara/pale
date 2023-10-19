import os
import re
from dataclasses import dataclass

from click import group, argument
from requests import get
from bs4 import BeautifulSoup

from pandas import DataFrame

from .Section import Section
from .util import normalize


@group()
def main():
    pass


CACHE_PATH = 'assets/cache/{champion}.html'

LINK_TEMPLATE = re.compile(r'\s*Link▶️\s*')

TIMEOUT = 3600  # seconds


@dataclass
class Record:
    header: BeautifulSoup
    subheader: BeautifulSoup | None
    item: BeautifulSoup
    source: BeautifulSoup
    champion: str

    @property
    def as_dict(self):
        return {
            'header': normalize(self.header.text),
            'subheader': None if self.subheader is None else normalize(self.subheader.text),
            'text': normalize(LINK_TEMPLATE.sub('', self.item.text)),
            'source': self.source['src'],
            'champion': self.champion
        }


@main.command()
@argument('path', type = str, default = 'assets/pale.tsv')
def parse(path: str):
    champions = ['kindred', 'jhin']
    # champions = ['jhin']
    # champions = ['kindred']

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

        sections = Section.from_separators(
            separators = bs.select('h2 > span.mw-headline'),
            find_next = lambda separator: separator.find_all_next('span', {'class': 'mw-headline'}),
            find_next_exclusions = lambda separator: separator.find_all_next('dt')
        )

        # for section in sections:
        #     print('#', section.title)
        #     for item in section.items:
        #         print('##', item)

        # separators = [
        #     item
        #     for section in sections
        #     for item in (
        #         [section.header] if section.length < 1 else section.elements
        #     )
        # ]

        separators = []
        element_to_section = {}

        for section in sections:
            if section.length < 1:
                separators.append(section.header)
            else:
                separators.extend(section.elements)

            for element in section.elements:
                # print(element.text, ' -> ', section.header.text)
                element_to_section[element] = section

        audios = Section.from_separators(
            separators = separators,
            find_next = lambda separator: separator.find_all_next('audio', {'class': 'ext-audiobutton'}),
            allow_duplicates = True
        )

        audio_index = set()

        for section in audios:
            # print('*', section.title, len(section.elements))
            i += len(section.elements)
            for element in section.elements:
                audio_index.add(element)

                if source := element.find('source'):
                    root = element_to_section.get(section.header)
                    records.append(
                        Record(
                            header = section.header if root is None else root.header,
                            subheader = None if root is None else section.header,
                            item = element.parent.parent,
                            source = source,
                            champion = champion
                        )
                    )

            #     print(element.parent.parent.text)
            #     i += 1

        # for separator in separators:
        #     print(separator.text)

        for audio in bs.find_all('audio', {'class': 'ext-audiobutton'}):
            if audio not in audio_index:
                print(audio.parent.parent.text)
            # if source := audio.find('source'):
            #     text = SPACE_TEMPLATE.sub(' ', LINK_TEMPLATE.sub('', audio.parent.parent.text))
            #     src = source['src']

        # for audio in bs.find_all('audio', {'class': 'ext-audiobutton'}):
        #     if source := audio.find('source'):
        #         text = audio.parent.parent.text  # SPACE_TEMPLATE.sub(' ', LINK_TEMPLATE.sub('', audio.parent.parent.text))
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

        # print(f'found {len(records)} records for {champion}')
    # print(records[10].as_dict)

    df = DataFrame.from_records(record.as_dict for record in records)
    df.to_csv('assets/pale.tsv', sep = '\t', index = False)


if __name__ == '__main__':
    main()
