import gspread
import pandas as pd
import numpy as np
import random
import copy
import sys
import argparse
import requests
from bs4 import BeautifulSoup
import smtplib
import config


EMAIL_USERNAME = config.email_username
EMAIL_PASSWORD = config.email_password


def fetch_and_pair_participants(max_group_size=2):

    """
    Fetches the (new) participants using Google Spreadsheet API.
    Rematching is prevented by storing previous pairings. 
    """

    #fetch data
    gc = gspread.oauth()
    sheet = gc.open("MysteryCoffee")
    participants_df = pd.DataFrame(sheet.worksheet("new_participants").get_all_records())
    old_pairings = pd.DataFrame(sheet.worksheet("old_pairs").get_all_values()).values.tolist()
    del old_pairings[0]
    old_pairings_noblanks = []
    for pair in old_pairings:
        new_pair = tuple(filter(lambda x: x != '', pair))
        old_pairings_noblanks.append(new_pair)
    old_pairings = set(old_pairings_noblanks)
    participants = list(set(participants_df['Email']))
    if len(participants) <= 1:
        sys.exit("No or only 1 participant.")
    elif len(participants) == 2:
        #check if these two individuals have been matched before
        if (participants[0], participants[1]) in old_pairings or \
        (participants[1], participants[0]) in old_pairings:
            sys.exit("Only two individuals signed up and both were already matched once before.")

    #assign new pairs
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

        #avoids redundancy in groups: if an individual was already in a pair/group with
        #another individual, they will not be a pair/in the same group again. Can be omitted.
        class NotUniqueGroup(Exception): pass
        try:
            for new_pair in new_pairings:
                for old_pair in old_pairings:
                    if len(set(new_pair).intersection(set(old_pair))) > 1:
                        raise NotUniqueGroup
        except NotUniqueGroup:
            tries += 1
            new_pairings.clear()
            copy_participants = copy.deepcopy(participants)
            continue

        break

    print('\n', old_pairings, '\n')
    print('\n', new_pairings)

    for pair in new_pairings:
        sheet.worksheet("old_pairs").append_row(pair)

    #clear the participants worksheet brute force fix (.clear() irreversibly clears form headers)
    # sheet.sheet1.resize(rows=2)
    # sheet.sheet1.resize(rows=1000)
    # sheet.sheet1.delete_row(2)
  
    #return also the participants_df pandas dataframe, for use in email function
    return new_pairings, participants_df


def fetch_conversation_starter():
    
    """ 
    Fetch a conversation starter from Conversationstarter.com
    """

    url = 'https://www.conversationstarters.com/generator.php'

    try:
        response = requests.get(url)
        html_content = response.content
        soup = BeautifulSoup(html_content, 'html.parser')
        question = soup.find_all(text=True)[22].strip()
        return question

    except Exception as e:
        print("Error occurred fetching conversation starter: ", '\n', e)


def email_participants(pairings, dataframe):
    
    """
    To send out emails for example every Monday at 12:00, set up a cronjob (Linux)
    like so:
        
        '0 12 * * 1 python3 /path/to/mysterycoffee.py'

    """

    #pairings[0] = new pairings 
    #pairings[1] = dataframe with the names and emails (look-up table for names)
    pairings = list(pairings)
    df = dataframe

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo() 
        smtp.login(EMAIL_USERNAME, EMAIL_PASSWORD)

        #loops over new pairings en checks for names, calls fetch_conversation_starter 
        #method and finally sends email to all participants
        subject = 'Mystery Coffee'
        for pair in pairings:
            conversation_starter = fetch_conversation_starter()
            pair = list(pair)
            pair = df[df['Email'].isin(pair)][['Name', 'Email']].values.tolist()
            tmp = copy.deepcopy(pair)
            for person in pair:
                person_name = person[0]
                person_mail = person[1]
                tmp.remove(person)
                names = []
                mails = []
                for name, email in tmp:
                    names.append(name)
                    mails.append(email)
                recipients = [names, mails]
                recipients_names = ', '.join(recipients[0])
                recipients_emails = ', '.join(recipients[1])
                body = f"Hi {person_name},\n\nYour partner(s) for the Mystery Coffee " \
                f"of this week: {recipients_names}.\n\n" \
                f"Conversation starter: {conversation_starter}\n\n" \
                f"Their email(s):\n{recipients_emails}" 

                msg = f'Subject: {subject}\n\n{body}'
                smtp.sendmail(EMAIL_USERNAME, person_mail, msg)

                tmp = copy.deepcopy(pair)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-group_size', '--group_size', type=int, required=True, help='Desired group size (range 2-5).')
    args = parser.parse_args()

    if not 1 < args.group_size < 6:
        sys.exit("Choose a group size between 2-5.")

    new_pairings, dataframe = fetch_and_pair_participants(max_group_size=args.group_size)
    email_participants(new_pairings, dataframe)


if __name__ == '__main__':
    main()
