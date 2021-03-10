import camelot
import wget
import numpy as np
import pandas as pd

# the URL for the Tenaris catalogue so I can claim I'm not copying anything
url = 'https://www.tenaris.com/media/isfmuyog/tenarishydril-premium-connections-catalog.pdf'
file = wget.download(url)

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

def main():
    # initiate our catalogue dictionary
    catalogue = {}

    # loop over out template dictionary we made with the table headers
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
        # filer them out of the data
        mask = np.all(np.isnan(filtered_data), axis=1)
        catalogue[k] = np.vstack(np.array(filtered_data)[~mask])

    return catalogue

if __name__ == '__main__':
    catalogue = main()

print("Done")
