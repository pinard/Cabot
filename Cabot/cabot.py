#! /usr/bin/env python
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
IRC bot for `icule'.

Usage: cabot [OPTION] [SERVER]

Options:
  -h           Print this help page and exit.
  -l SOURCE    Load data from standard input (adding stamps and SOURCE).
  -e SOURCE    Erase entries when from SOURCE, and dump them.
  -d           Dump the whole database to standard output.
  -u           Undump (a partial) database from standard input.

Unless special options are used, the bot installs under name `cabot' within
channels `#cabot' and `#icule' on SERVER, or if SERVER is not given, according
to `IRCSSERVER' environment variable.

The bot replies directly to the user sending private messages, otherwise it
listens and replies on the public channels it joined.  Roughly said, it there
recognises a command when the line start with its name followed by a colon, if
the line starts with a comma, or within the line after two commas.  A single
word on a line, followed by a question mark, is also recognized.
"""

NAME_PASSWORD = 'cabot', 'martgolu'
NAME_PASSWORD = 'cabot', None
#CHANNELS = '#cabot', '#icule'
CHANNELS = '#cabot',
file_encoding = 'UTF-8'

# REVOIR:
# - Base de données pour les manuels Python, le site Python, Vaults, Wiki.
# - Interface au DMF.
# - Donner +o à `icule' lorsqu'il arrive.

__metaclass__ = type
import codecs, os, random, re, sys, time
import common, ircbot, irclib

# Instantiate all commands.
import autopun, chat, database

class Main:

    def main(self, *arguments):
        # Decode arguments.
        program = None
        import getopt
        options, arguments = getopt.getopt(arguments, 'de:hl:u')
        for option, value in options:
            if option == '-d':
                program = database.dump_database,
            elif option == '-e':
                program = database.erase_entries, value
            elif option == '-h':
                sys.stdout.write(__doc__)
                return
            elif option == '-l':
                program = database.load_entries, value
            elif option == '-u':
                program = database.undump_database,
        if program is None:
            if arguments:
                program = self.start_bot, arguments[0]
                arguments = arguments[1:]
            else:
                program = self.start_bot, os.environ['IRCSERVER']
        assert not arguments, arguments
        sys.stdout = codecs.getwriter(file_encoding)(
            sys.stdout, 'backslashreplace')
        sys.stderr = codecs.getwriter(file_encoding)(
            sys.stderr, 'backslashreplace')
        program[0](*program[1:])

    def start_bot(self, irc_server):
        common.server = Server(irc_server)
        try:
            common.server.start()
        except KeyboardInterrupt:
            common.server.die()

run = Main()
main = run.main

