sudo ifconfig tap0 down
sudo ifconfig tap0 hw ether 30:14:4a:e6:46:e4
sudo ifconfig tap0 mtu 440
sudo ifconfig tap0 192.168.123.2 netmask 255.255.255.0 up

sudo route del -net 192.168.123.0/24
sudo route add -net 192.168.123.0/24 mss 400 dev tap0

sudo arp -s 192.168.123.1 12:34:56:78:90:ab

