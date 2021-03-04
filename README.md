# ProtectiveReverseProxy
The protective reverse proxy to place in front of a web service to protect it.


## Configuration

> After configuring the STMP E-Mail notifications one may send a testmail by 
> running `docker exec --user www-data protection_proxy python /proxy/mail.py`.
> One may run `python /proxy/mail.py --debug` to get debug output.

> Logs can be found at `/tmp/prp.log` and printed by
> `docker exec --user www-data protection_proxy tail -n 20 /tmp/prp.log`