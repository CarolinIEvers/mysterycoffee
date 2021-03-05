import gspread
import requests
import pandas as pd
import numpy as np
import random
import copy
import sys


def fetch_and_pair_participants(max_group_size=2):

    """
    Fetches the (new) participants using Google Spreadsheet API.
    Rematching is prevented by storing previous pairings. 
    """

    #fetch data
    gc = gspread.oauth()
    sheet = gc.open("MysteryCoffee")
    sheet.updated
    participants_df = pd.DataFrame(sheet.worksheet("new_participants").get_all_records())
    old_pairings_df = pd.DataFrame(sheet.worksheet("old_pairs").get_all_records(head=0, default_blank=None))

    old_pairings = old_pairings_df.values.tolist()
    del old_pairings[0]
    for pair in old_pairings:
        for person in pair:
            if person is None:
                pair.remove(person)
    old_pairings = set([tuple(pair) for pair in old_pairings])
    participants = list(set(participants_df['Email']))
    if len(participants) <= 1:
        sys.exit("No or only 1 participant.")
    elif len(participants) == 2:
        #check if these two individuals have been matched before
        if (participants[0], participants[1]) in old_pairings or \
        (participants[1], participants[0]) in old_pairings:
            sys.exit("Only two individuals signed up and both were already matched once before.")

    # assign new pairs
    copy_participants = copy.deepcopy(participants)
    new_pairings = set()
    tries = 0
    while tries < 1000000:

        while len(copy_participants) > 0:
            
            group_size = random.choice([2, max_group_size])

            if len(copy_participants) == 1:
                #add remaining person to a random group
                random_group = random.choice(list(new_pairings))
                new_group = tuple(sorted(random_group + (copy_participants[0],)))
                new_pairings.remove(random_group)
                new_pairings.add(new_group)
                del copy_participants[0]

            elif len(copy_participants) == 2:
                #pair these two remaining persons
                new_pairings.add(tuple(sorted(copy_participants)))
                del copy_participants[:]

            else:
                try:
                    sample = random.sample(copy_participants, group_size)
                    new_pairings.add(tuple(sorted(sample)))
                    for person in sample:
                        copy_participants.remove(person)
                except ValueError:
                    #remaining individuals < group_size, so just put the remaining people in the same group
                    remaining_individuals = tuple(sorted(copy_participants)) 
                    new_pairings.add(remaining_individuals)
                    del copy_participants[:]

        if new_pairings.isdisjoint(old_pairings):
            break
        else:
            tries += 1
            new_pairings.clear()
            copy_participants = copy.deepcopy(participants)

    print('\n', new_pairings)

    for pair in new_pairings:
        sheet.worksheet("old_pairs").append_row(pair)

    #clear the participants worksheet brute force fix
    # sheet.sheet1.resize(rows=2)
    # sheet.sheet1.resize(rows=1000)
    # sheet.sheet1.delete_row(2)
  
    #return also the participants pandas dataframe, for use in email function
    # return new_pairings, participants_df


def fetch_conversation_starter():
    
    """ 
    Fetch a conversation starter from Conversationstarter.com
    """

    pass


def email_participants(pairings):
    
    """
    To send out emails for example every Monday at 12:00, set up a cronjob (Linux)
    like so:
        
        '0 12 * * 1 python3 /path/to/mysterycoffee.py'

    """
    #pairings[0] = actual pairings 
    #pairings[1] = dataframe with the names and emails (look-up table)
    #loop over new_pairings en check participants_df for names, call fetch_conversation
    #starter method and send email

    pass






def main():

    fetch_and_pair_participants(max_group_size=3)
    pass



if __name__ == '__main__':
    main()