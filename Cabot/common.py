# -*- coding: UTF-8 -*-

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
Common code for Cabot.
"""

__metaclass__ = type
import random, time

datadir = '/home/pinard/net/cabot/database'

# SERVER is set, within `cabot.py', to the single Server instance.
server = None

class Error(Exception):
    pass

## Basic command processing.

class NoCommand:
    # Derive from NoCommand instead of Command to easily comment out a command.
    pass

class Command:
    # All command doc-strings, for producing help output.
    doc_strings = []
    # Command indexed by keywords.
    registry = {}
    # Matchers trying to decipher a line into a command.
    matchers = []
    # (PARTIAL_WEIGHT, HANDLER) pairs for commands having a BURP_WEIGHT.
    burps = []
    # Handler encapsulating an exception text into an error message.
    error_handler = None

    class __metaclass__(type):

        def __new__(cls, name, bases, dict):
            self = type.__new__(cls, name, bases, dict)
            if hasattr(self, 'handler'):
                if self.__doc__ is not None:
                    Command.doc_strings.append(self.__doc__)
                keywords = [name.lower()]
                if hasattr(self, 'extra_keywords'):
                    if isinstance(self.extra_keywords, str):
                        keywords.append(self.extra_keywords)
                    else:
                        keywords += list(self.extra_keywords)
                command = self()
                for keyword in keywords:
                    assert keyword not in Command.registry, keyword
                    Command.registry[keyword] = command
                if hasattr(command, 'matcher'):
                    Command.matchers.append(command.matcher)
                if hasattr(command, 'burp_weight'):
                    if Command.burps:
                        burp_weight = Command.burps[-1][0]
                    else:
                        burp_weight = 0
                    burp_weight += command.burp_weight
                    Command.burps.append((burp_weight, command.handler))
            return self

    def split_arguments(self, line):
        return line.split()

    number_arguments = 0

    def check_number_arguments(self, arguments):
        number = len(arguments)
        if isinstance(self.number_arguments, tuple):
            lower, higher = self.number_arguments
        else:
            lower = higher = self.number_arguments
        if number < lower or higher is not None and number > higher:
            if lower == higher:
                if lower == 0:
                    diagnostic = "does not have arguments"
                elif lower == 1:
                    diagnostic = "expects one argument"
                else:
                    diagnostic = "expects %d arguments" % lower
            elif higher is None:
                if lower == 1:
                    diagnostic = "should have at least one argument"
                else:
                    diagnostic = "expects at least %d arguments" % lower
            elif lower == 0:
                if higher == 1:
                    diagnostic = "accepts one optional argument at most"
                else:
                    diagnostic = ("should not have more than %d arguments"
                                  % higher)
            else:
                diagnostic = ("expects between %d and %d arguments"
                              % (lower, higher))
            raise Error("%s %s." % (type(self).__name__.lower(), diagnostic))

## Cabot log files.

class Log:
    encoding = 'UTF-8'

    def __init__(self, text=None, mode='a'):
        self.log = file('%s/log' % datadir, mode)
        if text is not None:
            self.write(text.encode(Log.encoding))

    def __getattr__(self, attribute):
        return getattr(self.log, attribute)

    def write(self, text):
        self.log.write(text.encode(Log.encoding))
        self.log.flush()

## Miscellaneous services.

def choice(*arguments):
    total = 0
    weight = 1
    pairs = []
    for argument in arguments:
        if isinstance(argument, int):
            weight = argument
        else:
            total += weight
            weight = 1
            pairs.append((total, argument))
    cut = random.randrange(0, total)
    for partial, text in pairs:
        if cut < partial:
            return text

def timestamp():
    y, mo, d, h, mi, s = time.localtime()[:6]
    y -= 2000
    return '%.2d%.2d%.2d%.2d%.2d%.2d' % (y, mo, d, h, mi, s)
