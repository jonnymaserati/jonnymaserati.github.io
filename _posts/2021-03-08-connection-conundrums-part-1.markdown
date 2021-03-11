---
layout: post
title:  "Connection Conundrums - Part 1"
tags: python wells drilling casing connections engineering data
---
Recently, I had the fortune of working on a complex deep water well that required many casing liners (including expandable liners) to deliver the well objectives. With such tight clearances, finding suitable casing connections was a challenge and many hours were spent searching and downloading connection specification data sheets and updating WellCat model casing and Connection Utilization Envelope (CUE) data.

## There must be a better way
Frustrated, I turned to Python, my go to problem solving companion. With the help of a couple of colleagues who already had the casing and connection data in a convenient format, I was able to generate all of the casing permutations that were feasible with the client's approved list of casing connections. Investing a couple of hours writing some code saved me many hours of laborious work checking dimensions, calculating clearances and manually inputting data into well design software.

In this post, I'll step through a similar work flow and demonstrate how truly amazing Wells and Drilling Engineers in the Oil and Gas industry are for being able to manage such large option spaces in their heads.

## *Acquiring* some data
The data I used previously was proprietary, so the first step is getting some suitable new data that I can use for this exercise.

> casing connections manufacturers, please allow us to download your data in a more useable format. You'll thank us for it.

Most connections manufacturers have the facility for downloading connection data from their websites, but this is a laborious process. I started writing some code to automate this, but automating selections from drop down menus is error prone and slow. I gave up.

