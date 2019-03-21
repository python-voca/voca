#!/bin/bash

run (){
    venv/bin/intervoice manage /tmp/intervoice/sock & sleep 1 && fg
    venv/bin/intervoice mic | nc -U /tmp/intervoice/sock
}

run 2>/dev/null
