# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Request, HtmlResponse
from scrapy_splash import SplashRequest, SplashJsonResponse, SplashTextResponse
import base64
import time
import datetime
from pkgutil import get_data
from w3lib.http import basic_auth_header

class parameters:
    starturl = 'https://www.betfair.com/exchange/plus/football/competition/10932509'
    #starturl = 'https://www.betfair.com/exchange/plus/football'
    baseurl = 'https://www.betfair.com/exchange/plus/'
    #input link format: http://localhost:8050/\\"football/market/1.155251684\\
    #localhost = 'http://localhost:8050/\\"'
    localhost = 'https://rvgvp6ok-splash.scrapinghub.com/\\'
    #wait = 10
    sleeptime = 3

class BetfairItem(scrapy.Item):
    gametag = scrapy.Field()
    eventname = scrapy.Field()
    competition = scrapy.Field()
    timestamp = scrapy.Field()
    current_gametime = scrapy.Field()
    current_score = scrapy.Field()
    volume = scrapy.Field()
    pick_1 = scrapy.Field()
    pick_2 = scrapy.Field()
    pick_X = scrapy.Field()
    back_1 = scrapy.Field()
    back_2 = scrapy.Field()
    back_X = scrapy.Field()
    HH_back_X = scrapy.Field()
    AH_back_X = scrapy.Field()
    noscore_back = scrapy.Field()

def addbaselink(rellink):
    abslink = parameters.baseurl + rellink
    return abslink

def saveimage(response, tag):
    imgdata = base64.b64decode(response.data['png'])
    marketid = response.url.split(".")[-1]
    marketid = marketid.replace("'\'",'')
    name = marketid + str(tag) + str(int(time.time()))
    _file2 = "{0}.png".format(name)
    with open(_file2, 'wb') as f:
        f.write(imgdata)

def getsessionid(response):
    sessionid = "create"
    # headers = response.data['headers']
    # sessionheader = next((item for item in headers if item["name"] == "X-Crawlera-Session"),dict())
    # if "value" in sessionheader:
    #     sessionid = sessionheader.get("value")
    return sessionid

