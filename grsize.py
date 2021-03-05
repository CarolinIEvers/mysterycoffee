import pandas as pd
import random
import sys
import copy

def fetch_and_pair_participants(max_group_size=2):

    #will change, using gspread to fetch participants and old pairings from Google Spreadsheet
    participants = list(set(pd.read_csv("participants.csv")['email']))
    old_pairings_df = pd.read_csv("all_pairs.csv", header=None)
    old_pairings_list = [tuple(row) for row in old_pairings_df.to_records(index=False)]
    old_pairings = {pair for pair in old_pairings_list} #set comprehension
    if len(participants) <= 1:
        sys.exit("No or only 1 participant.")
    elif len(participants) == 2:
        #check if these two individuals have been matched before
        if (participants[0], participants[1]) in old_pairings or \
        (participants[1], participants[0]) in old_pairings:
            sys.exit("Only two individuals signed up and both were already matched once before.")

    # assign new pairs
    copy_participants = copy.deepcopy(participants)
    # print(copy_participants)
    new_pairings = set()
    tries = 0
    while tries < 1000000:

        while len(copy_participants) > 0:
            
            group_size = random.choice([2, max_group_size])

            if len(copy_participants) == 1:
                #add remaining person to a random group
                random_group = random.choice(list(new_pairings))
                new_group = tuple(sorted(random_group + (copy_participants[0],)))
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
                    continue

        if new_pairings.isdisjoint(old_pairings):
            break
        else:
            tries += 1
            new_pairings.clear()
            copy_participants = copy.deepcopy(participants)

    print('\n', new_pairings)
    # return list(new_pairings)


fetch_and_pair_participants(max_group_size=5)
