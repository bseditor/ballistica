# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Tools for parsing/filtering makefiles."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional, List, Tuple


@dataclass
class Section:
    """Represents a section of a Makefile."""
    name: Optional[str]
    paragraphs: List[Paragraph]


@dataclass
class Paragraph:
    """Represents a continuous set of non-blank lines in a Makefile."""
    contents: str

    def get_logical_lines(self) -> List[str]:
        """Return contents broken into logical lines.

        Lines joined by continuation chars are considered a single line.
        """
        return self.contents.replace('\\\n', '').splitlines()


class Makefile:
    """Represents an entire Makefile."""

    header_line_full = '#' * 80
    header_line_empty = '#' + ' ' * 78 + '#'

    def __init__(self, contents: str):

        self.sections: List[Section] = []

        self._original = copy.copy(contents)

        lines = contents.splitlines()

        paragraphs: List[Paragraph] = []

        # First off, break into paragraphs (continuous sets of lines)
        plines: List[str] = []
        for line in lines:

            if line.strip() == '':
                if plines:
                    paragraphs.append(Paragraph(contents='\n'.join(plines)))
                    plines = []
                continue
            plines.append(line)
        if plines:
            paragraphs.append(Paragraph(contents='\n'.join(plines)))

        # Now break all paragraphs into sections.
        section = Section(name=None, paragraphs=[])
        self.sections.append(section)
        for paragraph in paragraphs:

            # Look for our very particular section headers and start
            # a new section whenever we come across one.
            plines = paragraph.contents.splitlines()
            # pylint: disable=too-many-boolean-expressions
            if (len(plines) == 5 and plines[0] == self.header_line_full
                    and plines[1] == self.header_line_empty
                    and len(plines[2]) == 80 and plines[2][0] == '#'
                    and plines[2][-1] == '#'
                    and plines[3] == self.header_line_empty
                    and plines[4] == self.header_line_full):
                section = Section(name=plines[2][1:-1].strip(), paragraphs=[])
                self.sections.append(section)
            else:
                section.paragraphs.append(paragraph)

    def find_assigns(self, name: str) -> List[Tuple[Section, int]]:
        """Return section/index pairs for paragraphs containing an assign.

        Note that the paragraph may contain other statements as well.
        """
        found: List[Tuple[Section, int]] = []
        for section in self.sections:
            for i, paragraph in enumerate(section.paragraphs):
                if any(
                        line.split('=')[0].strip() == name
                        for line in paragraph.get_logical_lines()):
                    found.append((section, i))
        return found

    def find_targets(self, name: str) -> List[Tuple[Section, int]]:
        """Return section/index pairs for paragraphs containing a target.

        Note that the paragraph may contain other statements as well.
        """
        found: List[Tuple[Section, int]] = []
        for section in self.sections:
            for i, paragraph in enumerate(section.paragraphs):
                if any(line.split()[0] == name + ':'
                       for line in paragraph.get_logical_lines()):
                    found.append((section, i))
        return found

    def get_output(self) -> str:
        """Generate a Makefile from the current state."""

        output = ''
        for section in self.sections:
            did_first_entry = False
            if section.name is not None:
                output += '\n\n' + self.header_line_full + '\n'
                output += self.header_line_empty + '\n'
                spacelen = 78 - len(section.name)
                output += '#' + ' ' * (spacelen // 2) + section.name
                spacelen -= spacelen // 2
                output += ' ' * spacelen + '#\n'
                output += self.header_line_empty + '\n'
                output += self.header_line_full + '\n'
                did_first_entry = True
            for paragraph in section.paragraphs:
                if did_first_entry:
                    output += '\n'
                output += paragraph.contents + '\n'
                did_first_entry = True
        # print(output)

        return output
