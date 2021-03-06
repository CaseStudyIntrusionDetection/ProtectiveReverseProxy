> **Attention: This is a student's project, not a (fully) functional product.**

> *Adding a layer of protection in front of a web application does not guarantee perfect security.
> Always make sure to secure the main web application using best practices!*

# **P**rotective**R**everse**P**roxy
The Protective Reverse Proxy (PRP) to place in front of a web service to protect it.

![Architecture of PRP](conf/prp_graphic.svg)

## Configuration

> After configuring the SMTP E-Mail notifications one may send a testmail by 
> running `docker exec --user www-data protection_proxy python /proxy/mail.py`.
> One may run `python /proxy/mail.py --debug` to get debug output.

> Logs can be found at `/tmp/prp.log` and printed by
> `docker exec --user www-data protection_proxy tail -n 20 /tmp/prp.log`