#dump data from dqcache
33 * * * *   root    /usr/bin/svc -a /etc/service/rpiap_dqcache

#we create "urandom seed" every hour
44 * * * *   root    /lib/systemd/systemd-random-seed save
