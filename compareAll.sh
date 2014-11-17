#!/bin/sh

rm compare.log
while read p; do python comparePrototype.py $p; done<numbers.txt
python plotAll.py
