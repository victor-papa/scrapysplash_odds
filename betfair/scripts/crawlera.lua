function use_crawlera(splash)
    local user = splash.args.crawlera_user
    local host = 'proxy.crawlera.com'
    local port = 8010
    --local session_header = 'X-Crawlera-Session'
    --local session_id = 'create'

    splash:on_request(function(request)

        -- Avoid using Crawlera for subresources fetching to increase crawling
        -- speed. The example below avoids using Crawlera for URLS starting
        -- with 'static.' and the ones ending with '.png'.
        if string.find(request.url, '%.json$') ~= nil or
        string.find(request.url, '%/gtm%.%') ~= nil or
        string.find(request.url, '%.css$') ~= nil or
        string.find(request.url, '%.js$') ~= nil or
        string.find(request.url, '%.gif$') ~= nil or
        string.find(request.url, '%.gif%') ~= nil or
        string.find(request.url, '%.svg$') ~= nil or
        string.find(request.url, '%.jpg$') ~= nil or
        string.find(request.url, '%=GET$') ~= nil or
        string.find(request.url, '%/images/%') ~= nil or
        string.find(request.url, '%/readonly/%') ~= nil or
        string.find(request.url, '%/csb/%') ~= nil or
        string.find(request.url, '%/static/%') ~= nil or
        string.find(request.url, '%/streaming/%') ~= nil or
        string.find(request.url, '%/signals/%') ~= nil or
        string.find(request.url, '%=MARKET_STATE$') ~= nil or
        string.find(request.url, '%MARKET_LICENCE$') ~= nil or
        string.find(request.url, '%RUNNER_EXCHANGE_PRICES_BEST$') ~= nil or
        string.find(request.url, '%.png$') ~= nil then
        return
        end

        -- Discard requests to advertising and tracking domains.
        if string.find(request.url, '%videoplayer%.') or
        string.find(request.url, '%regstat%.') or
        string.find(request.url, '%bing%.') or
        string.find(request.url, '%apieds%.') or
        string.find(request.url, '%qualtrics%.') or
        string.find(request.url, '%cdnppb%.') or
        string.find(request.url, '%maxymiser%.') or
        string.find(request.url, '%analytics%.') or
        string.find(request.url, '%adnxs%.') then
        request.abort()
        return
        end

        request:set_header('X-Crawlera-Cookies', 'disable')
        --request:set_header(session_header, session_id)
        request:set_proxy{host,port,username=user,password=''}
    end)

    --splash:on_response_headers(function (response)
    --    if type(response.headers[session_header]) ~= nil then
    --        session_id = response.headers[session_header]
    --    end
    --end)
end

function main(splash)
    use_crawlera(splash)
    splash:go(splash.args.url)
    assert(splash:wait(20))
    --return splash:html()

    local entries = splash:history()
    local last_response = entries[#entries].response

    return {
        html = splash:html(),
        headers = last_response.headers,
        png = splash:png(),
        har = splash:har(),
    }
end