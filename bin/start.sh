#!/usr/bin/bash
project_dir=$(cd $(dirname $0)/..; pwd)
cd $project_dir

app_dir=$project_dir/src/python


function start_app() {
    cd $app_dir
    python app.py
}

function stop_app() {
    cd $app_dir
    pkill -f "python app.py"
}

function restart_app() {
    stop_app
    start_app
}
restart_app