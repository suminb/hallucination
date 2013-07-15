import os, sys
sys.path.insert(0, 'hallucination')

from hallucination import *

h = Hallucination(dict(db_uri='sqlite:///test.db'))

def main():
    print h.select(1)

if __name__ == '__main__':
    main()
