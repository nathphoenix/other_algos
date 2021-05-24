
## Initialise all the available boards for the current user
from trello import TrelloClient
from trello.member import Member
import pandas as pd
from datetime import datetime as dt
import requests
import json
import numpy as np

account_token = ''
trello_api_key = ''
trello_api_secret = ''

client = TrelloClient(
    api_key=trello_api_key,
    api_secret=trello_api_secret,
    token=account_token,
#     token_secret='your-oauth-token-secret'
)

# Get a list of all the available boards
all_boards = client.list_boards()


"""
New Functioncs
"""
def get_target_board_lists(all_boards, target_board):
    """
    This function gets a list of all the trello-lists belonging to a target board
    """
    for i in range(len(all_boards)):
        board = all_boards[i]
#         print(board)
        if board.name == target_board:
            break
    target_board = all_boards[i]
    target_board_lists = target_board.list_lists()
    
    return target_board, target_board_lists


def get_target_list_card_details(target_board, target_board_lists, target_list_name):
    """
    This function takes a target list within a board, and then gets all the
    card details for each card in that list
    """
    for items in range(len(target_board_lists)):
        lst = target_board_lists[items]
        print('lst',lst)
        if lst.name == target_list_name:
            target_list_id = lst.id
            
            break
    target_list = target_board.get_list(target_list_id)
    return target_list

def trello_alert(title, body):
    payload = {"msg_title": title,
            "msg_body": body,
            "slack_channel": 'trello-alerts',
        }
    
    slack_endpoint = "https://ds4.bloverse.com/v1/slack-notification"
    try:
        response = requests.request("POST", slack_endpoint,
                                    headers={'Content-Type': 'application/json'},
                                    data=json.dumps(payload, indent="     ", default=str)
                                    )
    except Exception as e:
        print(e)
        response = 'Post request error, check your data'
    
    return response

def convert_df_dict(df):
    new_dict = df.T.to_dict()
    final = [v for k, v in new_dict.items()]
    return final


## Input parameters
# Board that we will be monitoring
def trello_performance(target_board_name):
    # Relevant lists that we will want to be analysing
    relevant_list_names = ['Test Current Sprint', 'Test Doing', 'Test Blocker', 'Test Review', 'Test Done', 'To-do']
    target_list_name = relevant_list_names[0] # later you will just run through the relevant list names when getting the performance update
    target_list_name = 'Sprint 1.1 In Progress'
    ## Nat to create employee dict for the DS team

    # Get the target board, as well as all the trello lists within that board
    target_board, target_board_lists = get_target_board_lists(all_boards, target_board_name)
    all_labels = []
    for labels in target_board_lists:
        labels = str(labels)
        labels = labels.replace('<', '').replace('>', '').replace('List ', '')
        all_labels.append(labels)
    all_labels = all_labels[1:7]
    # This gets the target list that were looking for
    details = []
    all_details = []
    df = pd.DataFrame()
    #df = pd.DataFrame(columns=['card_name', 'assigned_member_ids', 'assigned_member_names', 'task_category', 'task_duration', 'task_description', 'task_last_activity'])

    for items in all_labels:
        target_list = get_target_list_card_details(target_board, target_board_lists, items)
#         print(items)
        for card in target_list.list_cards():
            try:
                card_name = card.name
                print('Task name: %s' % card_name)
                
                assigned_member_ids = card.member_id

                try:
                    assigned_member_names = [client.get_member(un_id).full_name for un_id in card.member_id]
                except Exception as e:
                    print(e)
                    assigned_member_names = ['Network or API error, run the script again']
                
                if not assigned_member_ids:
                    assigned_member_ids = 'empty_id'
                else:
                    assigned_member_ids = ' '.join(assigned_member_ids)
    #             print('User_id : %s' % assigned_member_ids)
                assigned_member_names = ' '.join(assigned_member_names)
                print('Assigned to: %s' % assigned_member_names)
                user_data = {
                            assigned_member_names:assigned_member_ids
                       }
                details.append(user_data)

                task_category = card.labels[0].name
                task_duration = card.labels[1].name

    #             print('Task Category: %s' % task_category)
    #             print('Task Duration: %s' % task_duration)
                task_description = card.desc
                checklist = card.countCheckItems

    #             print('Task Description: %s' % task_description)
                task_last_activity = card.dateLastActivity
    #             print('Task Last Activity: %s' % task_last_activity)
                
                # Due date for the task
                due = card.due


                task_details = {
                    'labels': items,
                    'card_name': card_name,
                    'assigned_member_ids':assigned_member_ids,
                    'assigned_member_names': assigned_member_names,
                    'task_category':task_category,
                    'checklist': checklist,
                    'task_duration':task_duration,
                    'task_description':task_description,
                    'task_last_activity':task_last_activity,
                    'due_date': due

                }
                print('task_details', task_details)
                all_details.append(task_details)
                df.append(task_details, ignore_index=True)


                print()
            except Exception as e:
                print(e)
