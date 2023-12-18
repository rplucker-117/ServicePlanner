import ezodf
import pprint
from logzero import logger

class ReadSheet:
    def __init__(self, spreadsheet_path):
        self.sheet_path = spreadsheet_path
        self.spreadsheet = None
        # logger.debug('Opening spreadsheet %s', self.sheet_path)

    def read_cc_sheet(self):
        # Numberical input = [COLUMN, ROW]
        # Returns dict of CC names in format:
        # {
        #     'bank1: [cc1 name, cc2 name, etc],
        #       ...
        #     'bank8: [cc1 name, cc2 name, etc],
        # }
        # from a specified spreadsheet in .ods format. Use carbonite_cc_name_template.ods.

        self.spreadsheet = ezodf.opendoc(self.sheet_path)
        sheet = self.spreadsheet.sheets['Sheet1']

        cc_data = {}

        banks = 8
        for bank in range(1, banks+1):
            bank_name = 'bank' + str(bank)
            bank_data = []
            for cc in range(1, 33):
                bank_data.append(sheet[cc, bank].value)

            cc_data.update({bank_name: bank_data})
        # logger.debug('Got sheet data: %s', cc_data)
        return cc_data

    def read_lbl_file(self):  # reads a nk .lbl sheet, outputs a dict>list containing names of each input/output
        inputs = []
        outputs = []

        with open(self.sheet_path) as f:
            for line in f.readlines():
                outputs.append(line.split(',')[1])  # outputs
                inputs.append(line.split(',')[3])  # inputs

        io = {
            'inputs': inputs,
            'outputs': outputs
        }

        return io

if __name__ == '__main__':
    pprint.pprint(ReadSheet('2021_05_11.lbl').read_lbl_file())
