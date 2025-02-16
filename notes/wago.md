# WAGO IO-Error LED

Default credentials are: admin:wago

Generating a new ea-config.xml based on the currently attached terminals:

``` js
await fetch("http://192.168.178.172/DOCPLFUNC", {
    "credentials": "include",
    "headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.7,de;q=0.3",
        "Content-Type": "application/x-www-form-urlencoded",
        "Sec-GPC": "1",
        "Authorization": "Basic YWRtaW46d2Fnbw==",
        "Upgrade-Insecure-Requests": "1",
        "Priority": "u=4",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache"
    },
    "referrer": "http://192.168.178.172/webserv/cplcfg/ea-config.ssi",
    "body": "DO_CREATE_EA_XML=create+ea-config.xml",
    "method": "POST",
    "mode": "cors"
});
```

Download ea-config.xml under http://192.168.178.172/etc/ea-config.xml (authorization required)