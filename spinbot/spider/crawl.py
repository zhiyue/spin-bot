#!/usr/bin/env python3.4
# -*- coding: UTF-8 -*-
# vim:set shiftwidth=2 tabstop=2 expandtab textwidth=79:

"""A simple web crawler -- main driver program."""

# TODO:
# - Add arguments to specify TLS settings (e.g. cert/key files).

import argparse
import asyncio
import logging
import sys
import uvloop

from spinbot.spider.crawler import DoubanGroupUserCrawler, CoupletCrawler, get_user_agents
from spinbot.spider.reporting import *
from spinbot.settings import *

ARGS = argparse.ArgumentParser(description="Web crawler")
ARGS.add_argument(
    '--iocp', action='store_true', dest='iocp',
    default=False, help='Use IOCP event loop (Windows only)')
ARGS.add_argument(
    '--select', action='store_true', dest='select',
    default=False, help='Use Select event loop instead of default')
ARGS.add_argument(
    'roots', nargs='*',
    default=[], help='Root URL (may be repeated)')
ARGS.add_argument(
    '--max_redirect', action='store', type=int, metavar='N',
    default=10, help='Limit redirection chains (for 301, 302 etc.)')
ARGS.add_argument(
    '--max_tries', action='store', type=int, metavar='N',
    default=CRAWLER_SETTINGS.get('max_tries', 10),
    help='Limit retries on network errors')
ARGS.add_argument(
    '--max_tasks', action='store', type=int, metavar='N',
    default=CRAWLER_SETTINGS.get('max_tasks', 5),
    help='Limit concurrent connections')
ARGS.add_argument(
    '--exclude', action='store', metavar='REGEX',
    help='Exclude matching URLs')
ARGS.add_argument(
    '--strict', action='store_true',
    default=False, help='Strict host matching (default)')
ARGS.add_argument(
    '--lenient', action='store_false', dest='strict',
    default=True, help='Lenient host matching')
ARGS.add_argument(
    '-v', '--verbose', action='count', dest='level',
    default=2, help='Verbose logging (repeat for more verbose)')
ARGS.add_argument(
    '-q', '--quiet', action='store_const', const=0, dest='level',
    default=2, help='Only log errors')


def fix_url(url):
    """Prefix a schema-less URL with http://."""
    if '://' not in url:
        url = 'https://' + url
    return url


def main():
    """Main program.
    Parse arguments, set up event loop, run crawler, print report.
    """
    args = ARGS.parse_args()
    # if not args.roots:
    #     print('Use --help for command line help')
    #     return

    # levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    # logging.basicConfig(level=levels[min(args.level, len(levels)-1)])
    # logging.basicConfig(level=levels[2])

    # if args.iocp:
    #     from asyncio.windows_events import ProactorEventLoop
    #     loop = ProactorEventLoop()
    #     asyncio.set_event_loop(loop)
    # elif args.select:
    #     loop = asyncio.SelectorEventLoop()
    #     asyncio.set_event_loop(loop)
    # else:
    #     loop = asyncio.get_event_loop()
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()
    roots = {fix_url(root) for root in args.roots}
    user_agents = get_user_agents('user-agents.txt')
    crawler = DoubanGroupUserCrawler(roots,
                                     exclude=args.exclude,
                                     strict=args.strict,
                                     max_redirect=args.max_redirect,
                                     max_tries=args.max_tries,
                                     max_tasks=args.max_tasks,
                                     user_agents=user_agents,
                                     proxy='http://127.0.0.1:3128',
                                     group_range=(100000, 600000),
                                     loop=loop)
    try:
        loop.run_until_complete(crawler.crawl())  # Crawler gonna crawl.
    except KeyboardInterrupt:
        sys.stderr.flush()
        print('\nInterrupted\n')
    finally:
        report(crawler)
        print('\ncrawler number of users : {} \n'.format(len(crawler._users)))
        crawler.close()

        # next two lines are required for actual aiohttp resource cleanup
        loop.stop()
        loop.run_forever()

        loop.close()


if __name__ == '__main__':
    main()
