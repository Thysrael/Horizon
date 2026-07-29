# Notion Agent health checks

Check the Horizon Notion Agent directly on the host:

```bash
curl --fail --silent --show-error http://127.0.0.1:4782/healthz
```

Then check the same endpoint through the stable Cloudflare Tunnel:

```bash
curl --fail --silent --show-error https://<public-hostname>/healthz
```

A successful local check confirms that the Listener is responding. A successful
public check confirms that the Tunnel can reach it. Supervise the Listener and
Tunnel separately so either process can be restarted and diagnosed
independently. If only the public check fails, inspect Tunnel status and routing;
if both fail, check the Listener first.
