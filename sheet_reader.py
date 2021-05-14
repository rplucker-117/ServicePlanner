import ezodf
import pprint
from logzero import logger

class ReadSheet:
    def __init__(self, spreadsheet_path):
        self.sheet_path = spreadsheet_path
        self.spreadsheet = ezodf.opendoc(self.sheet_path)
        logger.debug('Opening spreadsheet %s', self.sheet_path)

    def read_cc_sheet(self):
        # Numberical input = [COLUMN, ROW]
        # Returns dict of CC names in format:
        # {
        #     'bank1: [cc1 name, cc2 name, etc],
        #       ...
        #     'bank8: [cc1 name, cc2 name, etc],
        # }
        # from a specified spreadsheet in .ods format. Use carbonite_cc_name_template.ods.

        logger.debug('Reading rosstalk custom control spreadsheet: %s', self.sheet_path)
        sheet = self.spreadsheet.sheets['Sheet1']

        cc_data = {}

        banks = 8
        for bank in range(1, banks+1):
            bank_name = 'bank' + str(bank)
            bank_data = []
            for cc in range(1, 33):
                bank_data.append(sheet[cc, bank].value)

            cc_data.update({bank_name: bank_data})
        logger.debug('Got sheet data: %s', cc_data)
        return cc_data

# if __name__ == '__main__':
#     sheet = read_sheet(spreadsheet_path='flowood.ods')
#     sheet.read_cc_sheet()
