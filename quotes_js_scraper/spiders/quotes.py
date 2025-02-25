import scrapy
from scrapy_playwright.page import PageMethod 
from quotes_js_scraper.items import QuoteItem 

class QuotesSpider(scrapy.Spider):
    name = 'quotes'

    def start_requests(self):
        url = 'http://quotes.toscrape.com/scroll'
        yield scrapy.Request(
            url,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", "div.quote"),
                    PageMethod("evaluate", """
                        async () => {
                            let previousHeight = 0;
                            while (document.body.scrollHeight > previousHeight) {
                                previousHeight = document.body.scrollHeight;
                                window.scrollBy(0, document.body.scrollHeight);
                                await new Promise(resolve => setTimeout(resolve, 2000));  // Wait 2s
                            }
                        }
                    """) 
                ],
            },
            errback=self.errback
        )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        quote_item = QuoteItem()
        for quote in response.css("div.quote"):
            quote_item["text"] = quote.css("span.text::text").get() 
            quote_item["author"] = quote.css("small.author::text").get()
            quote_item["tags"] = quote.css("div.tags a.tag::text").getall()
            yield quote_item
        
        await page.close()
       
        next_page = response.css('.next>a ::attr(href)').get()
        if next_page is not None:
            next_page_url = 'http://quotes.toscrape.com' + next_page
            yield scrapy.Request(
                next_page_url, 
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "div.quote") 
                    ],
                },
                errback=self.errback
            )  

    async def errback(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.close()

  
  
    # def snap(self, response):
    #     """Save a screenshot of the page."""
    #     screenshot = response.meta.get('screenshot')
    #     if screenshot:
    #         with open('screenshot.png', 'wb') as image_file:
    #             image_file.write(screenshot)
    #         self.logger.info("Screenshot saved as screenshot.png") 
    #     else:
    #         self.logger.warning("No screenshot found in response.meta")  
 