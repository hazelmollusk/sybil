#!/usr/bin/env python3
"""
DOCSTRING for first public console interface.

USAGE:
    soothsayer [options]
"""
import sys
import re
from functools import cached_property
from argparse import ArgumentParser, Namespace
from random import randint
from logging import warn, debug, getLogger, WARN, INFO, DEBUG
from pathlib import Path
from soothsayer.libs.fortune_file import FortuneFile, DEFAULT_FORTUNE_PATH
from pprint import pp


class Soothsayer:

    def __init__(self, cmd=None, params=[], *args, **kwargs):
        self.args = cmd
        self.opts = None
        self._files = {}
        if params or args or kwargs:
            self.process_options(params, *args, **kwargs)

    def main(self, main_args=None):
        debug('main')
        args = main_args or self.args or sys.argv[1:]
        self.process_args(args)
        return self.run()

    def get_opts(self):
        if not hasattr(self, '_opts'):
            self._opts = None
        return self._opts

    def set_opts(self, val):
        if val is None:
            return
        if not isinstance(val, Namespace):
            raise TypeError('Soothsayer.opts must be of type argparse.Namespace'
                            + f' ({val} is of type {type(val)})')
        self._opts = val
        if self._opts.verbose:
            getLogger().setLevel(INFO)
        if self._opts.debug:
            getLogger().setLevel(DEBUG)

    opts = property(get_opts, set_opts)

    def process_args(self, args=None):
        debug('process_args')
        parser = ArgumentParser()
        parser.add_argument('-a', '--all', action='store_true',
                            help='Choose from all lists of maxims, both offensive and not.')
        parser.add_argument('-c', '--show-file', action='store_true',
                            help='Show the cookie file from which the fortune came.')
        parser.add_argument('-e', '--equal', action='store_true',
                            help='Consider all fortune files to be of equal size.')
        parser.add_argument('-f', '--list-files', action='store_true',
                            help='Print out the list of files which would be searched; don’t print a fortune.')
        parser.add_argument('-l', '--long', action='store_true',
                            help='Long dictums only.')
        parser.add_argument('-m', '--match', type=str,
                            help='Print out all fortunes which match the basic regular expression pattern.')
        parser.add_argument('-n', '--short-max', default=160, type=int,
                            help='Set the longest fortune length considered short.')
        parser.add_argument('-o', '--off', action='store_true',
                            help='Choose only from potentially offensive aphorisms.')
        parser.add_argument('-s', '--short', action='store_true',
                            help='Short apothegms only.')
        parser.add_argument('-i', '--ignore-case', action='store_true',
                            help='Ignore case for -m patterns.')
        parser.add_argument('-w', '--wait', action='store_true',
                            help='Wait before termination for an amount of time calculated from the number of characters in the message.')
        parser.add_argument('-u', action='store_true',
                            help='Don’t translate UTF-8 fortunes to the locale when searching or translating.')
        parser.add_argument('-v', '--verbose', action='store_true')
        parser.add_argument('-d', '--debug', action='store_true')
        parser.add_argument('params', metavar='arg', nargs='*',
                            help='[#%%] file/directory/all')
        self.opts = parser.parse_args(args)
        return self.opts

    def process_options(self, params=[], *args, **kwargs):
        debug('process_options')
        VALID_FLAGS = ('all', 'show_file', 'equal', 'list_files', 'long', 'off',
                       'short', 'ignore_case', 'wait', 'u', 'verbose', 'debug')
        VALID_ARGS = {'match': str, 'short_max': 160}
        for arg in args:
            if arg in VALID_FLAGS and arg not in kwargs:
                kwargs[arg] = True
        for k, v in kwargs:
            if k not in (VALID_FLAGS + VALID_ARGS.keys()):
                warn(f'option "{k}" not recognized!')
                del kwargs[k]
            if (k in VALID_FLAGS and type(v) is not bool) or \
                    (k in VALID_ARGS and type(v) is not VALID_ARGS[k]):
                warn(f'"{k}" is not valid for option {k}')
        self.opts = Namespace(**kwargs)
        return self.opts

    def process_files(self, params):
        debug('process_files')
        self._files = {}
        next_weight = None
        while len(params):
            next_sym = params.pop(0)
            if m := re.fullmatch(r'([0-9]+)%?', next_sym):
                next_weight = m.group(0)
            else:
                for next_file in FortuneFile.load_path(next_sym):
                    self._files[next_file] = next_weight

    def run(self, cmd=[], params=[], *args, **kwargs):
        debug('run')
        if cmd:
            self.process_args(cmd)
        if params or args or kwargs:
            self.process_options(params, *args, **kwargs)
        self.process_files(self.opts.params)
        if self.opts.show_file:
            pass
        elif self.opts.list_files:
            pass
        # elif self.opts.version:
        #     pass
        else:
            fortune = self.fortune
            print(fortune)
            return 0

    @property
    def files(self):
        f = self._files or self.default_files
        r = []
        for k, v in f.items():
            if not (v and k.length):
                debug(f'removing file {k}')
                r.append(k)
        for k in r:
            del f[k]
        return f

    @cached_property
    def default_files(self):
        def_files = {}
        def_path = DEFAULT_FORTUNE_PATH if self.opts.all \
            else f'{DEFAULT_FORTUNE_PATH}/fortunes.dat'
        for next_file in FortuneFile.load_path(def_path):
            def_files[next_file] = 1
            debug(f'{next_file.path} has {next_file.length} entries')
        return def_files

    @property
    def fortune(self):
        total = sum(self.files.values())
        num = randint(0, total - 1)
        debug(f'fortune() file #{num}/{total}')
        selected = None
        for ff, weight in self.files.items():
            debug(f'{ff}: {num} - {weight}')
            num -= weight
            if num < 0:
                debug(f'{ff.path} is selected')
                selected = ff
                if selected.length > 0:
                    break
                warn(f'{ff} has no entries!')

        return selected.get_random(self.opts)


def main(*args, **kwargs):
    return Soothsayer(*args, **kwargs).main()


if __name__ == '__main__':
    exit(main())