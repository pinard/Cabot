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
Entertaining commands.
"""

__metaclass__ = type
import common
Command = common.Command

# Various noise or burp ideas, none important.
# - eliza

## Standard commands.

class Help(Command):
    """\
cabot (for icule and his friends, inspired by deego's impressive fsbot).
/m cabot COMMAND; cabot: COMMAND; ,COMMAND;  ... ,,COMMAND (execute COMMAND).
WORD? (resolve WORD).
"""
    extra_keywords = 'h', '?'

    def handler(self, write, *arguments):
        for text in Command.doc_strings:
            for line in text.splitlines():
                line = line.rstrip()
                if line and line[-1] in '.!?':
                    write(line + '  ')
                else:
                    write(line + ' ')
        write('\n')

class More(Command):
    "more (10 more lines)."

    def handler(self, write, *arguments):
        server = common.server
        if server.target in server.queues:
            server.queues[server.target].allow_more()
            if selver.target not in server.targets:
                server.targets.insert(0, server.target)

class Error(Command):
    # Turn a message into an error.

    number_arguments = 0, 1

    def __init__(self):
        handler = Command.error_handler
        assert handler is None, handler
        Command.error_handler = self.handler

    def split_arguments(self, line):
        if line:
            return line,
        return ()

    def handler(self, write, *arguments):
        if arguments and arguments[0]:
            format = common.choice(
                'Doh.  %s',
                '... %s',
                )
            write(format % arguments[0] + '\n')
        else:
            write(common.choice('... huh?'))

## Tiny chats.

class Hello(Command):
    extra_keywords = 'greet', 'hey', 'hi'
    number_arguments = 0, None

    def handler(self, write, *arguments):
        write("hi %s !!\n" % common.server.source)

class Kiss(Command):
    number_arguments = 0, None

    def handler(self, write, *arguments):
        write("/me kisses %s\n" % common.server.source)

class Fuck(Command):
    number_arguments = 0, None

    def handler(self, write, *arguments):
        write("/me goes with %s into a private place..." % common.server.source)

class Kill(Command):
    number_arguments = 0, None

    def handler(self, write, *arguments):
        write("/me, trained by apt, chops %s into half with an AOL CD\n"
              % common.server.source)

class Bye(Command):
    number_arguments = 0, None

    def handler(self, write, *arguments):
        write(common.choice(
            "Okay, see you later",
            "later",
            "Bye then",
            "Take care now",
            "Happy hacking",
            ))

## French dictionary commands.

class Dmf(Command):
    """\
dmf WORD (French radices).
"""
    burp_weight = 10
    encoding = 'ISO-8859-1'
    number_arguments = 1

    def handler(self, write, mot):
        try:
            mot = mot.encode(Dmf.encoding)
        except UnicodeEncodeError:
            return
        try:
            from Dmf import dmf
        except ImportError:
            write("DMF is not available")
        db = dmf.Fichier()
        articles = list(db.fouiller(mot))
        for counter, article in enumerate(articles):
            if len(articles) != 1:
                write('[%d] ' % counter)
            write(article.graphie.decode(Dmf.encoding))
            keys = article.keys()
            for key, butnot in ((u'Catég', ()),
                                ('Temps', ()),
                                ('Perso', ()),
                                ('Genre', ('genI',)),
                                ('Nombr', ('nomI',)),
                                ):
                key = key.encode(Dmf.encoding)
                if key in keys:
                    value = getattr(article, key).decode(Dmf.encoding)
                    if value not in butnot:
                        write(' %s' % value)
            write('\n')

# FIXME: Last resort burp.  Keep it last, as it always succeed.

class Burp(Command):
    burp_weight = 10000
    number_arguments = 0, None

    def handler(self, write, *arguments):
        raise common.Error('')
