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
Handle Cabot databases and logs.
"""

# Each database entry relates a key to a value, or more precisely a
# `KEY\0STAMP' to a `SOURCE\0VALUE'.  Users see only WORD and VALUE.  STAMP is
# `YYMMDDhhmmss' and is used to order duplicate entries.  SOURCE is either a
# nickname or by convention, a '@' followed by a keyword indicating another
# type of source.

# `\0DSTAMP' for a key signals a deleted entry, DSTAMP tells delete time.
# The value is `DSOURCE\0KEY\0STAMP\0SOURCE\0VALUE', where DSOURCE is the
# deleter, and the remaining fields describe the deleted key and value.

# Currently, each group of consecutive records having the same KEY within
# `KEY\0STAMP' are preceded by a record having `KEY' for a key and '' for
# a value.  This record might disappear in some future.

__metaclass__ = type
import bsddb, re, sys
import common

file_encoding = 'UTF-8'
NUL = '\0'

## Utility programs.

def dump_database():
    db = Unicode_database('r')
    for key, value in db:
        sys.stdout.write('%s\t%s\n' % (key, value))
    db.close()

def undump_database():
    db = Unicode_database('c')
    for line in sys.stdin:
        line = line.decode(file_encoding)
        key, value = line.split('\t')
        db[key] = value.rstrip()
    db.close()

def load_entries(source):
    pairs = []
    for line in sys.stdin:
        line = line.decode(file_encoding)
        key, value = line.split(None, 1)
        pairs.append((key, value.rstrip()))
    db = Unicode_database('c')
    db.add_entries(souce, pairs)
    db.close()

def erase_entries(source):
    db = Unicode_database('w')
    db.delete_entries(source)
    db.close()

## Database commands.

class Close(common.Command):
    # CLOSE database - useful to force a re-read after an external update.
    number_arguments = 1

    def handler(self, write, word):
        if word == 'database':
            database.close()

class Search(common.Command):
    "KEY (search)."
    extra_keywords = 'find',
    number_arguments = 1

    def matcher(self, write, line):
        arguments = line.split()
        if len(arguments) == 1:
            self.handler(write, arguments[0])

    def handler(self, write, key):
        pairs = list(database.getall(key))
        if pairs:
            key, value = pairs[0]
            if len(pairs) == 1 and value[0].isupper():
                write('%s.\n' % value)
            else:
                format = common.choice(
                    "%s is perhaps",
                    "%s is, like,",
                    "I heard %s is",
                    "It's been said %s may be",
                    "I am told %s is",
                    "Might %s be",
                    "I think %s is",
                    "%s may be",
                    "Perhaps, %s is",
                    "%s is",
                    "Some say %s is",
                    "%s:",
                    "hmm.. %s is",
                    "Our records indicate that %s is",
                    "Humans tell me %s is",
                    )
                if len(pairs) == 1:
                    write('%s %s.\n' % (format % key, value))
                else:
                    prefix = format % key + ' '
                    for counter, (key, value) in enumerate(pairs):
                        separator = ';.'[counter == len(pairs) - 1]
                        write('%s[%d] %s%s\n'
                              % (prefix, counter, value, separator))
                        prefix = ''
        else:
            keys = database.resolve(key)
            if keys:
                write(' '.join(keys) + '\n')
            else:
                raise common.Error("But there's no such record: %s" % key)

class Also(common.Command):
    # For concision, this doc-string is held by Learn only.
    number_arguments = 2

    def matcher(self, write, line):
        line = ' '.join(line.split())
        for separator in (' is also ', 'is also,', ' are also ',
                          ' are also,', 'also are '):
            if separator in line:
                key, value = line.split(separator, 1)
                if key.count(' ') < 2:
                    self.handler(write, key, value)
                    return

    def handler(self, write, key, value):
        if not database.has_key(key):
            raise common.Error("%s unknown" % key)
        database.add(key, value)
        write("  (%s added)\n" % key)

class Learn(common.Command):
    "KEY is [also] DEF (learn)."
    number_arguments = 2

    def matcher(self, write, line):
        line = ' '.join(line.split())
        # The `also' case does not need to be checked here, as Learn appears
        # only after Also in the Command.matchers list.
        for separator in ' is ', ' are ':
            if separator in line:
                key, value = line.split(separator, 1)
                if key.count(' ') < 2:
                    self.handler(write, key, value)
                    return

    def handler(self, write, key, value):
        if database.has_key(key):
            raise common.Error("%s already known" % key)
        database.add(key, value)
        reply = common.choice("  (%s learnt)" % key,
                              "created.")
        write('%s\n' % reply)

class Unlearn(common.Command):
    "forget KEY [N[-M]]|[all] (unlearn)."
    extra_keywords = 'del', 'delete', 'forget'
    number_arguments = 2, 3

    def split_arguments(self, line):
        line = ' '.join(line.split())
        match = re.match('(.*) ([0-9]+) ?- ?([0-9]+)$', line)
        if match:
            first = int(match.group(2))
            last = int(match.group(3))
            if last < first:
                raise common.Error("%d-%d is not a valid range" % (first, last))
            key = match.group(1).strip()
            which = first, last
        else:
            match = re.match('(.*) ([0-9]+)$', line)
            if match:
                key = match.group(1).strip()
                which = int(match.group(2))
            else:
                match = re.match('(.*) all$', line)
                if match:
                    key = match.group(1).strip()
                    which = True
                else:
                    key = line
                    which = None
        if key.count(' ') >= 2:
            raise common.Error("more than two words in the key")
        return key, which

    def handler(self, write, key, which):
        count = database.delete(key, which)
        if count == 0:
            common.Error("Nothing deleted.")
        elif count == 1:
            write("%s entry deleted.\n" % key)
        else:
            write("I deleted %d entries for %s.\n" % (count, key))

## Database handling.

class Database:
    def __init__(self):
        self.db = None
        self.word_to_keys = None

    def __iter__(self):
        if self.db is None:
            self.open()
        items = self.word_to_keys.items()
        items.sort()
        for word, keys in items:
            results = []
            for key in keys:
                for result in self.db.get_entries(key):
                    results.append(result)
            results.sort()
            for stamp, source, key, value in results:
                yield key, value

    def has_key(self, key):
        if self.db is None:
            self.open()
        return self.canonical_key(key) in self.word_to_keys

    def resolve(self, pattern):
        if self.db is None:
            self.open()
        pattern = self.canonical_key(pattern)
        results = []
        for word, keys in self.word_to_keys.iteritems():
            if pattern in word:
                results.append(keys[0])
        return results

    def getall(self, key):
        if self.db is None:
            self.open()
        results = []
        for key in self.word_to_keys.get(self.canonical_key(key), []):
            for result in self.db.get_entries(key):
                results.append(result)
        results.sort()
        for stamp, source, key, value in results:
            yield key, value

    def add(self, key, value):
        if self.db is None:
            self.open()
        self.db.add_entry(common.server.source, key, value)
        word = self.canonical_key(key)
        keys = self.word_to_keys.get(word)
        if keys is None:
            keys = self.word_to_keys[word] = []
        if key not in keys:
            keys.append(key)
            keys.sort()

    def delete(self, key, which):
        # WHICH is either a True for all, None for the only entry, a number
        # INDEX for that single entry index, or else, a tuple (FIRST, LAST)
        # for the first and last entry index (included) to be deleted.
        if self.db is None:
            self.open()
        # Establish RESULTS in listing order, so WHICH are meaningful.
        word = self.canonical_key(key)
        if word not in self.word_to_keys:
            raise common.Error("%s is not known" % key)
        keys = self.word_to_keys.get(word)
        results = []
        for key in keys:
            for result in self.db.get_entries(key):
                results.append(result)
        results.sort()
        if which is None:
            if len(results) > 1:
                raise common.Error("%d entries, need to say which..."
                                   % len(results))
            indices = [0]
        elif which is True:
            indices = range(len(results))
        elif isinstance(which, int):
            if which >= len(results):
                raise common.Error("%d is not valid index, %d is maximum"
                                   % (which, len(results) - 1))
            indices = [which]
        else:
            if which[1] >= len(results):
                raise common.Error("%d is not valid index, %d is maximum"
                                   % (which[1], len(results) - 1))
            indices = range(which[0], which[1] + 1)
        # Add "deleted" entries, so deletions leave a trace.
        pairs = []
        for index in indices:
            stamp, source, key, value = results[index]
            pairs.append(('', NUL.join([key, stamp, source, value])))
        self.db.add_entries(common.server.source, pairs)
        # Do the actual deletions, cleaning up WORD_TO_KEYS as we go.
        for index in indices:
            stamp, source, key, value = results[index]
            if self.db.delete_entry(key, stamp):
                keys.remove(key)
                if not keys:
                    del self.word_to_keys[word]
        # Return the number of deleted entries.
        return len(indices)

    def open(self):
        self.db = Unicode_database('w')
        self.word_to_keys = {}
        for key, value in self.db:
            if NUL not in key:
                word = self.canonical_key(key)
                if word not in self.word_to_keys:
                    self.word_to_keys[word] = []
                self.word_to_keys[word].append(key)
        if '' in self.word_to_keys:
            del self.word_to_keys['']

    def close(self):
        self.db.close()
        self.db = None

    def canonical_key(self, key):
        return key.replace(' ', '').replace('-', '').lower()

database = Database()

class Unicode_database:
    def __init__(self, mode):
        self.db = bsddb.btopen('%s/db' % common.datadir, mode)

    def __getattr__(self, attribute):
        return getattr(self.db, attribute)

    def __delitem__(self, key):
        del self.db[key.encode(file_encoding)]

    def __getitem__(self, key):
        return self.db[key.encode(file_encoding)].decode(file_encoding)

    def __setitem__(self, key, value):
        self.db[key.encode(file_encoding)] = value.encode(file_encoding)

    def __iter__(self):
        try:
            key, value = self.first()
            while True:
                yield key, value
                key, value = self.next()
        except bsddb.error:
            pass

    def has_key(self, key):
        return self.db.has_key(key.encode(file_encoding))

    def first(self):
        key, value = self.db.first()
        return key.decode(file_encoding), value.decode(file_encoding)

    def next(self):
        key, value = self.db.next()
        try:
            return key.decode(file_encoding), value.decode(file_encoding)
        except UnicodeDecodeError:
            return key.decode('ISO-8859-1'), value.decode('ISO-8859-1')

    def get_entries(self, goal_key):
        encoded_key = goal_key.encode(file_encoding)
        self.db.set_location(encoded_key)
        try:
            full_key, full_value = self.next()
            assert NUL in full_key, full_key
            key, stamp = full_key.split(NUL)
            while key == goal_key:
                source, value = full_value.split(NUL, 1)
                yield stamp, source, key, value
                full_key, full_value = self.next()
                if NUL not in full_key:
                    break
                key, stamp = full_key.split(NUL)
        except bsddb.error:
            pass

    def add_entries(self, source, pairs):
        if len(pairs) == 1:
            self.add_entry(source, *pairs[0])
        else:
            pairs.sort()
            previous_key = None
            stamp = common.timestamp()
            width = len(str(len(pairs)))
            for counter, (key, value) in enumerate(pairs):
                if key != previous_key:
                    self.db[key] = ''
                    previous_key = key
                self[key + NUL + stamp + '%.*d' % (width, counter)] = (
                    source + NUL + value)
            self.db.sync()

    def add_entry(self, source, key, value):
        self[key] = ''
        self[key + NUL + common.timestamp()] = source + NUL + value
        self.db.sync()

    def delete_entries(self, source_to_erase):
        deletes = set()
        current_key = None
        count = 0
        for full_key, full_value in self:
            if NUL in full_key:
                key, stamp = full_key.split(NUL)
                if key != current_key:
                    if current_key is not None and count == 0:
                        deletes.add(current_key)
                    current_key = None
                    count = 0
                source, value = full_value.split(NUL, 1)
                if source == source_to_erase:
                    deletes.add(full_key)
                else:
                    count += 1
            else:
                if current_key is not None and count == 0:
                    deletes.add(current_key)
                current_key = key
                count = 0
        if current_key is not None and count == 0:
            deletes.add(current_key)
        if deletes:
            for key in deletes:
                del self[key]
            self.db.sync()

    def delete_entry(self, goal_key, goal_stamp):
        encoded_key = goal_key.encode(file_encoding)
        encoded_stamp = goal_stamp.encode(file_encoding)
        self.db.set_location(encoded_key)
        found = False
        counter = 0
        try:
            full_key, full_value = self.next()
            assert NUL in full_key, full_key
            key, stamp = full_key.split(NUL)
            while key == goal_key:
                if stamp == goal_stamp:
                    found = True
                else:
                    counter += 1
                full_key, full_value = self.next()
                if NUL not in full_key:
                    break
                key, stamp = full_key.split(NUL)
        except bsddb.error:
            pass
        if found:
            del self.db[encoded_key + NUL + encoded_stamp]
        # Return True only when the last entry is being deleted.
        if counter:
            self.db.sync()
            return False
        del self.db[encoded_key]
        self.db.sync()
        return True
