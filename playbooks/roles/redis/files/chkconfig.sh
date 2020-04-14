#!/bin/bash
[ `grep redis /etc/rc.d/rc.local | wc -l` -eq 0 ] && echo -e '#redis\n/usr/local/redis/bin/redis-server /usr/local/redis/etc/redis.conf' >> /etc/rc.d/rc.local || /bin/true
