from __future__ import unicode_literals, print_function
import os
import requests
import json
import pytz
from datetime import datetime
from trac.env import Environment
from trac.ticket.model import Ticket, Milestone, Component, Version
from trac.attachment import Attachment
from trac.resource import Resource
from trac.ticket.query import Query
import re

# Load settings
with open('settings.json') as f:
    settings = json.load(f)

# Trac configuration
TRAC_ENV_PATH = settings['trac_env_path']

# GitLab configuration
GITLAB_API_URL = settings['gitlab_api_url']
GITLAB_TOKEN = settings['gitlab_token']
PROJECT_ID = settings['project_id']

# Map Trac users to GitLab user IDs
user_map = {}

# Initialize Trac environment
env = Environment(TRAC_ENV_PATH)

def load_usernames():
    with open('usernames.txt') as f:
        usernames = [line.strip() for line in f if line.strip()]
    return usernames

def export_trac_users(usernames):
    print("Exporting Trac users...")
    trac_users = []

    for username in usernames:
        email = None
        session = env.get_known_users()
        for sid, name, mail in session:
            if sid == username:
                email = mail
                break

        trac_users.append({
            'username': username,
            'email': email
        })

        print("Exported user: {}".format(username))

    print("Finished exporting Trac users.")
    return trac_users

