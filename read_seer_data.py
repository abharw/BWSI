import pandas as pd
from os import path
import csv
import numpy as np
from time import time
import re


class SEER_reader:

    def load_seer(self, seer_file):

        # open and read the file containing the data
        csvfile = open(seer_file)
        reader = csv.reader(csvfile)

        print('Reading data file... this may take ~30 seconds...')
        tstart = time()
        rows_list = []

        for line in reader:
            dict1 = {}
            for key, vals in self.records.items():
                entry = line[0][vals['ix'][0]:vals['ix'][1]]

                # Most values are integer values, but some may not be
                try:
                    dict1.update({key: int(entry)})
                except ValueError:
                    if entry.strip():
                        # Some entries are strings; keep those as-is
                        dict1.update({key: entry})
                    else:
                        # Empty strings should be treated as null values
                        dict1.update({key: None})
                except Exception as e:
                    print('Exception: {}'.format(e))
                    print('Skipping row...')
                    break

            rows_list.append(dict1)

        # create a pandas DataFrame from the list
        self.table = pd.DataFrame(rows_list)

        # delete stuff we don't need anymore
        csvfile.close()
        del rows_list

        print('Loading data took {:.1f} seconds\n\n'.format(time() - tstart))

        return self.table



    def filter_table_mod4(self):
        """
        This method filters the SEER dataframe to include only the data needed for Medlytics Module 4 homework.
        
        We will filter and stratify our data to mimic the analysis in "Breast Cancer Stage Variation and Survival in  
        Association With Insurance Status and Sociodemographic Factors in US Women 18 to 64 Years Old" by Hsu, et. al (2017). 
        Link to Full Paper: http://rdcu.be/Gdvp/
        :return: 
        """
        print('Filtering data on gender, age, year of diagnosis, ...\n')

        print('There are {} entries in our table.'.format(len(self.table.index)))

        # Filter for women only
        self.table = self.table[(self.table['Sex'] == 2)]
        print('There are {} women in our table.'.format(len(self.table.index)))

        # Filter by year of diagnosis
        self.table = self.table[(self.table['Year of diagnosis'] >= 2007) & (self.table['Year of diagnosis'] <= 2008)]
        print('There are {} diagnoses in 2007-2008.'.format(len(self.table.index)))

        # Filter by age
        self.table = self.table[(self.table['Age at diagnosis'] >= 18) & (self.table['Age at diagnosis'] <= 64)]
        print('There are {} diagnoses between the age of 18-64.'.format(len(self.table.index)))

        # Filter by AJCC 6th Stage excluded
        self.table = self.table[self.table['Breast Adjusted AJCC 6th Stage'] > 0]
        print('There are {} diagnoses with AJCC 6th Stage > 0.'.format(len(self.table.index)))

        # Filter by known survival time
        self.table = self.table[self.table['Survival months'] <= 60]
        print('There are {} diagnoses whose survival time is less than or equal to 60 months.'.format(len(self.table.index)))

        # Check to make sure we don't still have rows with missing data (if so, drop them)
        self.table = self.table.dropna()

        return self.table



    def encode_data_mod4(self):

        '''
        Encode cancer stages: The variable "breast adjusted AJCC 6th stage(1988)" was categorized as early-stage 
        (American Joint Committee on Cancer stage I, IIA, IIB, or IIIA) or late-stage (IIIB, IIIC, or IV).
        '''

        # Encode Early/Late-Stage

        print('\nAdding new columns for cancer stage, hormone reception, ... \n')

        early_codes = ['I', 'IIA', 'IIB', 'IIIA']
        late_codes = ['IIIB', 'IIIC', 'IV']

        record_lbl = 'Breast Adjusted AJCC 6th Stage'
        new_label = 'Early Late Stage'

        self.records[new_label] = {'codes': {1: 'early', 2: 'late'}}
        self.table[new_label] = np.nan

        idx = pd.IndexSlice

        for codekey in self.records[record_lbl]['codes']:

            mask = self.table.loc[:, idx[record_lbl]] == codekey
            if (self.records[record_lbl]['codes'][codekey] in early_codes):
                self.table.loc[mask, new_label] = 1
            elif (self.records[record_lbl]['codes'][codekey] in late_codes):
                self.table.loc[mask, new_label] = 2


        # Encode cancer stage (I, II, III, or IV)

        record_lbl = 'Breast Adjusted AJCC 6th Stage'
        new_label = 'Cancer Stage Num'

        self.records[new_label] = {'codes': {1: 'I', 2: 'II', 3: 'III', 4: 'IV'}}
        self.table[new_label] = np.nan

        idx = pd.IndexSlice

        reIV = re.compile('IV.*')
        reIII = re.compile('III.*')
        reII = re.compile('II.*')
        reI = re.compile('I.*')

        for codekey in self.records[record_lbl]['codes']:

            mask = self.table.loc[:, idx[record_lbl]] == codekey
            stage_code = self.records[record_lbl]['codes'][codekey]

            if (reIV.match(stage_code)):
                self.table.loc[mask, new_label] = 4
            elif (reIII.match(stage_code)):
                self.table.loc[mask, new_label] = 3
            elif (reII.match(stage_code)):
                self.table.loc[mask, new_label] = 2
            elif (reI.match(stage_code)):
                self.table.loc[mask, new_label] = 1


        '''
        Encode hormone receptor positive/negative: We classified individuals as having hormone receptor-positive or 
        hormone receptor–negative breast cancer according to Howlander et al, using the variables "ER status recode 
        breast cancer" and "PR status recode breast cancer."

        Cases recorded as having estrogen receptor(ER)-positive/progesterone receptor (PR)-positive, 
        ER-positive/PR-negative, or ER-negative/PR-positive breast cancer were classified as hormone receptor–positive, 
        whereas those recorded as having ER-negative/PR-negative breast cancer were classified as hormone 
        receptor–negative. Cases recorded as having a borderline ER-positive or PR-positive status were classified as 
        hormone receptor–positive.
        '''

        ER_label = 'ER Status Recode Breast Cancer'
        PR_label = 'PR Status Recode Breast Cancer'
        new_label = 'Hormone Receptor'

        self.records[new_label] = {'codes': {1: 'positive', 2: 'negative'}}
        self.table[new_label] = np.nan

        mask = (self.table[ER_label] == 1) | (self.table[PR_label] == 1) | (self.table[ER_label] == 3) | (self.table[PR_label] == 3)
        self.table.loc[mask, new_label] = 1

        mask = (self.table[ER_label] == 2) & (self.table[PR_label] == 2)
        self.table.loc[mask, new_label] = 2


        '''
        Encode dichotomized marital status and age: The variables "marital status" and "age at diagnosis" were 
        dichotomized as single (single, separated/divorced/unmarried, or widowed) or married and as younger 
        (18-39 years) or older (40-64 years)
        '''

        marital_label = 'Marital Status at DX'
        new_label = 'Marital Group'

        self.records[new_label] = {'codes': {1: 'single', 2: 'married'}}
        self.table[new_label] = np.nan

        mask = (self.table[marital_label] < 9)
        self.table.loc[mask, new_label] = 1

        mask = (self.table[marital_label] == 2)
        self.table.loc[mask, new_label] = 2

        age_label = 'Age at diagnosis'
        new_label = 'Age Group'

        self.records[new_label] = {'codes': {1: 'younger', 2: 'older'}}
        self.table[new_label] = np.nan

        mask = (self.table[age_label] < 40)
        self.table.loc[mask, new_label] = 1

        mask = (self.table[age_label] >= 40)
        self.table.loc[mask, new_label] = 2

        return self.table



    def dropna(self):
        self.table = self.table.dropna(axis=0, how='any')
        return self.table



    def get_table(self):
        return self.table



    def get_records(self):
        """
        records_dict = {...} is a dictionary which stores information about where in the text file certain fields are 
        stored, as well as what the field codes mean. This schema is based on the November 2016 Submission of the SEER  
        Research Data Record. To ensure this will work with other submissions (or to fix accordingly), visit: 
        https://seer.cancer.gov/data/documentation.html

        The ix values correspond to the string slice indices for each field. Note that these follow python slicing 
        syntax: [min,max] where min is inclusive and max is exclusive. For example, ix:[20,21] corresponds to 
        position 20 only. Note that the positions provided in the SEER documentation start at 1, whereas python indices 
        start at 0.
        """

        return self.records


    def __init__(self):

        self.records = {'Patient ID number':
                   {'ix': [0, 8]},
               'Marital Status at DX':
                   {'ix': [18, 19],
                    'codes': {1: 'Single (never married)',
                              2: 'Married (including common law)',
                              3: 'Separated',
                              4: 'Divorced',
                              5: 'Widowed',
                              6: 'Unmarried or Domestic Partner',
                              9: 'Unknown'
                              }
                    },
               'Sex':
                   {'ix': [23, 24],
                    'codes': {1: 'male',
                              2: 'female'
                              }
                    },
               'Age at diagnosis':
                   {'ix': [24, 27],
                    'codes': {999: 'Unknown'}
                    },
               'Year of diagnosis':
                   {'ix': [38, 42]},
               'Race recode (W,B,AI,API)':
                   {'ix': [233, 234],
                    'codes': {1: 'White',
                              2: 'Black',
                              3: 'American Indian/Alaska Native',
                              4: 'Asian or Pacific Islander',
                              7: 'Other unspecified',
                              9: 'Unknown'
                              }
                    },
               'Insurance recode':
                   {'ix': [310, 311],
                    'codes': {1: 'Uninsured',
                              2: 'Any Medicaid',
                              3: 'Insured',
                              4: 'Insured/No specifics',
                              5: 'Insurance status unknown',
                              9: 'Not available'
                              }
                    },
               'Breast Adjusted AJCC 6th Stage':
                   {'ix': [329, 331],
                    'codes': {0: '0',
                              1: '0a',
                              2: '0is',
                              10: 'I',
                              11: 'INOS',
                              12: 'IA',
                              13: 'IA1',
                              14: 'IA2',
                              15: 'IB',
                              16: 'IB1',
                              17: 'IB2',
                              18: 'IC',
                              19: 'IS',
                              20: 'IEA',
                              21: 'IEB',
                              22: 'IE',
                              23: 'ISA',
                              24: 'ISB',
                              30: 'II',
                              31: 'IINOS',
                              32: 'IIA',
                              33: 'IIB',
                              34: 'IIC',
                              35: 'IIEA',
                              36: 'IIEB',
                              37: 'IIE',
                              38: 'IISA',
                              39: 'IISB',
                              40: 'IIS',
                              41: 'IIESA',
                              42: 'IIESB',
                              43: 'IIES',
                              50: 'III',
                              51: 'IIINOS',
                              52: 'IIIA',
                              53: 'IIIB',
                              54: 'IIIC',
                              55: 'IIIEA',
                              56: 'IIIEB',
                              57: 'IIIE',
                              58: 'IIISA',
                              59: 'IIISB',
                              60: 'IIIS',
                              61: 'IIIESA',
                              62: 'IIIESB',
                              63: 'IIIES',
                              70: 'IV',
                              71: 'IVNOS',
                              72: 'IVA',
                              73: 'IVB',
                              74: 'IVC',
                              88: 'N/A',
                              90: 'OCCULT',
                              99: 'UNK Stage'
                              }
                    },
               'ER Status Recode Breast Cancer':
                   {'ix': [277, 278],
                    'codes': {1: 'Positive',
                              2: 'Negative',
                              3: 'Borderline',
                              4: 'Unknown',
                              9: 'Not 1990+ Breast'
                              }
                    },
               'PR Status Recode Breast Cancer':
                   {'ix': [278, 279],
                    'codes': {1: 'Positive',
                              2: 'Negative',
                              3: 'Borderline',
                              4: 'Unknown',
                              9: 'Not 1990+ Breast'
                              }
                    },
               'SEER Cause-Specific Death Classification':
                   {'ix': [271, 272],
                    'codes': {0: 'Alive or dead of other cause',
                              1: 'Dead',
                              9: 'N/A not first tumor'
                              }
                    },
               'Survival months':
                   {'ix': [300, 304],
                    'codes': {9999: 'Unknown'}
                    },
               }

