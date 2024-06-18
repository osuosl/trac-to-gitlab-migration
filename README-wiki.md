# Trac to GitLab Wiki Migration Script

This script converts a Trac 1.0.8 wiki into a GitLab wiki.

## Requirements

- Python 2.7
- Trac environment with access to the `trac.env` and `trac.wiki.model` modules.
- GitLab account and a private token with API access.

## Python Packages

You need to install the following Python packages:

- `requests`
- `trac`

To install these packages, run:

```sh
pip install requests trac
```

## Setup

1. Clone the repository:

   ```sh
   git clone https://github.com/yourusername/trac-to-gitlab-wiki.git
   cd trac-to-gitlab-wiki
   ```

2. Create a `settings.json` file:

   Create a `settings.json` file in the same directory as the script with the following content:

   ```json
   {
       "trac_env_path": "/path/to/trac/environment",
       "gitlab_api_url": "https://gitlab.example.com/api/v4",
       "gitlab_token": "your_gitlab_private_token",
       "project_id": "your_gitlab_project_id"
   }
   ```

3. Run the script:

  ```sh
  python2 trac_to_gitlab_wiki.py
  ```

## Script Details

The script performs the following steps:

1. Loads settings from settings.json.
2. Connects to the Trac environment specified in the settings.
3. Queries all wiki page names from the Trac environment.
4. Excludes default and specific wiki pages that come with Trac.
5. Converts the content of each Trac wiki page to GitLab-flavored Markdown.
6. Creates or updates the corresponding wiki page in GitLab.

## Excluded Pages

The script automatically exclude pages that are automatically created within a Trac installation.

## Customizing the Conversion

If your Trac content requires additional handling, you can customize the `trac_to_markdown` function in the script.
This function is responsible for converting Trac wiki syntax to GitLab-flavored Markdown.

## Conversion Details

The `trac_to_markdown` function handles:

- Headers
- Links
- Inline code blocks
- Code blocks with language specification
- Bold and italic text
- Unordered and ordered lists
- Tables

## Troubleshooting

If you encounter any issues while running the script, ensure that:

- Your Trac environment path is correct.
- Your GitLab API URL, private token, and project ID are correct.
- You have the necessary permissions in GitLab to create or update wiki pages.

If you still face issues, feel free to open an issue in this repository.

## License

This project is licensed under the GPL v3 License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please create a pull request or submit an issue for any improvements or bug fixes.

## Acknowledgements

It was created in with the use of ChatGPT.
