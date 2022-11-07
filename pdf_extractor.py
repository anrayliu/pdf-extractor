'''
Anray Liu (high school co op student)
Nov 2 2022
Used to extract fields and values from a pdf into a csv file
'''

import sys #exit
import os #listdir, path.join, abspath
import csv #writer, QUOTE_ALL
from PyPDF2 import PdfReader
from types import SimpleNamespace as Ns

def read_pdf(path, fields):
    reader = PdfReader(path)

    '''
    joins the text from each page into one string
    the format of the text is unknown, since structure depends on how the pdf was made
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
    the code below aims to organize the format so each field and value are on seperate lines
    it finds each field and adds new line characters (\n) before and after the field if needed
    the code is able to find duplicate fields as long as the fields are given in order
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
    
        if text[index - 1] != "\n":
            text = text[:index] + "\n" + text[index:]
            index += 1
        index += len(field)
        if text[index] != "\n":
            text = text[:index] + "\n" + text[index:]
            index += 1

        i = index


    #goes through the text and if a field is found, its value on the next line is written down
        
    values = []
    line_gen = enumerate(text.split("\n"))
    for i, line in line_gen:
        if line in fields:
            values.append(next(line_gen)[1].strip())
            

    return values


#ns argument is only used to communicate with the gui when function is run from a thread
#if gui.py is not being used, ignore ns

def create_csv(input_path, output_path, fields, ns=Ns(percent=0, request_stop=False, stopped=False)):
    print("Input Path: {}".format(os.path.abspath(input_path)))
    print("Output Path: {}".format(os.path.abspath(output_path)))

    try:
        with open(output_path, "w") as file:
            pass
    except IOError:
        print('"output.csv" being used. Please close it and try again.')
        ns.stopped = True
        return
    
    #creates csv file (output_path)
    with open(output_path, "w", newline="") as file:
        writer = csv.writer(file, quoting=csv.QUOTE_ALL)
        writer.writerow(["File Name"] + fields)

        #identifies number of pdfs in given folder (input_path)

        pdfs = [file for file in os.listdir(input_path) if file.endswith(".pdf")]
        print(f"Discovered {len(pdfs)} pdfs.")

        #adds each pdf with all values as a row to the csv
        
        for i, file in enumerate(pdfs):
            print(f'Reading "{file}"')
                
            values = read_pdf(os.path.join(input_path, file), fields)
            writer.writerow([file] + values)

            ns.percent = (i + 1) / len(pdfs)
            if ns.request_stop:
                ns.stopped = True
                print("Stopped.")
                return

        print("Done!")


if __name__ == "__main__":
    
    fields = []
    
    create_csv("pdfs", "output.csv", fields)
    input()
