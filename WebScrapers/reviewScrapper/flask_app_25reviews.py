# doing necessary imports

from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import pymongo

app = Flask(__name__)  # initialising the flask app with the name 'app'




@app.route('/',methods=['POST','GET']) # route with allowed methods as POST and GET
def index():
    if request.method == 'POST':
        searchString = request.form['content'].replace(" ","") # obtaining the search string entered in the form
        try:
            dbConn = pymongo.MongoClient("mongodb://localhost:27017/")  # opening a connection to Mongo
            db = dbConn['crawlerDB'] # connecting to the database called crawlerDB
            reviews = db[searchString].find({}) # searching the collection with the name same as the keyword
            if reviews.count() > 0: # if there is a collection with searched keyword and it has records in it
                return render_template('results.html',reviews=reviews) # show the results to user
            else:
                review_count = 0
                flipkart_url = "https://www.flipkart.com/search?q=" + searchString # preparing the URL to search the product on flipkart
                uClient = uReq(flipkart_url) # requesting the webpage from the internet
                flipkartPage = uClient.read() # reading the webpage
                uClient.close() # closing the connection to the web server
                flipkart_html = bs(flipkartPage, "html.parser") # parsing the webpage as HTML
                bigboxes = flipkart_html.findAll("div", {"class": "_13oc-S"}) # seacrhing for appropriate tag to redirect to the product link
                del bigboxes[0:3] # the first 3 members of the list do not contain relevant information, hence deleting them.
                box = bigboxes[0] #  taking the first iteration (for demo)
                productLink = "https://www.flipkart.com" + box.div.div.a['href'] # extracting the actual product link
                prodRes = requests.get(productLink) # getting the product page from server
                prod_html = bs(prodRes.text, "html.parser") # parsing the product page as HTML
                allreviews = prod_html.find_all('div', {'class': "col JOpGWq"}) # finding the HTML section containing the customer comments
                allreviews_link=  allreviews[0].find_all('a')[0]['href']
                table = db[searchString]  # creating a collection with the same name as search string. Tables an

                reviews = []  # initializing an empty list for reviews
                while review_count < 25:

                    allreviews_link = "https://www.flipkart.com"  + allreviews_link
                    allReviews = requests.get(allreviews_link)  #Get the Allreviews page
                    reviews_html = bs(allReviews.text, "html.parser")

                    if review_count == 0:  #for the first page, we need to get the 'overall' tab
                        tabs = reviews_html.find_all('div', {'class': "_33iqLu"})
                        all_reviews_link = tabs[0].div.a['href']
                        all_reviews_link = "https://www.flipkart.com" + all_reviews_link
                        allReviews = requests.get(all_reviews_link)  # Get the Allreviews page
                        reviews_html = bs(allReviews.text, "html.parser")

                    commentboxes = reviews_html.find_all('div', {'class': "_1AtVbE col-12-12"})  #the customer comments




                    #  iterating over the comment section to get the details of customer and their comments
                    for commentbox in commentboxes[4:-1]:
                        try:
                            name = commentbox.find_all('p', {'class':'_2sc7ZR _2V5EHH'})[0].text

                        except:
                            name = 'No Name'

                        try:
                            rating = commentbox.div.div.div.div.div.text

                        except:
                            rating = 'No Rating'

                        try:
                            commentHead = commentbox.div.div.div.p.text
                        except:
                            commentHead = 'No Comment Heading'
                        try:
                            comtag = commentbox.div.div.find_all('div', {'class': ''})
                            custComment = comtag[0].div.text
                        except:
                            custComment = 'No Customer Comment'
                        #fw.write(searchString+","+name.replace(",", ":")+","+rating + "," + commentHead.replace(",", ":") + "," + custComment.replace(",", ":") + "\n")
                        mydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead,
                                  "Comment": custComment} # saving that detail to a dictionary
                        x = table.insert_one(mydict) #insertig the dictionary containing the rview comments to the collection
                        reviews.append(mydict) #  appending the comments to the review list

                        review_count += 1
                    nextlink = commentboxes[-1]
                    allreviews_link = nextlink.find_all('a', {'class': '_1LKTO3'})[-1]['href']

                return render_template('results.html', reviews=reviews) # showing the review to the user
        except:
            return 'something is wrong'
            #return render_template('results.html')
    else:
        return render_template('index1.html')
if __name__ == "__main__":
    app.run(port=8000,debug=True) # running the app on the local machine on port 8000