#                 exception_title = 'Error, There is no category or duration included when creating card'
#                 exception_body = card_name
#                 trello_alert(exception_title, exception_body)
#                 print('There is no category or duration included when creating %' %card_name)
                print()


    #get all users on Bloverse Mobile
    new_ds = []
    for x in details:
        if x not in new_ds:
            new_ds.append(x)
    dico = new_ds
    # convert list of dictionary to dictionary
    final_dict = {k:v for element in dico for k,v in element.items()}
    for key in list(final_dict.keys()):
         if key == '':
            del final_dict[key]
    final_dict = final_dict
    #in other to get just the individual names in DS board
    new_dict_users = {}
    for key, value in final_dict.items():
        keys = len(str(value))
        if keys <= 25:
            new_dict_users[key] = value

    df = pd.DataFrame.from_records(all_details)
    
    df['task_last_activity'] = df['task_last_activity'].dt.strftime('%Y-%m-%d %H:%M:%S')
    try:
        df['due_date'] =  pd.to_datetime(df['due_date'], infer_datetime_format=True)
        df['due_date'] = df['due_date'].dt.date
    except TypeError:
        pass
    df = df[['labels', 'card_name', 'checklist', 'assigned_member_names', 'task_category', 'task_duration', 'due_date']]
    #handle misplace values on thesame row
    m = pd.to_numeric(df['task_category'], errors='coerce').notna()
    df.loc[m, ['task_category', 'task_duration']] = df.loc[m, ['task_duration','task_category']].values
    

    

    current_sprint = 'Current Sprint'
    progress = 'Working On'
    review = 'Code Review'
    completed_task = 'Done (Patch)'
    alpha_complete = 'Done 1.0'
#     blocker = 'Blocker'

    #for current sprint
    sprint_1_1 = df[df['labels'] == current_sprint]
    sprint_1_1['task_duration'] = sprint_1_1["task_duration"].astype(float)
    sprint_1_1 = sprint_1_1[['assigned_member_names', 'card_name', 'checklist', 'task_category', 'task_duration']]
    current = sprint_1_1
    users_dict = new_dict_users
    for key in list(users_dict.keys()):  # Use a list instead of a view
         if key in current['assigned_member_names'].to_list():
            del users_dict[key]
    unassign_user = users_dict
    unassign_current = list(unassign_user.keys())
#     texts = 'The users below has no task in queue for this current sprint'
    unassign_users_dicts = {
#         'response' : texts,
        'data': unassign_current   
    }
    total_duration_sprint = sprint_1_1.groupby('assigned_member_names')['task_duration'].sum().to_dict()
    number_of_task_sprint = sprint_1_1['assigned_member_names'].value_counts().to_dict()
    sprint_1_1 = convert_df_dict(sprint_1_1)
    
    unassign_title_current = 'Members without Task for the sprint'
    sprint_1_1_count_title = 'Number of task for each member In Sprint'
    sprint_1_1_duration_title = 'Total Task duration for each member In Sprint'
    
    
    title = 'Mobile Current Sprint Alerts'
    sprint_alert1 = trello_alert(title, sprint_1_1)
    sprint_alert2 = trello_alert(sprint_1_1_count_title, number_of_task_sprint)
    sprint_alert3 = trello_alert(sprint_1_1_duration_title, total_duration_sprint)
    sprint_alert4 = trello_alert(unassign_title_current, unassign_current)
    
#     sprint_alert = trello_alert(title, sprint_body)

#BLOCKER ALERTS
    blocker = 'Blocker'
    blocker = df[df['labels'] == blocker]
    if not blocker.empty:
        blocker = blocker.value_counts().to_dict()
    else:
        blocker = {'blockers':'No blocker Found'}
    blocker_title = 'Blocker Task Alert'
    blocker_alert = trello_alert(blocker_title, blocker)
    


    #progress category

    progress = df[df['labels'] == progress]
    progress = progress[['assigned_member_names', 'card_name', 'task_category', 'task_duration', 'due_date']]
    progress['task_duration'] = progress["task_duration"].astype(float)
    #Users without task they are currently working on
    for key in list(new_dict_users.keys()):  # Use a list instead of a view
         if key in progress['assigned_member_names'].to_list():
            del new_dict_users[key]
    unassign_users = new_dict_users
    unassign = list(unassign_users.keys())
