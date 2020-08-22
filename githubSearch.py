# Application that allows you to explore the following GitHub data using the
# GitHub REST API:
#
# 1. Find a GitHub organization by name and return a list of all public members
# in that organization, including each member's username, real name, and email
# address (if available).
#
# 2. Find a user by their user name and return a list of all public repos
# that they have made at least one commit to. For each repo returned return the
# repo name, the number of commits the user made to the repo, and the last date
# that the user committed to the repo.
#
# Instructions for use:
#
# 1. Install Python 3 (code written and tested in Python 3.6.4 on Windows in Powershell)
# 2. Add the environment variable 'GITHUB_TOKEN' with a personal access token
#    generated at 'https://github.com/settings/tokens' as the value
# 3. Run `pip install` for  `requests` module
#       - Other required modules you may need to install:
#           - `argparse`
# 4. Pull the code
# 5. Open terminal/cmd/powershell
# 6. Run `<path to python executable> <path to this file>/<this filename>`
# 7. Follow the instructions as they appear on the terminal.

import os
import re
import sys
import time
import argparse
import requests # must `pip install requests` library
# from pprint import pprint
from datetime import datetime

# ^authKey has to be valid for:
#   under repo: repo:status, public_repo
#   under admin:org: read:org,
#   under user: read:user, user:email
#
#################################### Model #####################################

def checkInput(input):
    # Only alphanumeric characters or single hyphens are allowed.
    # Cannot start or end with a hyphen.
    # Can only be 39 characters long.
    if input in ['help', 'about', 'pricing']:
        return ValueError("Input is a protected GitHub name. Please try a different name.")
    validInputRegex = '^[a-zA-Z\d](?:[a-zA-Z\d]|-(?=[a-zA-Z\d])){0,38}$'
    if not re.match(validInputRegex, input):
        raise ValueError("Input is invalid. Valid inputs can contain only "
                         "alphanumeric characters and single hyphens and cannot "
                         "be over 39 characters long.")

def getOrgMembers(orgName):
    # Returns a list of dictionaries of Member information
    # Ex.[{'Username': <username>, 'Real Name': <actual name>, 'Email': None},
    #     {'Username': <username2>, 'Real Name': <actual name2>, 'Email': <email}]

    #check input
    checkInput(orgName)

    authToken = os.getenv('GITHUB_TOKEN')
    headers = {'Authorization': f'token {authToken}'}

    members = []
    errors = []

    #This query to verify the existence of the Organization is technically not required.
    queryUrl = f"https://api.github.com/orgs/{orgName}"
    r = requests.get(queryUrl, headers=headers)
    if r.status_code != 200:
        message = f"Organization '{orgName}' not found."
        if r.status_code >= 400 and r.status_code < 500:
            message += f" Please check that it was spelled correctly.\n{r.text}"
        else:
            message += f" Returned error code {r.status_code}. {r.text}"
        raise ValueError(message)
    orgResult = r.json()
    # pprint(orgResult)

    #End url with 'members' if all members are desired.
    r2 = requests.get(f'https://api.github.com/orgs/{orgName}/public_members', headers=headers)
    if r2.status_code != 200:
        message = f"Members for organization '{orgName}' not found."
        if r2.status_code >= 400 and r.status_code < 500:
            message += f" Please check that it was spelled correctly.\n{r2.text}"
        else:
            message += f" Returned error code {r2.status_code}. {r2.text}"
        raise ValueError(message)
    orgMembersResult = r2.json()
    while 'next' in r2.links.keys():
        r2=requests.get(r2.links['next']['url'],headers=headers)
        if r2.status_code != 200:
            message = f"Further member search pages for organization '{rep.get('name')}' not found."
            message += f"\nReturned error code {r2.status_code}. {r2.text}"
            errors.append(ValueError(message))
            break
        orgMembersResult.extend(r2.json())

    for member in orgMembersResult:
        try:
            members.append(getUserInfo(member.get('login')))
        except Exception as e:
            errors.append(e)

    return members, errors

