'''
1. extracts all the text from a pdf
2. formats the text to seperate fields and values
3. writes data to a csv file

Note:
The structure of PDFs can vary depending on how it was made,
which means this script won't work for all PDFs.
'''


import sys
import os
import csv
from PyPDF2 import PdfReader


# loads fields from a text file (fields are seperated with a new line)

def load_fields(path):
    with open(path, "r") as file:
        return [line.strip("\n") for line in file.readlines()]

# extracts and formats text

def read_pdf(path, fields):
    reader = PdfReader(path)

    '''
    joins the text from each page into one string
    the format of the text is unknown, since structure depends on the pdf
    
    example format:

    field value
    field value
    field value
    '''
    
    text = "\n".join(page.extract_text() for page in reader.pages)
    if text.strip() == "":
        print("Empty pdf.")
        return []

    '''
    the code below reorganizes the text so each field and value are on seperate lines
    it finds each field and adds new line characters (\n) before and after the field if needed
    the code is able to find duplicate fields as long as the user inputs EVERY field in ORDER
    
    new format:

    field
    value
    field
    value
    field
    value
    '''
    
    i = 0
    for field in fields:
        index = text.find(field, i)
        if index == -1:
            print(f'Missing field: {field} - this may affect extraction accuracy.')
            continue

        # if extractor isn't working, try the following
        # remove the "if" lines and unindent the code inside
    
        if text[index - 1] != "\n":
            text = text[:index] + "\n" + text[index:]
            index += 1
        index += len(field)
        if text[index] != "\n":
            text = text[:index] + "\n" + text[index:]
            index += 1

        i = index

    # goes through the text and if a field is found, its value on the next line is written down
        
    values = []
    line_gen = enumerate(text.split("\n"))
    for i, line in line_gen:
        if line in fields:
            values.append(next(line_gen)[1].strip())
            
    return values

# comm is only used to communicate with the gui
# if gui.py is not being used, comm is redundant

def create_csv(input_path, output_path, fields, comm=None):
    print("Input Path: {}".format(os.path.abspath(input_path)))
    print("Output Path: {}".format(os.path.abspath(output_path)))

    try:
        with open(output_path, "w") as file:
            pass
    except IOError:
        print('"output.csv" being used. Please close it and try again.')
        return

    # creates output file and reads through all the pdfs
        
    with open(output_path, "w", newline="") as file:
        writer = csv.writer(file, quoting=csv.QUOTE_ALL)
        writer.writerow(["File Name"] + fields)

        pdfs = [file for file in os.listdir(input_path) if file.endswith(".pdf")]
        print("Discovered {} pdfs.".format(len(pdfs)))
        
        for i, file in enumerate(pdfs):
            print(f'Reading "{file}"')
                
            values = read_pdf(os.path.join(input_path, file), fields)
            writer.writerow([file] + values)

            # this code is necessary for the gui - avoid changing
            
            if comm is not None:
                comm["percent"] = (i + 1) / len(pdfs)
                if comm["stop"]:
                    print("Stopped.")
                    return

        print("Done!")


if __name__ == "__main__":
    
    create_csv("pdfs", "output.csv", [])
    
    input()
