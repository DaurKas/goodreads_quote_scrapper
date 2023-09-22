import requests
import csv
import json
from bs4 import BeautifulSoup
from time import sleep
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def get_page_text(url :str) -> str:
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    response = session.get(url)
    return response.text

def get_book_page_link(title: str) -> str:
    request_link = f'https://www.goodreads.com/search?q={title}'
    soup = BeautifulSoup(get_page_text(request_link), features="html.parser")
    table = soup.find('table', class_ = 'tableList')
    while(table == None):
        print("failed to find book link, will retry")
        soup = BeautifulSoup(get_page_text(request_link), features="html.parser")
        table = soup.find('table', class_ = 'tableList')
        sleep(1)
    book_title = table.find('a', class_="bookTitle")
    link = 'https://www.goodreads.com' + book_title['href']
    return link

def get_book_quotes_link(ref: str) -> str:
    text = get_page_text(ref)
    soup = BeautifulSoup(text, features="html.parser")
    discussion_card = (soup.find('a', class_ = 'DiscussionCard'))
    try_number = 0
    while(discussion_card == None):
        print("failed to find quote link, will retry")
        text = get_page_text(ref)
        soup = BeautifulSoup(text, features="html.parser")
        discussion_card = (soup.find('a', class_ = 'DiscussionCard'))
        sleep(1)
    link = discussion_card['href']
    return link

def get_book_id(ref: str) -> str:
    index = ref.find('show/')
    index += len('show/')
    dot_index = ref.find('.', index, len(ref) - 1)
    return ref[index:dot_index]

def read_book_list(filename :str):
    books = []
    with open(filename, newline='',encoding="utf8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            book = []
            book.append(row['book_title'])
            book.append(row['author'])
            books.append(book)

    return books

def get_book_quotes(ref :str, max_num_of_quotes = 1) -> list[str]:
    soup = BeautifulSoup(get_page_text(ref), features="html.parser")
    current_page_quotes = soup.findAll('div', class_ = 'quotes')
    quotes = []
    #for some reason on quotes page exist two quotes objects
    #first contains first quote, second contains others
    if len(current_page_quotes) <= 1:
        return quotes

    first_quote = current_page_quotes[0].find('div', class_= 'quoteText')
    quotes.append(first_quote.text.strip())
    other_quotes = current_page_quotes[1].findAll('div', class_= 'quoteText')
    for quote in other_quotes:
        raw_text = str(quote.text.strip())
        quote_text = raw_text.split('\n')[0]
        quotes.append(quote_text)
    
    return quotes

def get_book_info(book_name :str, author_name :str):
    book_page_link = get_book_page_link(book_name)
    book_quotes_link = get_book_quotes_link(book_page_link)
    print(book_page_link, "    ", book_quotes_link)
    book_id = get_book_id(book_page_link)
    book_quotes = get_book_quotes(book_quotes_link)
    dictionary = {
        "book_name" : book_name,
        "author_name" : author_name,
        "book_id" : book_id,
        "goodreads_link" : book_page_link,
        "goodreads_guotes_link" : book_quotes_link,
        "book_quotes" : book_quotes
    }
    return dictionary

def main():

    books_list = read_book_list("mybooks.csv")
    outfile = open("books.json", "w")    
    books = []
    for book in books_list:
        book_info = get_book_info(book[0], book[1])
        json_object = json.dumps(book_info, indent=4)
        books.append(json_object)

    books_dict = {
        "books" : books
    }
    json_object = json.dumps(books_dict, indent=4)
    outfile.write(json_object)
    outfile.close()
    return

if __name__ == '__main__':
    main()

# DiscussionCard - class of the ref to the quotes page
# https://www.goodreads.com/search?q={insert here name of the book from the list} - link for the search