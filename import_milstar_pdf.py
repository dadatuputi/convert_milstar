import PyPDF4
import argparse
import re
import csv
import datetime

regex_transaction = r"(?P<Date>[\d]{1,2}\s[\w]+\s[\d]{4})[\n](?P<Memo>[ \.\w]+?)[\n](?P<Ref>[\d\s]+)[\n](?P<Payee>[\w ]+)[\n](?P<Outflow>[-]*[$\.\d]+)"

# Pull transactions from text
def get_transactions(text):
    matches = re.finditer(regex_transaction, text, re.MULTILINE)
    _transactions = [match.groupdict() for match in matches]
    for _transaction in _transactions:
        _transaction['Memo'] = "{}: {}".format(_transaction['Memo'], _transaction.pop('Ref'))
        _transaction['Date'] = datetime.datetime.strptime(_transaction['Date'], "%d %b %Y").strftime("%Y/%m/%d")
    return _transactions
    

# Get input and output file as arguments
parser = argparse.ArgumentParser(description="Import transactions from Military Star Card MyECP Statement PDF into YNAB CSV file")
parser.add_argument('pdf', help="PDF Statement to import")
parser.add_argument('-o', '--output', default="out.csv", help="CSV Filename to write to")
args = parser.parse_args()

# Open PDF
with open(args.pdf, 'rb') as pdf_file:
    pdf = PyPDF4.PdfFileReader(pdf_file)

    # Get text from each page and pass to regex parser
    transactions = []
    for page in pdf.pages:
        transactions.extend(get_transactions(page.extractText()))

with open(args.output, 'w', newline='') as csv_file:
    writer = csv.DictWriter(csv_file, transactions[0].keys())
    writer.writeheader()
    writer.writerows(transactions)
