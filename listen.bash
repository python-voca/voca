#!/bin/bash

run (){
    venv/bin/voca manage /tmp/voca/sock & sleep 1 && fg
    venv/bin/voca mic | nc -U /tmp/voca/sock
}

run
