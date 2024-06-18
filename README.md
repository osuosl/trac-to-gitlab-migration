# Trac to GitLab Migration Script

This script migrates tickets, comments, attachments, labels, and users from a Trac instance to GitLab. The script is
designed to work with Python 2.7.

## Prerequisites

1. **Python 2.7**: Ensure you have Python 2.7 installed on your system.
2. **Python Packages**: Install the required Python packages listed below.

## Installation

1. Clone this repository to your local machine:
    ```bash
    git clone https://github.com/osuosl/trac-to-gitlab-migration.git
    cd trac-to-gitlab-migration
    ```

2. Install the required Python packages:
    ```bash
    pip install requests psycopg2
    ```

## Configuration

1. **Settings File**: Create a `settings.py` file in the root of the project directory with the following content:

    ```python
    # settings.py

    # Trac Database Configuration
    TRAC_DB_NAME = 'trac_db'
    TRAC_DB_USER = 'trac_user'
    TRAC_DB_PASSWORD = 'trac_password'
    TRAC_DB_HOST = 'localhost'
    TRAC_DB_PORT = '5432'

    # GitLab Configuration
    GITLAB_API_URL = 'https://gitlab.example.com/api/v4'
    GITLAB_TOKEN = 'your_gitlab_private_token'
    PROJECT_ID = 12345678
    ```

2. **Usernames File**: Create a `usernames.txt` file in the root of the project directory. This file should contain a
   list of Trac usernames to be migrated, one per line.

    ```
    user1
    user2
    user3
    ```

## Usage

1. **Run the Script**: Execute the script to start the migration process.

    ```bash
    python trac_to_gitlab.py
    ```

    The script will:
    - Export users from Trac and create them in GitLab.
    - Export tickets from Trac and create corresponding issues in GitLab.
    - Migrate comments, status changes, and attachments in chronological order.
    - Create labels for components, priorities, resolutions, and versions.
    - Close issues in GitLab if they are closed in Trac.

## Script Overview

### Key Functions

- **export_trac_users**: Exports users from the Trac database.
- **create_gitlab_user**: Creates a user in GitLab.
- **export_trac_tickets**: Exports tickets from the Trac database.
- **create_issue**: Creates an issue in GitLab.
- **add_comment**: Adds a comment to a GitLab issue.
- **add_attachment**: Adds an attachment to a GitLab issue.
- **update_issue_state**: Updates the state of a GitLab issue (e.g., closing it).
- **convert_urls_to_gitlab_markdown**: Converts Trac URLs to GitLab markdown format.
- **get_or_create_label**: Gets or creates a label in GitLab and caches it.
- **get_or_create_milestone**: Gets or creates a milestone in GitLab and caches it.

### Error Handling

The script includes error handling and logging to help diagnose issues during the migration process. Errors related to
label creation and user creation are logged with details to help identify the cause.

## License

This project is licensed under the GPL v3 License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please create a pull request or submit an issue for any improvements or bug fixes.

## Acknowledgements

It was created in with the use of ChatGPT.

---

*Note*: Ensure you have the necessary permissions to create users, labels, and issues in your GitLab project before
running the script.

