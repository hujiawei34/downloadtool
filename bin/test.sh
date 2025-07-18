#!/bin/bash
cwd=$(cd $(dirname $0); pwd)
project_root=${cwd}/../
src_python_dir=${project_root}/src/python
cd $project_root
source venv/bin/activate
cd $src_python_dir
python run_tests.py
