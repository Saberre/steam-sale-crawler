Steam Summer Sale Crawler
=========================

Introduction
------------

This is a simple crawler for Steam Summer Sale 2012. It crawls these things:

- Flash Sales
- Community Votes
- Community Vote Results
- Community Choice Sale

Dependencies
------------

- [Beautiful Soup 4](http://www.crummy.com/software/BeautifulSoup/)
- [Advanced Python Scheduler](http://packages.python.org/APScheduler/)
- [Tweepy](http://tweepy.github.com/)

How to use
----------

Make your own config.py first, and run it!

```
python sss_crawler.py
```

or throw it background!

```
python sss_crawler.py &
```

License
-------

This project follows [WTFPL](http://sam.zoy.org/wtfpl/). Please check out [COPYING](https://github.com/Saberre/steam-summer-sale-crawler/tree/master/COPYING) file.