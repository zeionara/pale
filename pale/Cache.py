import os

from requests import get


TIMEOUT = 3600  # seconds

STATUS_OK = 200


class Cache:
    def __init__(self, url: str, file: str):
        self.url = url
        self.file = file

    def __enter__(self):
        if os.path.exists(path := self.file):
            with open(path, 'r', encoding = 'utf-8') as file:
                page = file.read()
        else:
            response = get(self.url, timeout = TIMEOUT, allow_redirects = True)

            if (status := response.status_code) == STATUS_OK:
                page = response.text

                with open(path, 'w', encoding = 'utf-8') as file:
                    file.write(page)
            else:
                raise ValueError(f'Incorrect response status: {status} when opening page {self.url}')

        return page

    def __exit__(self, exc_type, exc_value, exc_tb):
        pass
