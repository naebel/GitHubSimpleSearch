��#   G i t H u b S i m p l e S e a r c h  

*GitHub Simple Search*
An application that allows you to explore the following GitHub data using the
GitHub REST API:

1. Find a GitHub organization by name and return a list of all public members
in that organization, including each member's username, real name, and email
address (if available).

2. Find a user by their user name and return a list of all public repos
that they have made at least one commit to. For each repo returned return the
repo name, the number of commits the user made to the repo, and the last date
that the user committed to the repo.

*Instructions for use:*
1. Install Python 3 (code written and tested in Python 3.6.4 on Windows in Powershell)

2. Add the environment variable 'GITHUB_TOKEN' with a personal access token
generated at 'https://github.com/settings/tokens' as the value

3. Run `pip install` for  `requests` module
   - Other required modules you may need to install:
       - `argparse`

4. Pull the code

5. Open terminal/cmd/powershell

6. Run `<path to python executable> <path to this file>/<this filename>`
    - Adding a `-g` to the end will start up the GUI version.

7. Follow the instructions as they appear on the terminal/GUI.
    - GUI search works with both hitting the enter key and clicking the `Search` button.
    - Searching does take some time, depending on the internet connection/size
      of the results.
