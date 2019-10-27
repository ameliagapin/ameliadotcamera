#!/bin/sh

ip=`ipconfig getifaddr en0`
hugo server -D --bind $ip --baseURL http://$ip
