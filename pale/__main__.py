import re
import os
from dataclasses import dataclass
from urllib.parse import quote

from click import group, argument
from bs4 import BeautifulSoup
from tqdm import tqdm
from requests import get

from pandas import DataFrame, read_csv
import numpy as np

from .Section import Section
from .Cache import Cache
from .util import normalize, to_kebab_case, drop_non_alphanumeric


@group()
def main():
    pass


INDEX_FILENAME = '_index'
INDEX_URL = 'https://leagueoflegends.fandom.com/wiki/League_of_Legends_Wiki'

CACHE_PATH = 'assets/cache/{champion}.html'

SPACE = ' '
LINK_TEMPLATE = re.compile(fr'\s*Link{SPACE}▶️\s*')

PATH = 'assets/pale.tsv'


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
            'header': normalize(self.header.get_text(separator = SPACE)),
            'subheader': None if self.subheader is None else normalize(self.subheader.get_text(separator = SPACE)),
            'text': normalize(LINK_TEMPLATE.sub(SPACE, self.item.get_text(separator = SPACE))).strip(),
            'source': self.source['src'],
            'champion': self.champion
        }


@main.command()
@argument('path', type = str, default = PATH)
@argument('output', type = str, default = 'assets/sound')
def pull_sound(path: str, output: str):
    if not os.path.isdir(output):
        os.makedirs(output)

    df = read_csv(path, sep = '\t')

    stem_to_index = {}

    def make_sound_filename(row):
        header = row['header']
        subheader = row['subheader']
        champion = drop_non_alphanumeric(row['champion'])

        stem = None
        key = None

        if subheader == subheader:  # if subheader is nan
            stem = to_kebab_case(f'{header} {subheader}')
            key = to_kebab_case(f'{champion} {header} {subheader}')
        else:
            stem = to_kebab_case(header)
            key = to_kebab_case(f'{champion} {header}')

        if (index := stem_to_index.get(key)):
            stem_to_index[key] = index + 1
            stem = f'{stem}-{index:03d}'
        else:
            stem_to_index[key] = 1
            stem = f'{stem}-000'

        return champion, stem

    df['folder'], df['filename'] = zip(*df.apply(make_sound_filename, axis = 1))

    # print(df)

    pbar = tqdm(total = df.shape[0])

    for _, row in df.iterrows():
        folder = os.path.join(output, row['folder'])
        source = row['source']

        if not os.path.isdir(folder):
            os.makedirs(folder)

        file = os.path.join(folder, f'{row["filename"]}.ogg')

        if os.path.isfile(file):
            pbar.update()
            continue

        # print(file, source)

        response = get(source)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Open the local file in binary write mode and write the downloaded content to it
            with open(file, 'wb') as handle:
                handle.write(response.content)
        else:
            print(f"Failed to download the file {source} as {file}. Status code: {response.status_code}")

        pbar.update()

    # print(max(stem_to_index.values()))

    # print(sorted(stem_to_index.items(), key = lambda item: item[1], reverse = True)[:10])

    # print(df.source.tolist())


@main.command()
@argument('path', type = str, default = PATH)
def clean(path: str):
    df = read_csv(path, sep = '\t')

    # effects = df[~(df.text.str.contains('"'))].text

    # for item in sorted(set(effects.to_list()), key = len, reverse = True):
    #     print(item)

    # effects = df[df.text.isna()]

    # df['quote'] = df.text.str.contains('"')
    df['quote'] = df.text.apply(lambda text: True if text.startswith('"') and text.endswith('"') else np.nan if '"' in text else False)
    df.text = df.text.apply(lambda text: text[1:-1] if text.startswith('"') and text.endswith('"') else text)

    df.to_csv('assets/annotated.tsv', sep = '\t', index = False)

    df = df.dropna(subset = ['quote'])
    df = df[df.quote]
    df = df.drop(['quote', 'source'], axis = 1).drop_duplicates()

    df.to_csv('assets/quotes.tsv', sep = '\t', index = False)


@main.command()
@argument('path', type = str, default = PATH)
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
    # print(df)
    df.to_csv(path, sep = '\t', index = False)


if __name__ == '__main__':
    main()