class CoursecrawlerSplashSpider(CrawlSpider):
    name = 'oddsscraper'
    #allowed_domains = ['betfair.com']

    def __init__(self, *args, **kwargs):
        # to be able to load the Lua script on Scrapy Cloud, make sure your
        # project's setup.py file contains the "package_data" setting, similar
        # to this project's setup.py
        self.LUA_SOURCE = get_data(
            'betfair', 'scripts/crawlera.lua'
        ).decode('utf-8')
        super(CoursecrawlerSplashSpider, self).__init__(*args, **kwargs)

    #overwrite these 2 functions of CrawlSpider class to avoid non-HtmlResponses get skipped in CrawlSpider
    #see https://github.com/scrapy-plugins/scrapy-splash/issues/92
    def _requests_to_follow(self, response):
        print "entered _request_to_follow"
        seen = set()
        for n, rule in enumerate(self._rules):
            links = [lnk for lnk in rule.link_extractor.extract_links(response) if lnk not in seen]
            print links

            if links and rule.process_links:
                links = rule.process_links(links)
            for link in links:
                seen.add(link)
                r = self._build_request(n, link)
                yield rule.process_request(r)

    def _build_request(self, rule, link):
        print link.url
        #r = SplashRequest(url=link.url, endpoint='execute', callback=self._response_downloaded, args={'html': 1, 'png': 1, 'wait': parameters.wait, 'timeout': 300, 'lua_source': self.script})
        r = SplashRequest(
            url=link.url,
            endpoint='execute', 
            callback=self._response_downloaded,
            dont_filter=True,
            splash_headers={
                'Authorization': basic_auth_header(self.settings['SPLASH_APIKEY'], ''),
            },
            args={
                'lua_source': self.LUA_SOURCE,
                'crawlera_user': self.settings['CRAWLERA_APIKEY'],
                'timeout': 60,
            },
            cache_args=['lua_source'],
        )
        r.meta.update(rule=rule, link_text=link.text)
        return r

    def start_requests(self):
        print "start_requests"
        #yield SplashRequest(url=parameters.starturl, endpoint='execute', args={'html': 1, 'png': 1, 'wait': parameters.wait, 'timeout': 300, 'lua_source': self.script}, )
        yield SplashRequest(
            url=parameters.starturl,
            endpoint='execute',
            splash_headers={
                'Authorization': basic_auth_header(self.settings['SPLASH_APIKEY'], ''),
            },
            args={
                'lua_source': self.LUA_SOURCE,
                'crawlera_user': self.settings['CRAWLERA_APIKEY'],
                'timeout': 60,
            },
            # tell Splash to cache the lua script, to avoid sending it for every request
            cache_args=['lua_source'],
        )

    rules = (
        Rule(LinkExtractor(restrict_xpaths='//span[contains(text(),"Sat 30 Mar")]/ancestor::div[contains(@class,"card-header")]/following-sibling::div/descendant::a[contains(@class,"mod-link")]'), 
                process_links='process_links', process_request='splash_request', callback='parse_main', follow=True),
        # Rule(LinkExtractor(restrict_xpaths='//td/a[contains(@class,"mod-link")]'), 
        #     process_links='process_links', process_request='splash_request', callback='parse_main', follow=True),
        # Rule(LinkExtractor(restrict_xpaths='//a[text()="Match Odds "]'), 
        #     process_links='process_links', process_request='splash_request', callback='parse_main', follow=False),      
    )

    def process_links(self, links):
        print "process_links"
        print "input links:"
        print links
        #http://localhost:8050/\\"football/market/1.155251684\\
        for link in links:
            if parameters.localhost in link.url:
                #[:-2] to remove the \\ in http://localhost:8050/\\"football/market/1.155251684\\
                link.url = link.url.replace(parameters.localhost, parameters.baseurl)
                link.url = link.url[:-2]
        print "output links:"
        print links
        return links

    def splash_request(self, request):
        # print "processing splash test to add waiting time"
        # print "Sleeping " + str(parameters.sleeptime) + " seconds"
        # time.sleep(parameters.sleeptime)
        return request


    def parse_main(self, response):
        print "processing parse_main"
        print response.url
        print response.headers

        print "saving image..."
        saveimage(response,"_main_")

        #scrape main data
        eventname = response.xpath('//a[contains(@class,"EVENT   open active-node")]/text()').extract_first()
        competition = response.xpath('//a[@link-type="COMP"]/text()').extract_first()
        timestamp = int(time.time())
        current_gametime = response.xpath('//p[@class="time-elapsed inplay"]/span/text()').extract_first()
        volume = response.xpath('//*[contains(@class,"total-matched")]/text()')[1].extract()

        #construct gametag
        today = datetime.datetime.today().strftime('%Y%m%d')
        teams = eventname.split(" v ")
        gametag = today + "_" + teams[0][:3] + teams[1][:3]
        gametag = gametag.upper()
        print "gametag: " + gametag

        #prices
        table = response.xpath('//table[@class="mv-runner-list"]')[1]
        rows = table.xpath('.//tr')
        prices = rows.xpath('.//button[contains(@class,"back-button back-selection-button")]/@price').extract()
        picks = rows.xpath('.//h3/text()').extract()
        print "picks and prices: "
        print picks
        print prices
        back_1 = prices[0]
        back_2 = prices[1]
        back_X = prices[2]
        pick_1 = picks[0]
        pick_2 = picks[1]
        pick_X = picks[2]

        #store in item
        item = BetfairItem()
        item['gametag'] = gametag
        item['eventname'] = eventname
        item['competition'] = competition
        item['timestamp'] = timestamp
        item['current_gametime'] = current_gametime
        item['volume'] = volume
        item['pick_1'] = pick_1
        item['pick_2'] = pick_2
        item['pick_X'] = pick_X
        item['back_1'] = back_1
        item['back_2'] = back_2
        item['back_X'] = back_X

        #reuse session ID
        # session_id = getsessionid(response)
        # print "gametag: " + gametag
        # print "session_id: " + session_id
        # sessionidscript = self.script.replace("create",session_id)

        #send new follow-up request: noscore
        correct_score_link = response.xpath('//a[text()="Correct Score "]/@href').extract_first()
        correct_score_link = addbaselink(correct_score_link)
        print correct_score_link
        print "Sleeping " + str(parameters.sleeptime) + " seconds"
        time.sleep(parameters.sleeptime)
        #r = SplashRequest(url=correct_score_link, endpoint='execute', callback=self.parse_correctscore, args={'html': 1, 'png': 1, 'wait': parameters.wait, 'timeout': 300, 'lua_source': sessionidscript})
        r = SplashRequest(
            url=correct_score_link,
            endpoint='execute',
            callback=self.parse_correctscore,
            splash_headers={
                'Authorization': basic_auth_header(self.settings['SPLASH_APIKEY'], ''),
            },
            args={
                'lua_source': self.LUA_SOURCE,
                'crawlera_user': self.settings['CRAWLERA_APIKEY'],
                'timeout': 60,
            },
            cache_args=['lua_source'],
        )
        r.meta['item'] = item
        return r

    def parse_correctscore(self, response):
        print "processing parse_correctscore"
        print response.url
        print response.headers

        #welcome item
        item = response.meta['item']

        print "saving image..."
        saveimage(response,"_correctscore_")

        #find current score and noscore_back
        current_score = response.xpath('//span[contains(@class,"score")]/text()').extract_first()
        print current_score
        if current_score == ' ' or current_score is None:
            current_score = '0-0 '
        print current_score
        current_score_l = current_score.strip().split('-')
        current_score_s = current_score_l[0] + " - " + current_score_l[1]
        noscore_row = response.xpath('//h3[text()="' + current_score_s + '"]/ancestor::tr')
        noscore_back = noscore_row.xpath('.//button[contains(@class,"back-button back-selection-button")]/@price').extract_first()
        print "noscore_back:"
        print current_score_s
        print noscore_back

        #store in item
        item['current_score'] = current_score_s
        item['noscore_back'] = noscore_back

        #reuse session ID
        # session_id = getsessionid(response)
        # print "session_id: " + session_id
        # sessionidscript = self.script.replace("create",session_id)

        #send new follow-up request: home handicap
        home_team = item['pick_1']
        home_plusone = "" + home_team + " +1 "
        home_handicap_link = response.xpath('//a[text()="' + home_plusone + '"]/@href').extract_first()
        home_handicap_link = addbaselink(home_handicap_link)
        print home_handicap_link
        print "Sleeping " + str(parameters.sleeptime) + " seconds"
        time.sleep(parameters.sleeptime)
        
        #r = SplashRequest(url=home_handicap_link, endpoint='execute', callback=self.parse_homehandicap, args={'html': 1, 'png': 1, 'wait': parameters.wait, 'timeout': 300, 'lua_source': sessionidscript})
        r = SplashRequest(
            url=home_handicap_link,
            endpoint='execute',
            callback=self.parse_homehandicap,
            splash_headers={
                'Authorization': basic_auth_header(self.settings['SPLASH_APIKEY'], ''),
            },
            args={
                'lua_source': self.LUA_SOURCE,
                'crawlera_user': self.settings['CRAWLERA_APIKEY'],
                'timeout': 60,
            },
            cache_args=['lua_source'],
        )
        r.meta['item'] = item
        return r

    def parse_homehandicap(self, response):
        print "processing parse_homehandicap"
        print response.url
        print response.headers

        #welcome item
        item = response.meta['item']

        print "saving image..."
        saveimage(response,"_homehandicap_")

        #prices
        table = response.xpath('//table[@class="mv-runner-list"]')[1]
        rows = table.xpath('.//tr')
        prices = rows.xpath('.//button[contains(@class,"back-button back-selection-button")]/@price').extract()
        picks = rows.xpath('.//h3/text()').extract()
        HH_back_X = prices[2]
        print "home_handicap_back_X:"
        print HH_back_X

        #store in item
        item['HH_back_X'] = HH_back_X

        #reuse session ID
        # session_id = getsessionid(response)
        # print "session_id: " + session_id
        # sessionidscript = self.script.replace("create",session_id)

        #send new follow-up request: home handicap
        away_team = item['pick_2']
        away_plusone = "" + away_team + " +1 "
        away_handicap_link = response.xpath('//a[text()="' + away_plusone + '"]/@href').extract_first()
        away_handicap_link = addbaselink(away_handicap_link)
        print away_handicap_link
        print "Sleeping " + str(parameters.sleeptime) + " seconds"
        time.sleep(parameters.sleeptime)
        
        #r = SplashRequest(url=away_handicap_link, endpoint='execute', callback=self.parse_awayhandicap, args={'html': 1, 'png': 1, 'wait': parameters.wait, 'timeout': 300, 'lua_source': sessionidscript})
        r = SplashRequest(
            url=away_handicap_link,
            endpoint='execute',
            callback=self.parse_awayhandicap,
            splash_headers={
                'Authorization': basic_auth_header(self.settings['SPLASH_APIKEY'], ''),
            },
            args={
                'lua_source': self.LUA_SOURCE,
                'crawlera_user': self.settings['CRAWLERA_APIKEY'],
                'timeout': 60,
            },
            cache_args=['lua_source'],
        )
        r.meta['item'] = item
        return r

    def parse_awayhandicap(self, response):
        print "processing parse_awayhandicap"
        print response.url
        print response.headers

        #welcome item
        item = response.meta['item']

        print "saving image..."
        saveimage(response,"_awayhandicap_")

        #prices
        table = response.xpath('//table[@class="mv-runner-list"]')[1]
        rows = table.xpath('.//tr')
        prices = rows.xpath('.//button[contains(@class,"back-button back-selection-button")]/@price').extract()
        picks = rows.xpath('.//h3/text()').extract()
        AH_back_X = prices[2]
        print "away_handicap_back_X:"
        print AH_back_X

        #store in item
        item['AH_back_X'] = AH_back_X

        #return item
        return item
