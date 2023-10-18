import re

from click import group, argument
from requests import get
from bs4 import BeautifulSoup

from pandas import DataFrame


@group()
def main():
    pass


LINK_TEMPLATE = re.compile(r'\s*Link▶️\s*')
SPACE_TEMPLATE = re.compile(r'\s+')

TIMEOUT = 3600  # seconds


@main.command()
@argument('path', type = str)
def parse(path: str):
    champions = ['kindred', 'jhin']

    # i = 0

    records = []
    src_index = set()

    for champion in champions:
        response = get(f'https://leagueoflegends.fandom.com/wiki/{champion.capitalize()}/LoL/Audio', timeout = TIMEOUT)

        if response.status_code == 200:
            bs = BeautifulSoup(response.text, 'html.parser')

            for audio in bs.find_all('audio', {'class': 'ext-audiobutton'}):
                if source := audio.find('source'):
                    text = SPACE_TEMPLATE.sub(' ', LINK_TEMPLATE.sub('', audio.parent.parent.text))
                    src = source['src']

                    # print(source['src'])
                    # print(text)
                    # print()

                    if src not in src_index:
                        records.append({'text': text, 'sound': src, 'champion': champion})
                        src_index.add(src)

                    # i += 1

            # for item in bs.find_all('li'):
            #     if audio := item.find('audio', {'class': 'ext-audiobutton'}):
            #         if source := audio.find('source'):
            #             text = LINK_TEMPLATE.sub('', item.text)

            #             print(source['src'])
            #             print(text)
            #             print()

            #             i += 1
        else:
            raise ValueError(f'Cannot fetch data for {champion}')

        # print('found', i, 'values')

        # print(len(rows))
        # print(rows[:2])

        df = DataFrame.from_records(records)
        df.to_csv('assets/pale.tsv', sep = '\t', index = False)


if __name__ == '__main__':
    main()