#     text = 'The users below has not been assign any task'
    unassign_users_dict = {
#         'response' : text,
        'data': unassign   
    }
    
    unassign_title = 'Mobile Team Members without Task currently'

    progress_count = progress['assigned_member_names'].value_counts().to_dict()
    progress_duration = progress.groupby('assigned_member_names')['task_duration'].sum().to_dict()
    progress_count_title = 'Number of task for each member In Progress'
    progress_duration_title = 'Total Task duration for each member In Progress'
    
    progress_dict = convert_df_dict(progress)
#     progress_dict = [v for k, v in progress_dict.items()]
    
    #OVERDUE TASK IN PROGRESS
    Current_time = dt.utcnow().date()
    overdue = progress['due_date'] - Current_time
    progress['Overdue_since'] = overdue.astype('timedelta64[D]').astype('Int64')
    progress[['assigned_member_names', 'card_name', 'due_date', 'Overdue_since' ]]
    Overdue_progress_title = 'Overdue Task'
    try:
        Overdue_progress = progress[progress['Overdue_since'] < 0]
        not_overdue_progress = progress[progress['Overdue_since'] >= 0]
    except IndexError:
        Overdue_progress = pd.DataFrame()
        not_overdue_progress = pd.DataFrame()
    if not Overdue_progress.empty:
        Overdue_progress = convert_df_dict(Overdue_progress)
    else:
        Overdue_progress = 'No overdue task'
        
    if not not_overdue_progress.empty:
        not_overdue_progress = convert_df_dict(not_overdue_progress)
    else:
        not_overdue_progress = 'No overdue task'
    
        
    
    
    
    Overdue_progress_title = 'Overdue Task Alerts'
    not_overdue_progress_title = 'Non-Overdue(Active) Task Alerts'
    progress_title = 'Progress Task Alerts'
    
    progress_alert = trello_alert(progress_title, progress_dict)
    progress_alert = trello_alert(progress_count_title, progress_count)
    progress_alert = trello_alert(progress_duration_title, progress_duration)
    progress_alert = trello_alert(unassign_title, unassign)
    progress_alert = trello_alert(Overdue_progress_title, Overdue_progress)
    progress_alert = trello_alert(not_overdue_progress_title, not_overdue_progress)
    

    
    

    #review
    review = df[df['labels'] == review]
    review = review[['assigned_member_names', 'card_name', 'task_category', 'task_duration']]
    review_count = review['assigned_member_names'].value_counts().to_dict()
    review_duration = review.groupby('assigned_member_names')['task_duration'].sum().to_dict()
    review = convert_df_dict(review)
#     review = [v for k, v in review.items()]
    review_title = 'Review Alerts'


    
    review_count_title = 'Number of task for each member In review'
    review_duration_title = 'Total Task duration for each member In review'
    
    
    
    review_alert = trello_alert(review_title, review)
    review_alert = trello_alert(review_count_title, review_count)
    review_alert = trello_alert(review_duration_title, review_duration)
    
    #complete category
    complete = df[df['labels'] == completed_task]
    complete = complete[['assigned_member_names', 'card_name', 'task_category', 'task_duration']]
    complete_count = complete['assigned_member_names'].value_counts().to_dict()
    
    complete = convert_df_dict(complete)
#     complete = [v for k, v in complete.items()]
    complete_title = 'Completed Done (Patch) Alerts'
    complete_count_title = 'Number of task completed by each member'
    complete_alert = trello_alert(complete_title, complete)
    complete_alert = trello_alert(complete_count_title, complete_count)
    
    #Done1.0 complete category
    complete_done = df[df['labels'] == alpha_complete]
    complete_done = complete_done[['assigned_member_names', 'card_name', 'task_category', 'task_duration']]
    complete_done_count = complete_done['assigned_member_names'].value_counts().to_dict()

    complete_done = convert_df_dict(complete_done)
    complete_done_title = 'Completed (Done.10) Task Alerts'

    complete_alpha_count_title = 'Number of task completed by each member for Done 1.0'
    complete_alpha_alert = trello_alert(complete_done_title, complete_done)
    complete_alpha_alert = trello_alert(complete_alpha_count_title, complete_done_count)

    return complete_done, review_duration, review_count, progress_duration, progress_count, unassign_users_dict, number_of_task_sprint, total_duration_sprint, Overdue_progress

# if __name__ == "__main__" :
#     result = trello_performance('DS')
complete_count, review_duration, review_count, progress_duration, progress_count, unassign_users_dict, number_of_task_sprint, total_duration_sprint, Overdue_progress = trello_performance('DS')   