def getUserInfo(username):
    # Returns a dictionary containing the username, real name, and email (if it exists)
    # Ex. {'Username': <username>, 'Real Name': <actual name>, 'Email': None}
    checkInput(username)
    #run username search
    authToken = os.getenv('GITHUB_TOKEN')
    headers = {'Authorization': f'token {authToken}'}

    queryUrl = f"https://api.github.com/users/{username}"
    r = requests.get(queryUrl, headers=headers)
    if r.status_code != 200:
        message = f"User {username}' not found."
        if r.status_code >= 400 and r.status_code < 500:
            message += f" Please check that it was spelled correctly.\n{r.text}"
        else:
            message += f" Returned error code {r.status_code}. {r.text}"
        raise ValueError(message)
    userInfo = r.json()
    # pprint(userInfo)
    userDict = {'Username': userInfo.get('login'),
                'Real Name': userInfo.get('name'),
                'Email':userInfo.get('email')}

    return userDict

def getReposForUser(username):
    # Parse for repos user has made at least one commit to.
    # Returns dictionary with full repo names as keys with a dictionary
    # containing the number of commits and date of last commit of specified user.
    # ex. {<repoName>: {{'Number of Commits':numberOfCommits, 'Last Commit':latestDate}}}

    checkInput(username)

    repoDict = {}

    authToken = os.getenv('GITHUB_TOKEN')
    headers = {'Authorization': f'token {authToken}'}

    repoQueryUrl = f"https://api.github.com/users/{username}/repos"
    repoParams = {"type": "all"}
    r = requests.get(repoQueryUrl, headers=headers, params=repoParams)
    if r.status_code != 200:
        message = f"Repos for user '{username}' not found."
        if r.status_code >= 400 and r.status_code < 500:
            message += f" Please check that user was spelled correctly.\n{r.text}"
        else:
            message += f" Returned error code{r.status_code}. {r.text}"
        raise ValueError(message)
    repos = r.json()

    errors = []

    for rep in repos:
        # pprint(rep)
        #Counts for commits across all of the repos branches
        numberOfCommits = 0
        latestDate = 0
        try:
            repoOwner = rep['owner']['login']
        except Exception as e:
            errors.append(e)
            continue

        branchQueryUrl = f"https://api.github.com/repos/{repoOwner}/{rep.get('name')}/branches"
        branchParams = {
            "per_page": 100,
            "page": 1
        }
        r2 = requests.get(branchQueryUrl, headers=headers, params=branchParams)
        if r2.status_code != 200:
            message = f"Branches for repo '{rep.get('name')}' not found."
            message += f" Returned error code {r2.status_code}. {r2.text}"
            errors.append(ValueError(message))
            break
        branches = r2.json()
        while 'next' in r2.links.keys():
            r2=requests.get(r2.links['next']['url'],headers=headers)
            if r2.status_code != 200:
                message = f"Further branch search pages for repo '{rep.get('name')}' not found."
                message += f"\nReturned error code {r2.status_code}. {r2.text}"
                errors.append(ValueError(message))
                break
            branches.extend(r2.json())

        for branch in branches:
            # Finding the commits for each branch
            commitQueryUrl = f"https://api.github.com/repos/{repoOwner}/{rep.get('name')}/commits"
            commitParams = {
                "author": username,
                "per_page": 100,
                "page": 1,
                "sha": branch['name']
            }
            r3 = requests.get(commitQueryUrl, headers=headers, params=commitParams)
            if r3.status_code != 200:
                message = f"Commits for branch '{branch.get('name')}' not found."
                message += f" Returned error code {r3.status_code}. {r3.text}"
                errors.append(ValueError(message))
            commits = r3.json()
            # pprint(commits)
            while 'next' in r3.links.keys():
                r3=requests.get(r3.links['next']['url'],headers=headers)
                if r3.status_code != 200:
                    message = f"Further commit search pages for branch '{branch.get('name')}' not found."
                    message += f"\nReturned error code {r3.status_code}. {r3.text}"
                    errors.append(ValueError(message))
                    break
                commits.extend(r3.json())
            # pprint(commits)
            for commit in commits:
                #check if commits exist
                try:
                    if commits.get('message') == 'Git Repository is empty.':
                        continue
                except:
                    pass
                # pprint(commit)

                #check to make sure it belongs to the author and check the time
                try:
                    commitAuthorInfo = commit['commit']['author']
                except TypeError as e:
                    #probably not a real commit/not one attached to a person. Ignore.
                    errors.append(e)
                    # pprint(commit)
                    # pprint(commits)
                    continue
                if commitAuthorInfo.get('name') == username:
                    numberOfCommits += 1
                    dateString = commitAuthorInfo.get('date')
                    # print(dateString) #datestring I'm getting is a day ahead
                    #of what GitHub says sometimes?!
                    commitDate = datetime.strptime(dateString, "%Y-%m-%dT%H:%M:%SZ")
                    if not latestDate:
                        latestDate = commitDate
                    elif commitDate > latestDate:
                        latestDate = commitDate

            # pprint(commits)
        # At least one commit from the user was in the repo
        if numberOfCommits:
            #full name listed instead of just name, in case there are multiple of the same name repo
            repoDict[rep.get('full_name')] = {'Number of Commits':numberOfCommits,
                                          'Last Commit':latestDate}
            # print(f"Repo: {rep['full_name']}\n\tNumber of Commits: {numberOfCommits}\n\tLast Commit: {latestDate}")

    return repoDict, errors

