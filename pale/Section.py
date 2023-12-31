from dataclasses import dataclass

from bs4 import BeautifulSoup

from .util import normalize


@dataclass
class Section:
    header: BeautifulSoup
    elements: tuple[BeautifulSoup]

    @property
    def title(self):
        return normalize(self.header.text)

    @property
    def items(self):
        return tuple(normalize(element.text) for element in self.elements)

    @classmethod
    def from_separators(cls, separators: [BeautifulSoup], find_next: callable, find_next_exclusions: callable = None, allow_duplicates: bool = False):
        sections = []

        heading_index = set()

        for heading in separators[::-1]:
            # print('-', heading.text)
            heading_index.add(heading)

            subheadings = find_next(heading)

            n_subheadings = 0

            subsections = []
            duplicates = []

            def handle_subheadings():
                nonlocal subheadings, n_subheadings, heading_index, subsections, duplicates

                for subheading in subheadings:

                    if subheading in heading_index:
                        duplicates.append(subheading)
                        continue

                    if len(duplicates) > 0:
                        if allow_duplicates:
                            subsections.extend(duplicates)
                        duplicates = []

                    # print('##', subheading.text)
                    subsections.append(subheading)
                    heading_index.add(subheading)

                    n_subheadings += 1

            handle_subheadings()

            if find_next_exclusions is not None:
                subheadings = find_next_exclusions(heading)

                if n_subheadings < 1:
                    handle_subheadings()
                else:
                    for subheading in subheadings:
                        heading_index.add(subheading)

            sections.append(cls(header = heading, elements = subsections))

        return sections[::-1]

    @property
    def length(self):
        return len(self.elements)
