#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright © 2004 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2004.

"""\
Charger quelques abréviations.
"""

__metaclass__ = type
import os, sys
from Cabot import database

class Main:

    def main(self, *arguments):
        import getopt
        options, arguments = getopt.getopt(arguments, '')
        for option, valeur in options:
            pass
        triplets = []
        for ligne in file('/home/pinard/pers/listes/abréviations'):
            ligne = ligne.rstrip()
            if not ligne:
                continue
            cle, valeur = ligne.split(None, 1)
            if cle.isupper():
                continue
            if valeur.startswith('='):
                continue
            triplets.append((cle.lower(), cle.upper(), '"%s"' % valeur))
        db = database.Db('c')
        db.delete_entries('@abbrev')
        db.add_entries('@abbrev', triplets)
        db.close()

run = Main()
main = run.main

if __name__ == '__main__':
    main(*sys.argv[1:])
