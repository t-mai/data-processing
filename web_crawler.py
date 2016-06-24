from HTMLParser import HTMLParser
from urllib2 import urlopen
from urlparse import urljoin
from bs4 import BeautifulSoup

import logging
import os.path
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from nltk.corpus import stopwords

# We are going to create a class called LinkParser that inherits some
# methods from HTMLParser which is why it is passed into the definition
class LinkParser(HTMLParser):

    # This is a function that HTMLParser normally has
    # but we are adding some functionality to it
    def handle_starttag(self, tag, attrs):
        # We are looking for the begining of a link. Links normally look
        # like <a href="www.someurl.com"></a>
        if tag == 'a':
            for (key, value) in attrs:
                if key == 'href':
                    # We are grabbing the new URL. We are also adding the
                    # base URL to it. For example:
                    # www.netinstructions.com is the base and
                    # somepage.html is the new URL (a relative URL)
                    #
                    # We combine a relative URL with the base URL to create
                    # an absolute URL like:
                    # www.netinstructions.com/somepage.html

                    if value.find("http") <= -1:
                        newUrl = urljoin(self.baseUrl, value)
                        # And add it to our colection of links:
                        self.links = self.links + [newUrl]

    # This is a new function that we are creating to get links
    # that our spider() function will call
    def getLinks(self, url):
        self.links = []
        # Remember the base URL which will be important when creating
        # absolute URLs
        self.baseUrl = url
        # Use the urlopen function from the standard Python 3 library
        response = urlopen(url)
        # Make sure that we are looking at HTML and not other things that
        # are floating around on the internet (such as
        # JavaScript files, CSS, or .PDFs for example)
        if response.info().getheader('Content-Type').find('text/html') > -1:
            htmlString = response.read()
            self.feed(htmlString)
            soup = BeautifulSoup(htmlString, 'lxml')
            contentText = ""
            introtag = soup.find('section', id='section_introduction')
            if introtag is not None:
                ptags = introtag.find_all('p')
                contentText = "\n".join([tag.getText() for tag in ptags if tag.getText() != ""])
            return contentText, self.links
        else:
            return "",[]

def lines_cleanup(lines, min_length=3):
    """Clean up a list of lowercase strings of text for simple analysis.
    Splits on whitespace, removes all 'words' less than `min_length` characters
    long, and those in the `remove` set.
    Returns a list of strings.
    """
    remove = set(stopwords.words('english'))
    filtered = []

    for line in lines:
        if line != '':
            a = []
            for w in line.strip().lower().split():
                if len(w) > min_length and w not in remove:
                    a.append(w)
            filtered.append(' '.join(a))
    return filtered

# And finally here is our spider. It takes in an URL, a word to find,
# and the number of pages to search through before giving up
def spider(url, maxPages=200, outfile='output.txt'):  
    pagesToVisit = [url]
    visitedLinks = []
    numberVisited = 0
    foundWord = False
    # The main loop. Create a LinkParser and get all the links on the page.
    # Also search the page for the word or string
    # In our getLinks function we return the web page
    # (this is useful for searching for the word)
    # and we return a set of links from that web page
    # (this is useful for where to go next)
    
    output = open(outfile, 'w')
    while numberVisited < maxPages and pagesToVisit != []:
        numberVisited = numberVisited +1
        # Start from the beginning of our collection of pages to visit:
        url = pagesToVisit[0]
        pagesToVisit = pagesToVisit[1:]
        if url not in visitedLinks:
            try:
                print(numberVisited, "Visiting and saving %s to file %s" %(url,outfile))
                parser = LinkParser()
                data, links = parser.getLinks(url)
                if (data != ""):
                    output.write("\n".join(lines_cleanup(data.splitlines(), min_length=4)))
                visitedLinks = visitedLinks + [url]
                pagesToVisit = pagesToVisit + [page for page in links if page not in visitedLinks]
                pagesToVisit = pagesToVisit + links
            except:
                print(" **Failed to save data!**")
    output.close()
    print "Finished saved %s urls" % numberVisited

spider("http://www.japan-guide.com/", 10, 'output.txt')


if __name__ == '__main__':
    program = os.path.basename(sys.argv[0])
    logger = logging.getLogger(program)

    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s')
    logging.root.setLevel(level=logging.INFO)
    logger.info("running %s" % ' '.join(sys.argv))

    if len(sys.argv) < 4:
        print globals()['__doc__'] % locals()
        sys.exit()
    
    url, maxpages, outfile  = sys.argv[1:4]
    spider(url, int(maxpages), outfile)