################################## View ########################################

### Command line View ####

def printUserInfo(userDict):
    line = "Username: "
    line += f"{userDict.get('Username')}\t" if userDict.get('Username') else "     \t"
    line += 'Real Name: '
    line += f"{userDict.get('Real Name')}\t" if userDict.get('Real Name') else "     \t"

    if userDict.get('Email'):
        line +=f"\tEmail: {userDict.get('Email')}"
    print(line)


def cmdMain(args):
    print("Welcome to this simple GitHub search. I hope you find what you are looking for!\n")
    print("Before starting, please make sure to add the environment variable "
          "'GITHUB_TOKEN' with a personal access token generated at "
          "'https://github.com/settings/tokens' as the value. Then restart the "
          "terminal and rerun the program.\n\n")
    print("Ready?\n")
    time.sleep(1)
    print("Pefect!")
    time.sleep(1)

    keepGoing = True

    while(keepGoing):
        print("\n\n***********************************************************\n\n")
        print("What kind of search would you like to run?")
        print("(Enter 'O'/'o' to list the members of a GitHub organization.\n"
              "Enter 'U'/'u' to list repositories and commit counts of a GitHub user.\n"
              "Enter 'exit' to end the program.)")
        typeOfQuery = str(input())
        typeOfQuery = typeOfQuery.strip().lower()
        if typeOfQuery == 'o':
            print("Enter GitHub organization name to search:")
            print("(Enter '-r' to restart search)")
            orgName = str(input())
            if orgName == '-r':
                continue

            print("This may take some time. Thank you for your patience!")
            try:
                mDict, errors = getOrgMembers(orgName)
                print(f"\nMembers for '{orgName}':")
                if mDict:
                    for m in mDict:
                        printUserInfo(m)
                    print(f"\nTotal members for organization '{orgName}': {len(mDict)}")
                else:
                    print(f"\nNo public members for organization '{orgName}'")
                print("")
                for e in errors:
                    print(str(e))
            except Exception as err:
                print(f"\nCould not obtain members for organization '{orgName}'\n{str(err)}")

        elif typeOfQuery == 'u':
            print("Enter GitHub username to search:")
            print("(Enter '-r' to restart search)")
            username = str(input())

            if username == '-r':
                continue

            print("This may take some time. Thank you for your patience!")
            try:
                uDict = getUserInfo(username)
                rDict, errors2 = getReposForUser(username)
                #numbers and dates are off by one sometimes...
                print("")
                printUserInfo(uDict)

                if rDict:
                    print("\nRepos committed to:\n")
                    for r in rDict:
                        print(f"Repo: {r}\tNumber of Commits: {rDict[r]['Number of Commits']}\tLast Commit: {rDict[r]['Last Commit']}")
                else:
                    print("No repos with commits found for user")

                print("")
                for e2 in errors2:
                    print(str(e2))

            except Exception as err2:
                    print(f"Could not obtain repositories for user '{username}'\n{str(err2)}")

        elif typeOfQuery == 'exit':
            print("\n\nHope you found what you were looking for. Have a fantastic day!")
            keepGoing = False
        else:
            print("\n\nInput isn't recognized. Please use one of the propper cues.")


def guiMain(args):
    print("GUI version is not implemented. Going to command line version.")
    cmdMain(args)



################################### Startup ####################################
# __name__
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-g','--gui', action='store_true',
                        help='Include to run with GUI. Default is command line.')
    args = vars(parser.parse_args(sys.argv[1:]))
    print(args)
    if args['gui']:
        guiMain(args)
    else:
        cmdMain(args)
