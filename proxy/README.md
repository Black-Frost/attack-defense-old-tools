Proxy to run and handle traffic.

Using TPROXY

```bash
sudo iptables -t nat -I PREROUTING 1 -p tcp --dport 22 -j REDIRECT --to-port 22
sudo iptables -t nat -I PREROUTING 2 -p tcp -j REDIRECT --to-port <proxy_port>
```

We redirect every traffic to `proxy_port` except for port 22, every rule below is now considered useless. And we can rollback by deleting the first 2 rules.

```bash
sudo iptables -t nat -D PREROUTING 2 # Remove the redirect rule
```

This proxy will first create a connection to the real challenge bases on the port coming. We can modify this by editing `origin_mapping.py`.

We can modify input and output by editing `flagcheck.py`.

The proxy also have a http RESTAPI running to quickly get the result real time, because filtering by log files or by looking at terminal will be slower. This http will have a route exposed outside which other should not be able to scan for. (Anyhow, the Proxy is not having other outgoing port)
