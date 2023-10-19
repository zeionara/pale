import re
from dataclasses import dataclass
from urllib.parse import quote

from click import group, argument
from bs4 import BeautifulSoup
from tqdm import tqdm

from pandas import DataFrame

from .Section import Section
from .Cache import Cache
from .util import normalize


@group()
def main():
    pass


INDEX_FILENAME = '_index'
INDEX_URL = 'https://leagueoflegends.fandom.com/wiki/League_of_Legends_Wiki'

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

    champions = []

    with Cache(url = INDEX_URL, file = CACHE_PATH.format(champion = INDEX_FILENAME)) as page:
        bs = BeautifulSoup(page, 'html.parser')

        for icon in bs.find_all('span', {'class': 'grid-icon'}):
            champions.append(icon['data-champion'])

    # champions = champions[90:]
    # champions = ['kindred', 'jhin']
    # champions = ['jhin']
    # champions = ['kindred']

    i = 0

    records = []

    for champion in tqdm(champions):
        # if os.path.exists(cache_path := CACHE_PATH.format(champion = champion)):
        #     with open(cache_path, 'r', encoding = 'utf-8') as file:
        #         page = file.read()
        # else:
        #     response = get(f'https://leagueoflegends.fandom.com/wiki/{champion.capitalize()}/LoL/Audio', timeout = TIMEOUT)

        #     if (status := response.status_code) == 200:
        #         page = response.text

        #         with open(cache_path, 'w', encoding = 'utf-8') as file:
        #             file.write(page)
        #     else:
        #         raise ValueError(f'Incorrect response status: {status}')

        with Cache(
            url = f'https://leagueoflegends.fandom.com/wiki/{quote(champion.split("&")[0].strip(), safe = "/", encoding = None, errors = None)}/LoL/Audio',
            file = CACHE_PATH.format(champion = champion)
        ) as page:
            bs = BeautifulSoup(page, 'html.parser')

            sections = Section.from_separators(
                separators = bs.select('h2 > span.mw-headline'),
                find_next = lambda separator: separator.find_all_next('span', {'class': 'mw-headline'}),
                find_next_exclusions = lambda separator: separator.find_all_next('dt')
            )

            separators = []
            element_to_section = {}

            for section in sections:
                if section.length < 1:
                    separators.append(section.header)
                else:
                    separators.extend(section.elements)

                for element in section.elements:
                    element_to_section[element] = section

            audios = Section.from_separators(
                separators = separators,
                find_next = lambda separator: separator.find_all_next('audio', {'class': 'ext-audiobutton'}),
                allow_duplicates = True
            )

            audio_index = set()

            for section in audios:
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
                                champion = champion.lower()
                            )
                        )

    df = DataFrame.from_records(record.as_dict for record in records)
    df.to_csv('assets/pale.tsv', sep = '\t', index = False)


if __name__ == '__main__':
    main()
