#!/usr/bin/env bash

# only run pep8 on sqlite env
if [ $DB = sqlite ]; then 
  pep8 *.py tests/ haas/
fi