def create_gitlab_user(username, email):
    url = "{}/users".format(GITLAB_API_URL)
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    data = {
        "email": email,
        "username": username,
        "name": username,
        "skip_confirmation": True,
        "reset_password": True
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def create_gitlab_label(name, color="#428BCA"):
    url = "{}/projects/{}/labels".format(GITLAB_API_URL, PROJECT_ID)
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    data = {
        "name": name,
        "color": color
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def create_gitlab_milestone(title, description, due_date=None):
    url = "{}/projects/{}/milestones".format(GITLAB_API_URL, PROJECT_ID)
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    data = {
        "title": title,
        "description": description,
        "due_date": due_date
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def get_or_create_label(label_name, label_cache):
    if label_name not in label_cache:
        label = create_gitlab_label(label_name)
        label_cache[label_name] = label
    return label_cache[label_name]

def get_or_create_milestone(milestone_name, milestone_cache):
    if milestone_name not in milestone_cache:
        milestone = create_gitlab_milestone(milestone_name, milestone_name)
        milestone_cache[milestone_name] = milestone
    return milestone_cache[milestone_name]

def export_trac_tickets():
    print("Exporting Trac tickets...")
    trac_tickets = []

    query = Query(env, "max=0&order=id")
    tickets = query.execute()

    for ticket_info in tickets:
        ticket_id = ticket_info['id']
        ticket = Ticket(env, ticket_id)
        comments_list = []
        status_changes_list = []

        for change in ticket.get_changelog():
            timestamp, author, field, oldvalue, newvalue, permanent = change
            if timestamp is not None:
                timestamp = float(timestamp)
                timestamp_utc = datetime.fromtimestamp(timestamp, pytz.UTC).strftime('%Y-%m-%d %H:%M:%S %Z')
            else:
                timestamp_utc = None
            if field == 'comment':
                comments_list.append({'author': author, 'time': timestamp_utc, 'comment': newvalue})
            else:
                status_changes_list.append({'author': author, 'time': timestamp_utc, 'field': field, 'oldvalue': oldvalue, 'newvalue': newvalue})

        attachments_list = []
        resource = Resource('ticket', ticket_id)
        for attachment in Attachment.select(env, resource):
            if attachment.date is not None:
                attachment_date = float(attachment.date)
                timestamp_utc = datetime.fromtimestamp(attachment_date, pytz.UTC).strftime('%Y-%m-%d %H:%M:%S %Z')
            else:
                timestamp_utc = None
            file_path = attachment.path
            if os.path.isfile(file_path):
                attachments_list.append({
                    'ticket_id': ticket_id,
                    'filename': attachment.filename,
                    'description': attachment.description,
                    'author': attachment.author,
                    'time': timestamp_utc,
                    'file_path': file_path
                })
            else:
                print("Warning: File {} not found for ticket ID {}".format(file_path, ticket_id))

        if ticket.time_created is not None:
            ticket_time_created = float(ticket.time_created)
            ticket_time_created_utc = datetime.fromtimestamp(ticket_time_created, pytz.UTC).strftime('%Y-%m-%d %H:%M:%S %Z')
        else:
            ticket_time_created_utc = None

        trac_tickets.append({
            'id': ticket_id,
            'summary': ticket['summary'],
            'description': ticket['description'],
            'component': ticket['component'],
            'priority': ticket['priority'],
            'resolution': ticket['resolution'],
            'milestone': ticket['milestone'],
            'version': ticket['version'],
            'status': ticket['status'],
            'reporter': ticket['reporter'],
            'time': ticket_time_created_utc,
            'comments': comments_list,
            'attachments': attachments_list,
            'status_changes': status_changes_list
        })

        print("Exported ticket ID: {}".format(ticket_id))

    trac_tickets.sort(key=lambda x: x['id'])  # Sort tickets numerically by ID
    print("Finished exporting Trac tickets.")
    return trac_tickets

def convert_urls_to_gitlab_markdown(text):
    # Convert [http://example.org/foo Link Title] to [Link Title](http://example.org/foo)
    url_pattern = re.compile(r'\[(http[^\s]+) ([^\]]+)\]')
    return url_pattern.sub(r'[\2](\1)', text)

def format_comment(comment):
    # Add '@' to author, add extra new line, and convert {{{ and }}} to code blocks
    comment_text = "Comment by @{} on {}:\n\n{}".format(comment['author'], comment['time'], comment['comment'])
    comment_text = convert_urls_to_gitlab_markdown(comment_text).replace('{{{', '```').replace('}}}', '```')
    return comment_text

def import_to_gitlab():
    print("Importing tickets, comments, and attachments into GitLab...")

    label_cache = {}
    milestone_cache = {}

    def create_issue(ticket_id, title, description, labels, milestone_id, created_at):
        url = "{}/projects/{}/issues".format(GITLAB_API_URL, PROJECT_ID)
        headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
        data = {
            "iid": ticket_id,
            "title": title,
            "description": description,
            "labels": labels,
            "milestone_id": milestone_id,
            "created_at": created_at
        }
        response = requests.post(url, headers=headers, json=data)
        return response.json()

    def update_issue_state(issue_id, state):
        url = "{}/projects/{}/issues/{}".format(GITLAB_API_URL, PROJECT_ID, issue_id)
        headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
        data = {"state_event": state}
        response = requests.put(url, headers=headers, json=data)
        return response.json()

    def add_comment(issue_id, comment, created_at):
        if comment.strip():  # Only add non-empty comments
            url = "{}/projects/{}/issues/{}/notes".format(GITLAB_API_URL, PROJECT_ID, issue_id)
            headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
            data = {"body": comment, "created_at": created_at}
            response = requests.post(url, headers=headers, json=data)
            return response.json()

    def add_attachment(issue_id, attachment):
        url = "{}/projects/{}/uploads".format(GITLAB_API_URL, PROJECT_ID)
        headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}

        with open(attachment['file_path'], 'rb') as f:
            files = {'file': (attachment['filename'], f)}
            response = requests.post(url, headers=headers, files=files)
            upload_response = response.json()

        if 'markdown' in upload_response:
            comment_body = "Attachment by @{} on {}: {}\n\n{}".format(
                attachment['author'], attachment['time'], upload_response['markdown'], attachment['description']
            )
            add_comment(issue_id, comment_body, attachment['time'])
            print("Added attachment to GitLab issue ID: {}".format(issue_id))
        else:
            print("Failed to upload attachment for ticket ID {}: {}".format(attachment['ticket_id'], response.text))

    trac_tickets = export_trac_tickets()

    for ticket in trac_tickets:
        labels = []
        if ticket['component']:
            label = get_or_create_label(ticket['component'], label_cache)
            labels.append(label['name'])
        if ticket['priority']:
            label = get_or_create_label(ticket['priority'], label_cache)
            labels.append(label['name'])
        if ticket['resolution']:
            label = get_or_create_label(ticket['resolution'], label_cache)
            labels.append(label['name'])
        if ticket['version']:
            label = get_or_create_label(ticket['version'], label_cache)
            labels.append(label['name'])

        milestone_id = None
        if ticket['milestone']:
            milestone = get_or_create_milestone(ticket['milestone'], milestone_cache)
            milestone_id = milestone['id']

        description = "Comment by @{} on {}:\n\n{}".format(ticket['reporter'], ticket['time'], ticket['description'])
        description = convert_urls_to_gitlab_markdown(description).replace('{{{', '```').replace('}}}', '```')

        issue = create_issue(ticket['id'], ticket['summary'], description, ','.join(labels), milestone_id, ticket['time'])
        issue_id = issue['id']

        events = ticket['comments'] + ticket['status_changes'] + ticket['attachments']
        events.sort(key=lambda e: e['time'])

        for event in events:
            if 'comment' in event:
                comment_body = format_comment(event)
                add_comment(issue_id, comment_body, event['time'])
                print("Added comment to GitLab issue ID: {}".format(issue_id))
            elif 'field' in event:
                change_body = "Status change by @{} on {}: {} set to {}\n".format(
                    event['author'], event['time'], event['field'], event['newvalue'])
                add_comment(issue_id, change_body, event['time'])
                print("Added status change comment to GitLab issue ID: {}".format(issue_id))
            elif 'filename' in event:
                add_attachment(issue_id, event)

        if ticket['status'] in ['closed', 'resolved']:
            update_issue_state(issue_id, 'close')

    print("Finished importing tickets, comments, and attachments into GitLab.")

def main():
    usernames = load_usernames()

    trac_users = export_trac_users(usernames)
    for user in trac_users:
        if user['email']:
            gitlab_user = create_gitlab_user(user['username'], user['email'])
            user_map[user['username']] = gitlab_user['id']
            print("Created GitLab user: {} with ID: {}".format(user['username'], gitlab_user['id']))

    import_to_gitlab()

if __name__ == "__main__":
    main()
