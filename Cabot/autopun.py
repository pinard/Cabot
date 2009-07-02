#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright © 2004 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2004.

# This library is free software; you can redistribute it and/or
# modify it under the terms of version 2.1 of the GNU Lesser General Public
# License as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""\
Produce a phonetic pun over some text.

Usage: autopun [OPTION]... [FILE]

Options:
  -c         Convert FILE instead of reparsing standard input.

If -c is given, FILE is a list of English words and defaults to
`/usr/share/dict/words'.  A phone file is produced on standard output.  If -c
is not given, FILE is a phone file and defaults to `phones' in the database
directory; using it, each line of standard input creates a phonemically-simiar
line on standard output.  For example, "Happy Birthday" can be recast as "Hub
pip Earth tee".
"""

# The C sources, "v02i096: autopun - phonetically reparse English phrases",
# were published in comp.sources.games on 1987-11-25 by Bradford Needham
# <bradn@tekig4.tek.com>.  Autopun converts an English phrase into a table
# of phonetically-similar words, useful for creating rebus, punch-lines for
# shaggy-dog stories, and other perversions of spoken English.  For more
# practically-minded folks, autopun includes a text-to-phoneme translator
# (i.e., a text speaker) for English, derived from an earlier posting.
# Caveats: this tool blindly believes that the word list contains all
# interesting words and that everything there is interesting; careful editing
# of the English word list can correct these problems.  It doesn't know how
# to pronounce abbreviations, punctuation, or numerals.

# FIXME:
# - The `I' word is missing from `phones'?
# - `Modula-2' in `dicts' keeps the converter in a loop.
# - Histograms/statistics while converting, eradicate long words.

__metaclass__ = type
import random, sys
import common

class AutoPun(common.Command):
    "pun SENTENCE (phonetic pun)."
    extra_keywords = 'pun'
    burp_weight = 1
    number_arguments = 1

    def split_arguments(self, line):
        return line,

    def handler(self, write, text):
        text = run.produce_some_pun(text)
        if text:
            write(text + '\n')

class Main:
    convert = False
    words = '/usr/share/dict/words'
    word_phone_pairs = None
    phone = None
    squash_table = None

    def __init__(self):
        # Generate phone squash translation table.  Maps a set of
        # similar-sounding phonemes into one.
        before = ''
        after = ''
        for phonemes in (('IY', 'IH',),
                         ('EY', 'EH',),
                         ('AE', 'AA', 'AO', 'OW', 'UH', 'AX', 'AH', 'AW',),
                         ('UW', 'ER',),
                         ('AY',),
                         ('OY',),
                         ('p', 'b',),
                         ('t', 'd',),
                         ('k',),
                         ('g',),
                         ('f', 'v', 'DH',),
                         ('TH',),
                         ('s', 'z', 'SH', 'ZH',),
                         ('HH',),
                         ('m',),
                         ('n', 'NG',),
                         ('l', 'w',),
                         ('y',),
                         ('r',),
                         ('CH', 'j',),
                         ('WH',),
                         (' ',)):
            if len(phonemes) > 1:
                phone = Phonemes.phonemes_to_phone(phonemes)
                before += phone[1:]
                after += phone[0] * (len(phone) - 1)
        import string
        self.squash_table = string.maketrans(before, after)

    def main(self, *arguments):
        import getopt
        options, arguments = getopt.getopt(arguments, 'c')
        for option, value in options:
            if option == '-c':
                self.convert = True
        if self.convert:
            assert len(arguments) <= 1, arguments
            if arguments:
                name = arguments[0]
            else:
                name = '/usr/share/dict/words'
            for line in file(name):
                word = line.rstrip()
                phone = xlate_word(word).translate(self.squash_table)
                sys.stdout.write('%s ' % word)
                sys.stdout.flush()
                sys.stdout.write('%s\n' % phone)
        else:
            assert len(arguments) <= 1, arguments
            if arguments:
                self.load_phones(arguments[0])
            line = sys.stdin.readline()
            while line:
                pun = self.produce_some_pun(line, pairs)
                if pun is None:
                    sys.stdout.write("None found!\n")
                else:
                    sys.stdout.write(pun + "\n")
                line = sys.stdin.readline()

    def produce_some_pun(self, text):
        text_phone = xlate_line(text).translate(self.squash_table)
        # Make AT returns a list of (NEXT, WORD) tuples for a given position
        # in TEXT_PHONE.  Choosing WORD would push position to NEXT.
        at = {}
        avoid_words = set(text.split())
        if self.word_phone_pairs is None:
            self.load_phones()
        for word, phone in self.word_phone_pairs:
            position = text_phone.find(phone)
            if position >= 0 and word not in avoid_words:
                while position >= 0:
                    if position not in at:
                        at[position] = []
                    at[position].append((position + len(phone), word))
                    position = text_phone.find(phone, position + 1)

        def transform(start):
            # Turn AT[START] into a single (WEIGHT, TEXT) tuple and
            # return True, if some solution exists, otherwise delete it and
            # return False.  TEXT is a white-joined string of words covering
            # TEXT_PHONE[START:], randomly chosen over WEIGHT possibilities.
            solutions = []
            total = 0
            for next, word in at[start]:
                if next == len(text_phone):
                    total += 1
                    solutions.append((total, word))
                    continue
                if next not in at:
                    continue
                if not isinstance(at[next], tuple):
                    if not transform(next):
                        continue
                weight, text = at[next]
                total += weight
                solutions.append((total, word + ' ' + text))
            if solutions:
                select = random.randrange(0, total)
                for partial, text in solutions:
                    if select < partial:
                        at[start] = total, text
                        return True
            del at[start]
            return False

        if 0 in at and transform(0):
            return at[0][1]

    def load_phones(self, name=None):
        if name is None:
            name = '%s/phones' % common.datadir
        self.word_phone_pairs = [line.split() for line in file(name)]

# Phonetic tools.

def xlate_line(text):
    # Given an English-text phrase or word, translate that thing into a
    # phoneme-list.
    phone = ''
    word = ''
    for character in text:
        if character.isalpha() or character == '\'':
            word += character
        elif word:
            phone += xlate_word(word)
            word = ''
    if word:
        phone += xlate_word(word)
    return phone

def xlate_word(word):
    # Translate the given English word into a phoneme stream.  The word
    # contains only letters, apostrophes, and hyphens.
    phone = ''
    word = ' ' + word.upper() + ' '
    position = 1
    while position < len(word):
        for rule in Rule.rules_by_first.get(word[position], ()):
            if rule.matches(word, position):
                phone += rule.phone
                position += len(rule.string)
                break
        else:
            # Skip the annoyance.
            position =+ 1
    return phone[:-1]

class Phonemes:
    phoneme_to_character = {}
    character_to_phoneme = {}
    for counter, phoneme in enumerate(('IY',  # bEEt
                                       'IH',  # bIt
                                       'EY',  # gAte
                                       'EH',  # gEt
                                       'AE',  # fAt
                                       'AA',  # fAther
                                       'AO',  # lAWn
                                       'OW',  # lOne
                                       'UH',  # fUll
                                       'UW',  # fOOl
                                       'ER',  # mURdER
                                       'AX',  # About
                                       'AH',  # bUt
                                       'AY',  # hIde
                                       'AW',  # hOW
                                       'OY',  # tOY
                                       'p',   # Pack
                                       'b',   # Back
                                       't',   # Time
                                       'd',   # Dime
                                       'k',   # Coat
                                       'g',   # Goat
                                       'f',   # Fault
                                       'v',   # Vault
                                       'TH',  # eTHer
                                       'DH',  # eiTHer
                                       's',   # Sue
                                       'z',   # Zoo
                                       'SH',  # leaSH
                                       'ZH',  # leiSure
                                       'HH',  # How
                                       'm',   # suM
                                       'n',   # suN
                                       'NG',  # suNG
                                       'l',   # Laugh
                                       'w',   # Wear
                                       'y',   # Young
                                       'r',   # Rate
                                       'CH',  # CHar
                                       'j',   # Jar
                                       'WH',  # WHere
                                       ' ')): # short pause
        character = chr(ord('!') + counter)
        phoneme_to_character[phoneme] = character
        character_to_phoneme[character] = phoneme

    @staticmethod
    def phonemes_to_phone(phonemes):
        return ''.join(map(Phonemes.phoneme_to_character.get, phonemes))

    @staticmethod
    def phone_to_phonemes(string):
        return map(Phonemes.character_to_phoneme.get, string)

class Rule:
    # Special context values:
    #   None - no context requirement
    #   ' '  - context is beginning or end of word
    # Special context characters:
    #   # - One or more vowels
    #   : - Zero or more consonants
    #   ^ - One consonant.
    #   . - One of B, D, V, G, J, L, M, N, R, W or Z (voiced consonants)
    #   % - One of ER, E, ES, ED, ING, ELY (a suffix) (in right context only)
    #   + - One of E, I or Y (a "front" vowel)
    # Phonemes are recoded into a phone string.

    rules_by_first = {}

    def __init__(self, string, prefix, suffix, *phonemes):
        self.string = string
        if isinstance(prefix, str):
            self.prefix = prefix[::-1]
        else:
            self.prefix = prefix
        self.suffix = suffix
        self.phone = Phonemes.phonemes_to_phone(phonemes)
        rules = Rule.rules_by_first.get(string[0])
        if rules is None:
            rules = Rule.rules_by_first[string[0]] = []
        rules.append(self)

    def matches(self, word, position):
        end = position + len(self.string)
        return (word[position:end] == self.string
                and self.leftmatch(word, position - 1)
                and self.rightmatch(word, end))

    def leftmatch(self, word, position):
        pattern = self.prefix
        if pattern is None:
            return True
        for character in pattern:
            if character in '\' ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                if word[position] != character:
                    return False
                position -= 1
            elif character == '#':
                # One or more vowels.
                if not isvowel(word[position]):
                    return False
                position -= 1
                while isvowel(word[position]):
                    position -= 1
            elif character == ':':
                # Zero or more consonants.
                while isconsonant(word[position]):
                    position -= 1
            elif character == '^':
                # One consonant.
                if not isconsonant(word[position]):
                    return False
                position -= 1
            elif character == '.':
                # Voiced consonant.
                if word[position] not in 'BDVGJLMNRWZ':
                    return False
                position -= 1
            elif character == '+':
                # E, I or Y (front vowel).
                if word[position] not in 'EIY':
                    return False
                position -= 1
            else:
                assert False, character
        return True

    def rightmatch(self, word, position):
        pattern = self.suffix
        if pattern is None:
            return True
        for character in pattern:
            if character in '\' ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                if word[position] != character:
                    return False
                position += 1
            elif character == '#':
                # One or more vowels.
                if not isvowel(word[position]):
                    return False
                position += 1
                while isvowel(word[position]):
                    position += 1
            elif character == ':':
                # Zero or more consonants.
                while isconsonant(word[position]):
                    position += 1
            elif character == '^':
                # One consonant.
                if not isconsonant(word[position]):
                    return False
                position += 1
            elif character == '.':
                # Voiced consonant.
                if word[position] not in 'BDVGJLMNRWZ':
                    return False
                position += 1
            elif character == '+':
                # E, I or Y (front vowel).
                if word[position] not in 'EIY':
                    return False
                position += 1
            elif character == '%':
                # ER, E, ES, ED, ING, ELY (a suffix).
                for suffix in 'ED', 'ELY', 'ER', 'ES', 'E', 'ING':
                    if word[position:position+len(suffix)] == suffix:
                        position += len(suffix)
                        break
                else:
                    return False
            else:
                assert False, character
        return True

def isvowel(character):
    return character in 'AEIOU'

def isconsonant(character):
    return character.isupper() and not isvowel(character)

## Phonetic translation table.

# Declarations for phonemic translation derived from: "Automatic translation
# of English text to phonetics by means of letter-to-sound rules", NRL Report
# 7948, 1976-01-21, Naval Research Laboratory, Washington, D.C.  Published by
# the National Technical Information Service as document "AD/A021 929".

Rule(' ', None, None, ' ')
Rule('-', None, None)
Rule('\'S', '.', None, 'z')
Rule('\'S', '#:.E', None, 'z')
Rule('\'S', '#', None, 'z')
Rule('\'', None, None)
Rule(',', None, None, ' ')
Rule('.', None, None, ' ')
Rule('?', None, None, ' ')
Rule('!', None, None, ' ')
Rule('A', None, ' ', 'AX')
Rule('ARE', ' ', ' ', 'AA', 'r')
Rule('AR', ' ', 'O', 'AX', 'r')
Rule('AR', None, '#', 'EH', 'r')
Rule('AS', '^', '#', 'EY', 's')
Rule('A', None, 'WA', 'AX')
Rule('AW', None, None, 'AO')
Rule('ANY', ' :', None, 'EH', 'n', 'IY')
Rule('A', None, '^+#', 'EY')
Rule('ALLY', '#:', None, 'AX', 'l', 'IY')
Rule('AL', ' ', '#', 'AX', 'l')
Rule('AGAIN', None, None, 'AX', 'g', 'EH', 'n')
Rule('AG', '#:', 'E', 'IH', 'j')
Rule('A', None, '^+:#', 'AE')
Rule('A', ' :', '^+ ', 'EY')
Rule('A', None, '^%', 'EY')
Rule('ARR', ' ', None, 'AX', 'r')
Rule('ARR', None, None, 'AE', 'r')
Rule('AR', ' :', ' ', 'AA', 'r')
Rule('AR', None, ' ', 'ER')
Rule('AR', None, None, 'AA', 'r')
Rule('AIR', None, None, 'EH', 'r')
Rule('AI', None, None, 'EY')
Rule('AY', None, None, 'EY')
Rule('AU', None, None, 'AO')
Rule('AL', '#:', ' ', 'AX', 'l')
Rule('ALS', '#:', ' ', 'AX', 'l', 'z')
Rule('ALK', None, None, 'AO', 'k')
Rule('AL', None, '^', 'AO', 'l')
Rule('ABLE', ' :', None, 'EY', 'b', 'AX', 'l')
Rule('ABLE', None, None, 'AX', 'b', 'AX', 'l')
Rule('ANG', None, '+', 'EY', 'n', 'j')
Rule('A', None, None, 'AE')
Rule('BE', ' ', '^#', 'b', 'IH')
Rule('BEING', None, None, 'b', 'IY', 'IH', 'NG')
Rule('BOTH', ' ', ' ', 'b', 'OW', 'TH')
Rule('BUS', ' ', '#', 'b', 'IH', 'z')
Rule('BUIL', None, None, 'b', 'IH', 'l')
Rule('B', None, None, 'b')
Rule('CH', ' ', '^', 'k')
Rule('CH', '^E', None, 'k')
Rule('CH', None, None, 'CH')
Rule('CI', ' S', '#', 's', 'AY')
Rule('CI', None, 'A', 'SH')
Rule('CI', None, 'O', 'SH')
Rule('CI', None, 'EN', 'SH')
Rule('C', None, '+', 's')
Rule('CK', None, None, 'k')
Rule('COM', None, '%', 'k', 'AH', 'm')
Rule('C', None, None, 'k')
Rule('DED', '#:', ' ', 'd', 'IH', 'd')
Rule('D', '.E', ' ', 'd')
Rule('D', '#:^E', ' ', 't')
Rule('DE', ' ', '^#', 'd', 'IH')
Rule('DO', ' ', ' ', 'd', 'UW')
Rule('DOES', ' ', None, 'd', 'AH', 'z')
Rule('DOING', ' ', None, 'd', 'UW', 'IH', 'NG')
Rule('DOW', ' ', None, 'd', 'AW')
Rule('DU', None, 'A', 'j', 'UW')
Rule('D', None, None, 'd')
Rule('E', '#:', ' ')
Rule('E', '\':^', ' ')
Rule('E', ' :', ' ', 'IY')
Rule('ED', '#', ' ', 'd')
Rule('E', '#:', 'D ')
Rule('EV', None, 'ER', 'EH', 'v')
Rule('E', None, '^%', 'IY')
Rule('ERI', None, '#', 'IY', 'r', 'IY')
Rule('ERI', None, None, 'EH', 'r', 'IH')
Rule('ER', '#:', '#', 'ER')
Rule('ER', None, '#', 'EH', 'r')
Rule('ER', None, None, 'ER')
Rule('EVEN', ' ', None, 'IY', 'v', 'EH', 'n')
Rule('E', '#:', 'W')
Rule('EW', 'T', None, 'UW')
Rule('EW', 'S', None, 'UW')
Rule('EW', 'R', None, 'UW')
Rule('EW', 'D', None, 'UW')
Rule('EW', 'L', None, 'UW')
Rule('EW', 'Z', None, 'UW')
Rule('EW', 'N', None, 'UW')
Rule('EW', 'J', None, 'UW')
Rule('EW', 'TH', None, 'UW')
Rule('EW', 'CH', None, 'UW')
Rule('EW', 'SH', None, 'UW')
Rule('EW', None, None, 'y', 'UW')
Rule('E', None, 'O', 'IY')
Rule('ES', '#:S', ' ', 'IH', 'z')
Rule('ES', '#:C', ' ', 'IH', 'z')
Rule('ES', '#:G', ' ', 'IH', 'z')
Rule('ES', '#:Z', ' ', 'IH', 'z')
Rule('ES', '#:X', ' ', 'IH', 'z')
Rule('ES', '#:J', ' ', 'IH', 'z')
Rule('ES', '#:CH', ' ', 'IH', 'z')
Rule('ES', '#:SH', ' ', 'IH', 'z')
Rule('E', '#:', 'S ')
Rule('ELY', '#:', ' ', 'l', 'IY')
Rule('EMENT', '#:', None, 'm', 'EH', 'n', 't')
Rule('EFUL', None, None, 'f', 'UH', 'l')
Rule('EE', None, None, 'IY')
Rule('EARN', None, None, 'ER', 'n')
Rule('EAR', ' ', '^', 'ER')
Rule('EAD', None, None, 'EH', 'd')
Rule('EA', '#:', ' ', 'IY', 'AX')
Rule('EA', None, 'SU', 'EH')
Rule('EA', None, None, 'IY')
Rule('EIGH', None, None, 'EY')
Rule('EI', None, None, 'IY')
Rule('EYE', ' ', None, 'AY')
Rule('EY', None, None, 'IY')
Rule('EU', None, None, 'y', 'UW')
Rule('E', None, None, 'EH')
Rule('FUL', None, None, 'f', 'UH', 'l')
Rule('F', None, None, 'f')
Rule('GIV', None, None, 'g', 'IH', 'v')
Rule('G', ' ', 'I^', 'g')
Rule('GE', None, 'T', 'g', 'EH')
Rule('GGES', 'SU', None, 'g', 'j', 'EH', 's')
Rule('GG', None, None, 'g')
Rule('G', ' B#', None, 'g')
Rule('G', None, '+', 'j')
Rule('GREAT', None, None, 'g', 'r', 'EY', 't')
Rule('GH', '#', None)
Rule('G', None, None, 'g')
Rule('HAV', ' ', None, 'HH', 'AE', 'v')
Rule('HERE', ' ', None, 'HH', 'IY', 'r')
Rule('HOUR', ' ', None, 'AW', 'ER')
Rule('HOW', None, None, 'HH', 'AW')
Rule('H', None, '#', 'HH')
Rule('H', None, None)
Rule('IN', ' ', None, 'IH', 'n')
Rule('I', ' ', ' ', 'AY')
Rule('IN', None, 'D', 'AY', 'n')
Rule('IER', None, None, 'IY', 'ER')
Rule('IED', '#:R', None, 'IY', 'd')
Rule('IED', None, ' ', 'AY', 'd')
Rule('IEN', None, None, 'IY', 'EH', 'n')
Rule('IE', None, 'T', 'AY', 'EH')
Rule('I', ' :', '%', 'AY')
Rule('I', None, '%', 'IY')
Rule('IE', None, None, 'IY')
Rule('I', None, '^+:#', 'IH')
Rule('IR', None, '#', 'AY', 'r')
Rule('IZ', None, '%', 'AY', 'z')
Rule('IS', None, '%', 'AY', 'z')
Rule('I', None, 'D%', 'AY')
Rule('I', '+^', '^+', 'IH')
Rule('I', None, 'T%', 'AY')
Rule('I', '#:^', '^+', 'IH')
Rule('I', None, '^+', 'AY')
Rule('IR', None, None, 'ER')
Rule('IGH', None, None, 'AY')
Rule('ILD', None, None, 'AY', 'l', 'd')
Rule('IGN', None, ' ', 'AY', 'n')
Rule('IGN', None, '^', 'AY', 'n')
Rule('IGN', None, '%', 'AY', 'n')
Rule('IQUE', None, None, 'IY', 'k')
Rule('I', None, None, 'IH')
Rule('J', None, None, 'j')
Rule('K', ' ', 'N')
Rule('K', None, None, 'k')
Rule('LO', None, 'C#', 'l', 'OW')
Rule('L', 'L', None)
Rule('L', '#:^', '%', 'AX', 'l')
Rule('LEAD', None, None, 'l', 'IY', 'd')
Rule('L', None, None, 'l')
Rule('MOV', None, None, 'm', 'UW', 'v')
Rule('M', None, None, 'm')
Rule('NG', 'E', '+', 'n', 'j')
Rule('NG', None, 'R', 'NG', 'g')
Rule('NG', None, '#', 'NG', 'g')
Rule('NGL', None, '%', 'NG', 'g', 'AX', 'l')
Rule('NG', None, None, 'NG')
Rule('NK', None, None, 'NG', 'k')
Rule('NOW', ' ', ' ', 'n', 'AW')
Rule('N', None, None, 'n')
Rule('OF', None, ' ', 'AX', 'v')
Rule('OROUGH', None, None, 'ER', 'OW')
Rule('OR', '#:', ' ', 'ER')
Rule('ORS', '#:', ' ', 'ER', 'z')
Rule('OR', None, None, 'AO', 'r')
Rule('ONE', ' ', None, 'w', 'AH', 'n')
Rule('OW', None, None, 'OW')
Rule('OVER', ' ', None, 'OW', 'v', 'ER')
Rule('OV', None, None, 'AH', 'v')
Rule('O', None, '^%', 'OW')
Rule('O', None, '^EN', 'OW')
Rule('O', None, '^I#', 'OW')
Rule('OL', None, 'D', 'OW', 'l')
Rule('OUGHT', None, None, 'AO', 't')
Rule('OUGH', None, None, 'AH', 'f')
Rule('OU', ' ', None, 'AW')
Rule('OU', 'H', 'S#', 'AW')
Rule('OUS', None, None, 'AX', 's')
Rule('OUR', None, None, 'AO', 'r')
Rule('OULD', None, None, 'UH', 'd')
Rule('OU', '^', '^L', 'AH')
Rule('OUP', None, None, 'UW', 'p')
Rule('OU', None, None, 'AW')
Rule('OY', None, None, 'OY')
Rule('OING', None, None, 'OW', 'IH', 'NG')
Rule('OI', None, None, 'OY')
Rule('OOR', None, None, 'AO', 'r')
Rule('OOK', None, None, 'UH', 'k')
Rule('OOD', None, None, 'UH', 'd')
Rule('OO', None, None, 'UW')
Rule('O', None, 'E', 'OW')
Rule('O', None, ' ', 'OW')
Rule('OA', None, None, 'OW')
Rule('ONLY', ' ', None, 'OW', 'n', 'l', 'IY')
Rule('ONCE', ' ', None, 'w', 'AH', 'n', 's')
Rule('ON\'T', None, None, 'OW', 'n', 't')
Rule('O', 'C', 'N', 'AA')
Rule('O', None, 'NG', 'AO')
Rule('O', ' :^', 'N', 'AH')
Rule('ON', 'I', None, 'AX', 'n')
Rule('ON', '#:', ' ', 'AX', 'n')
Rule('ON', '#^', None, 'AX', 'n')
Rule('O', None, 'ST ', 'OW')
Rule('OF', None, '^', 'AO', 'f')
Rule('OTHER', None, None, 'AH', 'DH', 'ER')
Rule('OSS', None, ' ', 'AO', 's')
Rule('OM', '#:^', None, 'AH', 'm')
Rule('O', None, None, 'AA')
Rule('PH', None, None, 'f')
Rule('PEOP', None, None, 'p', 'IY', 'p')
Rule('POW', None, None, 'p', 'AW')
Rule('PUT', None, ' ', 'p', 'UH', 't')
Rule('P', None, None, 'p')
Rule('QUAR', None, None, 'k', 'w', 'AO', 'r')
Rule('QU', None, None, 'k', 'w')
Rule('Q', None, None, 'k')
Rule('RE', ' ', '^#', 'r', 'IY')
Rule('R', None, None, 'r')
Rule('SH', None, None, 'SH')
Rule('SION', '#', None, 'ZH', 'AX', 'n')
Rule('SOME', None, None, 's', 'AH', 'm')
Rule('SUR', '#', '#', 'ZH', 'ER')
Rule('SUR', None, '#', 'SH', 'ER')
Rule('SU', '#', '#', 'ZH', 'UW')
Rule('SSU', '#', '#', 'SH', 'UW')
Rule('SED', '#', ' ', 'z', 'd')
Rule('S', '#', '#', 'z')
Rule('SAID', None, None, 's', 'EH', 'd')
Rule('SION', '^', None, 'SH', 'AX', 'n')
Rule('S', None, 'S')
Rule('S', '.', ' ', 'z')
Rule('S', '#:.E', ' ', 'z')
Rule('S', '#:^##', ' ', 'z')
Rule('S', '#:^#', ' ', 's')
Rule('S', 'U', ' ', 's')
Rule('S', ' :#', ' ', 'z')
Rule('SCH', ' ', None, 's', 'k')
Rule('S', None, 'C+')
Rule('SM', '#', None, 'z', 'm')
Rule('SN', '#', '\'', 'z', 'AX', 'n')
Rule('S', None, None, 's')
Rule('THE', ' ', ' ', 'DH', 'AX')
Rule('TO', None, ' ', 't', 'UW')
Rule('THAT', None, ' ', 'DH', 'AE', 't')
Rule('THIS', ' ', ' ', 'DH', 'IH', 's')
Rule('THEY', ' ', None, 'DH', 'EY')
Rule('THERE', ' ', None, 'DH', 'EH', 'r')
Rule('THER', None, None, 'DH', 'ER')
Rule('THEIR', None, None, 'DH', 'EH', 'r')
Rule('THAN', ' ', ' ', 'DH', 'AE', 'n')
Rule('THEM', ' ', ' ', 'DH', 'EH', 'm')
Rule('THESE', None, ' ', 'DH', 'IY', 'z')
Rule('THEN', ' ', None, 'DH', 'EH', 'n')
Rule('THROUGH', None, None, 'TH', 'r', 'UW')
Rule('THOSE', None, None, 'DH', 'OW', 'z')
Rule('THOUGH', None, ' ', 'DH', 'OW')
Rule('THUS', ' ', None, 'DH', 'AH', 's')
Rule('TH', None, None, 'TH')
Rule('TED', '#:', ' ', 't', 'IH', 'd')
Rule('TI', 'S', '#N', 'CH')
Rule('TI', None, 'O', 'SH')
Rule('TI', None, 'A', 'SH')
Rule('TIEN', None, None, 'SH', 'AX', 'n')
Rule('TUR', None, '#', 'CH', 'ER')
Rule('TU', None, 'A', 'CH', 'UW')
Rule('TWO', ' ', None, 't', 'UW')
Rule('T', None, None, 't')
Rule('UN', ' ', 'I', 'y', 'UW', 'n')
Rule('UN', ' ', None, 'AH', 'n')
Rule('UPON', ' ', None, 'AX', 'p', 'AO', 'n')
Rule('UR', 'T', '#', 'UH', 'r')
Rule('UR', 'S', '#', 'UH', 'r')
Rule('UR', 'R', '#', 'UH', 'r')
Rule('UR', 'D', '#', 'UH', 'r')
Rule('UR', 'L', '#', 'UH', 'r')
Rule('UR', 'Z', '#', 'UH', 'r')
Rule('UR', 'N', '#', 'UH', 'r')
Rule('UR', 'J', '#', 'UH', 'r')
Rule('UR', 'TH', '#', 'UH', 'r')
Rule('UR', 'CH', '#', 'UH', 'r')
Rule('UR', 'SH', '#', 'UH', 'r')
Rule('UR', None, '#', 'y', 'UH', 'r')
Rule('UR', None, None, 'ER')
Rule('U', None, '^ ', 'AH')
Rule('U', None, '^^', 'AH')
Rule('UY', None, None, 'AY')
Rule('U', ' G', '#')
Rule('U', 'G', '%')
Rule('U', 'G', '#', 'w')
Rule('U', '#N', None, 'y', 'UW')
Rule('U', 'T', None, 'UW')
Rule('U', 'S', None, 'UW')
Rule('U', 'R', None, 'UW')
Rule('U', 'D', None, 'UW')
Rule('U', 'L', None, 'UW')
Rule('U', 'Z', None, 'UW')
Rule('U', 'N', None, 'UW')
Rule('U', 'J', None, 'UW')
Rule('U', 'TH', None, 'UW')
Rule('U', 'CH', None, 'UW')
Rule('U', 'SH', None, 'UW')
Rule('U', None, None, 'y', 'UW')
Rule('VIEW', None, None, 'v', 'y', 'UW')
Rule('V', None, None, 'v')
Rule('WERE', ' ', None, 'w', 'ER')
Rule('WA', None, 'S', 'w', 'AA')
Rule('WA', None, 'T', 'w', 'AA')
Rule('WHERE', None, None, 'WH', 'EH', 'r')
Rule('WHAT', None, None, 'WH', 'AA', 't')
Rule('WHOL', None, None, 'HH', 'OW', 'l')
Rule('WHO', None, None, 'HH', 'UW')
Rule('WH', None, None, 'WH')
Rule('WAR', None, None, 'w', 'AO', 'r')
Rule('WOR', None, '^', 'w', 'ER')
Rule('WR', None, None, 'r')
Rule('W', None, None, 'w')
Rule('X', None, None, 'k', 's')
Rule('YOUNG', None, None, 'y', 'AH', 'NG')
Rule('YOU', ' ', None, 'y', 'UW')
Rule('YES', ' ', None, 'y', 'EH', 's')
Rule('Y', ' ', None, 'y')
Rule('Y', '#:^', ' ', 'IY')
Rule('Y', '#:^', 'I', 'IY')
Rule('Y', ' :', ' ', 'AY')
Rule('Y', ' :', '#', 'AY')
Rule('Y', ' :', '^+:#', 'IH')
Rule('Y', ' :', '^#', 'AY')
Rule('Y', None, None, 'IH')
Rule('Z', None, None, 'z')

run = Main()
main = run.main

if __name__ == '__main__':
    main(*sys.argv[1:])
