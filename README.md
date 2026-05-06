![Memory Archive Logo](misc/images/banner.png)

**Memory Archive** is a self-hosted platform, built for Academic Lyceums 
(mainly, but can be used elsewhere) to share images (memories) via S3 
external storage

Security in uploading is made via authentication with EMIS (Ministry of 
Higher Education platform for lyceum students )

There is an instance for Academic Lyceum "International House - Tashkent", 
[you can check it out as an example ](https://t.me/archive_ihbot). </br>
**P.S.** for S3, we use [Cloupard](https://cloupard.uz) for our instances, 
it's pretty cheap considering it's a local provider (13k UZS per month for 
100 GB)

**WARNING**. This project was mainly _proudly vibe-coded_ with Claude, so
please forgive us for the code quality (at least it works, I mean)

### Self-hosting

For **development mode** (Dependencies: _Docker, Docker Compose, 
Python 3.14 (tested)_):
1. Copy [full.env.sample](./misc/samples/full.env.sample) into .env, and fill 
   all the values
2. Run `./scripts/setup.sh` (for macOS and Linux), it will set up virtualenv 
   and install needed requirements, running Docker Compose

For **production mode** (Dependencies: _Docker, Docker Compose_):
1. Copy [bot.env.sample](./misc/samples/bot.env.sample) and
   [web.env.sample](./misc/samples/web.env.sample) into bot.env and web.env 
   respectively, fill all the values
2. Run [docker-compose.prod.yml](docker-compose.prod.yml)

### Additional functionality and custdev

If you want to use this service to store and/or share some images for other
use case than Academic Lyceums (or be it lyceums) - freely contact our 
maintaining team by contacts below or by 
[technical@ihsu.uz](mailto:technical@ihsu.uz). 

We will be happy to help you edit code for your needs or help with setting up
hosting stuff.

### Contacts

**Maintainer**: Alex ([Telegram](https://t.me/megaplov), 
[Email](mailto:s.aleksei@21ci.uz))