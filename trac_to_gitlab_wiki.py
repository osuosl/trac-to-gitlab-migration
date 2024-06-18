import os
import json
import requests
import re
from trac.env import open_environment
from trac.wiki.model import WikiPage

# Load settings from settings.json
with open('settings.json') as f:
    settings = json.load(f)

TRAC_ENV_PATH = settings['trac_env_path']
GITLAB_API_URL = settings['gitlab_api_url']
GITLAB_TOKEN = settings['gitlab_token']
PROJECT_ID = settings['project_id']

# Full GitLab API URL
GITLAB_WIKI_API_URL = '{}/projects/{}/wikis'.format(GITLAB_API_URL, PROJECT_ID)

# List of specific pages to exclude
exclude_pages = [
    'WikiDeletePage', 'WikiNewPage', 'WikiPageNames', 'WikiRestructuredTextLinks',
    'Sandbox', 'InterWiki', 'PageTemplates', 'RecentChanges', 'InterMapTxt',
    'InterTrac', 'WikiFormatting', 'WikiMacros', 'WikiProcessors',
    'WikiRestructuredText', 'WikiHtml'
]

# Function to convert Trac wiki syntax to Markdown
def trac_to_markdown(trac_content):
    # Ensure trac_content is a Unicode string
    if not isinstance(trac_content, unicode):
        trac_content = trac_content.decode('utf-8')

    # Convert headers
    trac_content = re.sub(r'(^|\n)=(=*)\s*(.*?)\s*=(=*)', lambda m: '\n' + '#' * (len(m.group(2)) + 1) + ' ' + m.group(3), trac_content)

    # Convert links
    trac_content = re.sub(r'\[http([^\s]+)\s+([^\]]+)\]', r'[\2](http\1)', trac_content)
    trac_content = re.sub(r'\[wiki:([^\s]+)\s+([^\]]+)\]', r'[\2](\1)', trac_content)

    # Convert inline code blocks
    trac_content = re.sub(r'\{\{\{\s*(.*?)\s*\}\}\}', r'`\1`', trac_content)

    # Convert code blocks with language specification
    def convert_code_block(match):
        code_lang = match.group(1).strip() if match.group(1) else ''
        code_content = match.group(2).strip()
        return u'```{}\n{}\n```'.format(code_lang, code_content)
    trac_content = re.sub(r'\{\{\{\s*#!([^\n]+)?\n(.*?)\}\}\}', convert_code_block, trac_content, flags=re.DOTALL)

    # Convert code blocks without language specification
    trac_content = re.sub(r'\{\{\{\s*\n(.*?)\}\}\}', r'```\1```', trac_content, flags=re.DOTALL)

    # Convert bold and italic
    trac_content = re.sub(r"'''(.*?)'''", r'**\1**', trac_content)
    trac_content = re.sub(r"''(.*?)''", r'*\1*', trac_content)

    # Convert unordered lists
    trac_content = re.sub(r'^\s+\* ', r'- ', trac_content, flags=re.MULTILINE)

    # Convert ordered lists
    trac_content = re.sub(r'^\s+\d+\. ', r'1. ', trac_content, flags=re.MULTILINE)

    # Convert tables
    def convert_table(match):
        table_content = match.group(1).strip()
        rows = table_content.split('\n')
        markdown_table = ''
        for row in rows:
            markdown_table += '| ' + ' | '.join(row.split('||')[1:-1]) + ' |\n'
            if not markdown_table.strip().endswith('|\n-'):
                markdown_table += '| --- ' * (len(row.split('||')) - 2) + '|\n'
        return markdown_table
    trac_content = re.sub(r'\|\|.*\|\|\n(.*?)\|\|.*\|\|', convert_table, trac_content, flags=re.DOTALL)

    return trac_content

# Function to create or update a wiki page in GitLab
def create_or_update_gitlab_wiki(page_title, page_content):
    headers = {
        'Private-Token': GITLAB_TOKEN,
        'Content-Type': 'application/json'
    }
    data = {
        'title': page_title,
        'content': page_content
    }
    response = requests.post(GITLAB_WIKI_API_URL, headers=headers, json=data)
    if response.status_code == 201:
        print('Successfully created/updated page: {}'.format(page_title))
    else:
        print('Failed to create/update page: {}'.format(page_title))
        print(response.content)

# Open the Trac environment
env = open_environment(TRAC_ENV_PATH)

# Query to get all wiki page names
wiki_page_names = [row[0] for row in env.db_query("SELECT DISTINCT name FROM wiki")]

# Iterate through all wiki pages
for page_name in wiki_page_names:
    if page_name.startswith('Trac') or page_name in exclude_pages:
        print('Skipping excluded wiki page: {}'.format(page_name))
        continue

    page = WikiPage(env, page_name)
    if page.exists:
        print('Processing page: {}'.format(page_name))
        # Rename WikiStart to home
        gitlab_page_name = 'home' if page_name == 'WikiStart' else page_name
        # Convert Trac content to Markdown
        markdown_content = trac_to_markdown(page.text)
        # Create or update the page in GitLab
        create_or_update_gitlab_wiki(gitlab_page_name, markdown_content)