Instead, I wrote some code to scrape data from the the [Tenaris Premium Connections Catalogue](https://www.tenaris.com/media/isfmuyog/tenarishydril-premium-connections-catalog.pdf) using the [camelot-py](https://pypi.org/project/camelot-py/) library. Unfortunately, the data tables in the catalogue can't be read without a degree of fettling and rather than spend hours learning camelot's attributes, I manually cleaned up the data.

Let's start with importing the data. For this workflow we'll first need some libraries imported and while we're at it let's set the URL to the online Tenaris catalogue and download it.

```python
import camelot
import wget
import numpy as np

# the URL for the Tenaris catalogue so I can claim I'm not copying anything
url = 'https://www.tenaris.com/media/isfmuyog/tenarishydril-premium-connections-catalog.pdf'
file = wget.download(url)

```
## Importing some data
We now have the catalogue downloaded and accessible through the file variable. Next we'll write a function for extracting tables from specific pages in a pdf document. This is written as a function as we may wish to call it several times for different connections, especially if the tables are not consistent throughout the document.

```python
def import_tables(file, pages):
    """
    Function for extracting table data from a pdf file.

    Parameters
    ----------
    file: string
        The variable name or the path and filename of the pdf.
    pages: string
        The pages in the pdf where the tables are located, e.g. '1, 2, 3' or
        '1-3'.
    
    Returns
    -------
    tables: TableList object
    
    """
    tables = camelot.read_pdf(
        file, pages=pages,
        flavor='stream',
    )
    return tables

```
## Processing the data
It's time to process the data in the tables. To do this, we'll write a function that reads each line from the table, cleans it up into a common length array and appends the array to a list. Because this is the oilfield, we have to deal with fractions and need to write a function for interpreting a fraction and converting it to a float.

First let's write that function for handling fractions, since this is a helper function to our data extraction function.

```python
def convert_to_float(frac_str):
    """
    It wouldn't be the oilfield without a healthy mix of units and fractions.
    This function attempts to deal with fractions care of someone on stack
    overflow (thank you).

    Parameters
    ----------
    frac_str: string

    Returns
    -------
    result: float

    Exceptions
    ----------
    ValueError: if the string is not a number or a fraction
    """
    try:
        return float(frac_str)
    except ValueError:
        num, denom = frac_str.split('/')
        try:
            leading, num = num.split(' ')
            whole = float(leading)
        except ValueError:
            whole = 0
        frac = float(num) / float(denom)
        result = whole - frac if whole < 0 else whole + frac

        return result
```
And now the data extraction function.

```python
def extract_data(table, start_row=1, end_row=None):
    """
    This is where the real fun starts. I'm not proud of this processing
    workflow, but it works and cost me less time than arseing about with
    camelot's settings, especially since there's subtle differences between
    the tables in Tenaris' catalogue.

    Parameters
    ----------
    table: TableList object
    start_row: int
        If you're confident that the table header is a specific number of rows
        then enter that here and skip these rows.
    end_row: int or None
        If you only want to read a finite number of rows. The default 'None'
        reads them all.
    
    Returns
    -------
    datas: list of (n, m) arrays

    """
    # Define a list of characters in the table that we want to ignore
    characters = ['(', ')', '*']

    datas = []
    skip_header = True
    for i, row in enumerate(table.data[start_row:end_row]):
        if skip_header:
            # Read the first item of each row to determine if we're passed the
            # header and into the table data. We know the first row of data
            # begins with a number (or a fraction).
            try:
                convert_to_float(row[0])
            except ValueError:
                continue
        skip_header = False
        data = []
        for j, item in enumerate(row):
            # We don't want new line characters
            if '\n' in item:
                item = item.split('\n')[-1]
            # Skip and unwanted characters
            if any(c in item for c in characters):
                continue
            # Manage blank data - there's rogue columns in the read data
            if item == '':
                if j == 0:
                    data.append(datas[-1][j])
                else:
                    continue
            # If it's a number add to the data, otherwise add a NaN
            else:
                try:
                    data.append(
                        convert_to_float(item)
                    )
                except ValueError:
                    data.append(np.nan)
        # Remove and rows of NaNs
        if np.all(np.isnan(np.array(data)[1:])):
            continue
        else:
            datas.append(data)
    return datas
```
## Applying a template
Before we write our main function, we're going to create a dictionary of table headers. This isn't ideal, but having reviewed the connections catalogue, the table headers have differences between the connections and I'd rather state these explicitly than rely on code to interpret them. Sometimes you just have to pull your sleeves up and get dirty.

We'll structure the dictionary with the connection name as the main key followed by the page numbers in the catalogue where the associated tables are located. We'll then add a `headers` key where we'll list, in the correct order, the table headers we will assign to our imported data.

Creating the dictionary in this way means we can have an entry for each connection and loop over this dictionary in our main function.

Here's the dictionary, called `template` with an entry for the `Wedge 521` connection.

```python
# I'm not proud of manually typing these headers - and if this must
# be done it'd be better to place all this inside a yaml file and import it
# but I struggled to get camelot to interpret these
template = {
    'Wedge 521': {
        'pages': '49, 50',
        'connection_type': 'threaded',
        'headers': [
            'size', 'nominal_weight',
            'pipe_body_wall_thickness', 'pipe_body_inside_diameter',
            'pipe_body_drift', 'box_outside_diameter',
            'connection_inside_diameter', 'make_up_loss',
            'critical_section_area', 'tensile_efficiency',
            'compression_efficiency',
            'joint_yield_55', 'joint_yield_80', 'joint_yield_90',
            'joint_yield_95', 'joint_yield_110', 'joint_yield_125',
        ]
    }
}
```
So now it's time for our main function. It's good practice to write your main code inside a function since it can help with debugging and you can then do some performance checking easier.
## Tying together our code

```python
def main():
    # initiate our catalogue dictionary
    catalogue = {}

    # loop over our template dictionary we made with the table headers
    for k, v in template.items():
        # import the data
        data = []
        temp = import_tables(file, pages=v['pages'])
        # process the data
        for t in temp:
            data.extend(extract_data(t))
        # some of the data might not import correctly - for now we're just
        # going to ignore these rows (which may be longer or shorter)
        length = [len(l) for l in data]
        filtered_data = [
            d for d in data
            if len(d) == max(set(length), key=length.count)
        ]
        # just in case some rows with NaNs imported, we'll mask them off and
        # filter them out of the data
        mask = np.all(np.isnan(filtered_data), axis=1)
        catalogue[k] = np.vstack(np.array(filtered_data)[~mask])

    return catalogue
```
We're now ready to run it. This is done adding the following lines at the bottom of your script. I commonly add a simple `print` statement more to help me with debugging as it gives me somewhere to place a breakpoint in my editor.

## Running the code
```python
if __name__ == '__main__':
    catalogue = main()

print("Done")
```
Congratulations, we've just imported the data from the Tenaris Premium Connections catalogue for the Wedge 521 connection.
## Results
If you want to QAQC the data you can do so with the help of [pandas](https://pandas.pydata.org/), creating a `DataFrame` with the following line of code:

```python
df = pd.DataFrame(catalogue['Wedge 521'], columns=template['Wedge 521']['headers'])
```
Below is the first five rows of our freshly imported data, created with the help of [tabulate](https://pypi.org/project/tabulate/), a dependency that assists `pandas` to nicely format the table in markdown:

```python
print(df.head().to_markdown())
```

|    |   size |   nominal_weight |   pipe_body_wall_thickness |   pipe_body_inside_diameter |   pipe_body_drift |   box_outside_diameter |   connection_inside_diameter |   make_up_loss |   critical_section_area |   tensile_efficiency |   compression_efficiency |   joint_yield_55 |   joint_yield_80 |   joint_yield_90 |   joint_yield_95 |   joint_yield_110 |   joint_yield_125 |
|---:|-------:|-----------------:|---------------------------:|----------------------------:|------------------:|-----------------------:|-----------------------------:|---------------:|------------------------:|---------------------:|-------------------------:|-----------------:|-----------------:|-----------------:|-----------------:|------------------:|------------------:|
|  0 |    4   |              9.5 |                      0.226 |                       3.548 |             3.423 |                  4.103 |                        3.457 |           3.62 |                   1.646 |                 61.4 |                     83.6 |               91 |              132 |              148 |              156 |               181 |               206 |
|  1 |    4   |             11   |                      0.262 |                       3.476 |             3.351 |                  4.162 |                        3.401 |           3.62 |                   2.029 |                 66   |                     85.9 |              112 |              162 |              183 |              193 |               223 |               254 |
|  2 |    4   |             11.6 |                      0.286 |                       3.428 |             3.303 |                  4.2   |                        3.353 |           3.62 |                   2.284 |                 68.4 |                     86.9 |              126 |              183 |              205 |              217 |               251 |               285 |
|  3 |    4.5 |              9.5 |                      0.205 |                       4.09  |             3.965 |                  4.629 |                        4.04  |           2.74 |                   1.678 |                 60.7 |                     76.8 |               92 |              134 |              151 |              160 |               185 |               210 |
|  4 |    4.5 |             10.5 |                      0.224 |                       4.052 |             3.927 |                  4.651 |                        3.976 |           3.62 |                   1.821 |                 60.5 |                     82.6 |              100 |              146 |              164 |              173 |               200 |               228 |

Now that we have some data, in the next post we'll use it to determine how many permutations of casing design exist!

Feel free to [download the code](/assets/code/import_connections_from_tenaris_catalogue.py).