class Server(ircbot.SingleServerIRCBot):
    seconds_between_bursts = 10
    seconds_per_line = 2
    queue_timeout_in_seconds = 600
    bluemoon_interval = 10000

    def __init__(self, irc_server):
        # TARGETS is a rotating list of targets being output to, from the
        # most recently written to the least recently written, and QUEUES
        # contains pending output actions indexed by target.
        self.targets = []
        self.queues = {}
        # When OUTPUT_ACTIVE, output is currently scheduling itself, and
        # OUTPUT_STAMP is time of last overall output.
        self.output_active = False
        self.output_stamp = time.time()
        # When BLUEMOON drops back to zero, it's time to reply to a message
        # even when not being addressed to.  This is not to occur often.
        self.bluemoon = random.randrange(self.bluemoon_interval)
        # Launch server.
        self.joins = CHANNELS
        ircbot.SingleServerIRCBot.__init__(
            self, [(irc_server, 6667)], NAME_PASSWORD[0], NAME_PASSWORD[0])

    def on_nicknameinuse(self, connection, event):
        connection.nick(connection.get_nickname() + "_")

    def on_welcome(self, connection, event):
        if NAME_PASSWORD[1]:
            time.sleep(1)
            connection.notice('nickserv', 'identify %s' % NAME_PASSWORD[1])
            time.sleep(2)
        for join in self.joins:
            connection.join(join)

    def on_privmsg(self, connection, event):
        self.process_message(connection, event, True)

    def on_pubmsg(self, connection, event):
        self.process_message(connection, event, False)

    def process_message(self, connection, event, private):
        line = event.arguments()[0]
        # Try some detectable encodings.  If none detected, assume Latin-1.
        for encoding in 'ASCII', 'UTF-8':
            try:
                line = line.decode(encoding)
            except UnicodeDecodeError:
                pass
            else:
                break
        else:
            if re.search('[\x80-\x9f]', line):
                # The truth is that we have no idea of the real encoding.
                # Manage to output `\uNNNN' everywhere outside ASCII.
                encoding = 'ASCII'
            else:
                encoding = 'ISO-8859-1'
            line = line.decode('ISO-8859-1')
        # Set SOURCE to the requesting nick.  Set TARGET to either a nick or
        # channel, where the command output should go.
        self.source = irclib.nm_to_n(event.source())
        if private:
            writer = connection.notice
            self.target = self.source
            code = '/'
        else:
            writer = connection.privmsg
            self.target = event.target()
            code, line = find_command(connection, line)
            if code is None:
                if self.bluemoon == self.bluemoon_interval:
                    code = ':'
                    self.bluemoon = random.randrange(self.bluemoon_interval)
                else:
                    self.bluemoon += 1
        # CODE is now the command type (`/' private, `:` naming the bot,
        # `,' using comma or double comma, `?' question mark after word,
        # or None) and LINE is the extracted command as a Unicode string.
        if code and line.rstrip():
            # Dispatch and produce output lines.
            fragments = []
            try:
                try:
                    fields = line.split(None, 1)
                    keyword = fields[0]
                    if len(fields) > 1:
                        rest = fields[1]
                    else:
                        rest = ''
                    command = common.Command.registry.get(keyword)
                    if command is not None:
                        arguments = command.split_arguments(rest)
                        command.check_number_arguments(arguments)
                        command.handler(fragments.append, *arguments)
                    if not fragments:
                        for matcher in common.Command.matchers:
                            matcher(fragments.append, line)
                            if fragments:
                                break
                except common.Error:
                    raise
                except:
                    import traceback
                    # FIXME: Should send tracebacks to the Cabot log.
                    traceback.print_exc(file=sys.stderr)
                if not fragments and code != '?':
                    choice = random.randrange(0, common.Command.burps[-1][0])
                    for weight, handler in common.Command.burps:
                        if choice < weight:
                            handler(fragments.append, line)
                        if fragments:
                            break
            except common.Error, exception:
                common.Command.error_handler(fragments.append, str(exception))
            # Schedule a reply, then log both the request and the reply.
            text = ''.join(fragments)
            if code == '?':
                text = common.choice(5, text, self.source + ': ' + text)
            # Clean spurious white space.
            lines = [line.rstrip() for line in text.splitlines()]
            while lines and not lines[-1]:
                del lines[-1]
            while lines and not lines[0]:
                del lines[0]
            if lines:
                # Append lines to proper NICK's queue.
                if self.target in self.queues:
                    queue = self.queues[self.target]
                else:
                    queue = self.queues[self.target] = Queue()
                    if self.target not in self.targets:
                        self.targets.append(self.target)
                queue.save_lines(writer, self.target, lines, encoding)
                # Restart output if not already in progress.
                if queue and not self.output_active:
                    self.send_something()
            common.Log('%s: %r -> %r\n' % (self.target, line, text))
        else:
            common.Log('%s: %r!\n' % (self.target, line))

    def send_something(self):
        # How many lines can we burst together without flooding?
        now = time.time()
        if now > self.output_stamp + self.seconds_between_bursts:
            burstable = self.seconds_between_bursts // self.seconds_per_line
        else:
            burstable = 1
        # Round-robin output between all active targets.
        while self.targets:
            # Remove oldest target from list.  If output for that target is
            # still possible, it will be reinserted either as youngest if
            # output occurred, or back as oldest if output is delayed.
            target = self.targets.pop()
            queue = self.queues[target]
            if burstable:
                # Send some output right away.
                queue.send_line()
                if queue and not queue.suspended:
                    self.targets.insert(0, target)
                self.output_stamp = now
                burstable -= 1
            else:
                # Output pending, but we now have to wait.
                self.targets.append(target)
                self.connection.execute_delayed(
                    self.seconds_per_line, self.send_something)
                self.output_active = True
                return
        # No more active targets.  Get rid of expired queues.
        for target, queue in self.queues.items():
            if not queue or now > queue.stamp + self.queue_timeout_in_seconds:
                del self.queues[target]
                if target in self.targets:
                    self.targets.remove[target]
        self.output_active = False

def find_command(connection, line):
    if line.startswith(','):
        return ',', line[1:].strip()
    if ' ' not in line and line.endswith('?'):
        return '?', line[:-1]
    if ':' in line:
        left, right = line.split(':', 1)
        lower = irclib.irc_lower
        if lower(left) == lower(connection.get_nickname()):
            return ':', right.strip()
    if ',,' in line:
        left, right = line.split(',,', 1)
        return ',', right.strip()
    return None, line

class Queue(list):
    lines_per_page = 10

    def __init__(self):
        list.__init__(self)
        self.suspended = False

    def save_lines(self, function, target, lines, encoding):
        if self.suspended:
            del self[:]
        for line in lines:
            # Try to manage so messages are within 512 characters overall.
            # Approximative for now.
            if len(line) > 480:
                import textwrap
                for line in textwrap.wrap(line, 480):
                    self.append((function, target,
                                 line.encode(encoding, 'backslashreplace')))
            else:
                self.append((function, target,
                             line.encode(encoding, 'backslashreplace')))
        self.allow_more()
        self.stamp = time.time()

    def allow_more(self):
        self.sent_in_page = 0
        self.suspended = False

    def send_line(self):
        function, target, line = self.pop(0)
        self.sent_in_page += 1
        if self.sent_in_page == self.lines_per_page and self:
            line += ' ..[Type ,more]'
            self.suspended = True
        elif not line:
            line = ' '
        if line.startswith('/me '):
            common.server.connection.action(target, line[3:].lstrip())
        else:
            function(target, line)

if __name__ == '__main__':
    main(*sys.argv[1:])
