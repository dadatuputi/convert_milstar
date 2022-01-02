import PyPDF4
import argparse
import re
import csv
import datetime

# Use https://regex101.com/
regex_transactions = r"Transactions\nDate\nDescription\nReference #\nLocation\nAmount\n(?P<Transactions>.*?)\n ?\n"
regex_transaction = r"(?P<Date>\d{1,2}\s\w+\s\d{4})\n(?P<Memo>Charge|Return|ACH Online Pymt)\n(?P<Ref>[\d ]+)?\n?(?P<Payee>[\w\. ]+)\n(?P<Outflow>-{0,1}[$\.\d]+)"

regex_fees = r"Fees\nDate\nDescription\nAmount\n(?P<Fees>.*)Total Fees for This Period"
regex_fee = r"(?P<Date>\d{1,2}\s\w+\s\d{4})\n(?P<Memo>.+?)\n(?P<Outflow>-{0,1}[$\.\d]+)"

# Pull transactions from PDF text
def get_transactions(text):
    transactions = []

    # Transactions
    # Get transaction lists first
    transaction_list_matches = re.finditer(regex_transactions, text, re.DOTALL | re.MULTILINE)
    for transaction_list_match in transaction_list_matches:
        transaction_list_text = transaction_list_match.groupdict()['Transactions']
        # Get all individual transactions out of the transaction list
        transaction_group_match = re.finditer(regex_transaction, transaction_list_text, re.DOTALL | re.MULTILINE)
        transactions.extend([match.groupdict() for match in transaction_group_match])

    # Fees
    # Get fee lists first
    fee_str = ""
    fee_list_matches = re.finditer(regex_fees, text, re.DOTALL | re.MULTILINE)
    for fee_list_match in fee_list_matches:
        fee_list_text = fee_list_match.groupdict()['Fees']
        # Get any individual fees out of fee list
        fee_group_match = re.finditer(regex_fee, fee_list_text, re.DOTALL | re.MULTILINE)
        fees = [match.groupdict() for match in fee_group_match]
        for fee in fees:
            fee['Payee'] = 'MilitaryStar Card Fee'
            fee['Ref'] = None
        transactions.extend(fees)
        fee_str = " ({} fee)".format(len(fees))

    print("Imported {} transactions{}".format(len(transactions), fee_str))

    # Fix the memo and date 
    for transaction in transactions:
        ref_str = ": {}".format(transaction['Ref'])
        if not transaction.pop('Ref'):
            ref_str = ""
        transaction['Memo'] = "{}{}".format(transaction['Memo'], ref_str)
        transaction['Date'] = datetime.datetime.strptime(transaction['Date'], "%d %b %Y").strftime("%Y/%m/%d")
    
    return transactions

# Get input and output file as arguments
parser = argparse.ArgumentParser(description="Import transactions from Military Star Card MyECP Statement PDF into YNAB CSV file")
parser.add_argument('pdf', help="PDF Statement to import")
parser.add_argument('-o', '--output', default="out.csv", help="CSV Filename to write to")
parser.add_argument('-d', '--debug', help="Debug by printing out text of supplied PDF", action='store_true')
args = parser.parse_args()

# Open PDF
with open(args.pdf, 'rb') as pdf_file:
    pdf = PyPDF4.PdfFileReader(pdf_file)

    # Get text from each page and pass to regex parser
    text = ''.join([page.extractText() for page in pdf.pages])
    transactions = get_transactions(text)
    if args.debug:
        print(text)

    if transactions:
        print("Writing {} transactions to {}".format(len(transactions), args.output))
        with open(args.output, 'w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, transactions[0].keys())
            writer.writeheader()
            writer.writerows(transactions)
    else:
        print("No transactions found in PDF")