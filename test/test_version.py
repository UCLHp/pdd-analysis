import requests
from urllib.request import urlopen, URLError

def get_last_master_commit(repo_url):
    """Return hash key of latest commit on master branch
    of given github repository"""

    url = repo_url + "/tree/master"
    page = requests.get(url).text
    lines = page.split("\n")

    for line in lines:
        if "Permalink" in line:
            commit_href = line[line.find("href")+6:line.find("\">")]
            commit = commit_href.split("/")[-1]
            return commit

def internet_on():
    '''Confirms if user can access the internet'''

    try:
        response=urlopen('http://github.com/UCLHp/Spot_Analysis',timeout=20)
        return True
    except URLError as err: pass
    return False

# selfhash should be updated for each release of a new executable
# if this is not updated after a further commit to the master branch
# a warning will be flagged to the user.

def check_version():
    print('Checking latest version release...\n')

    selfhash = '744921a011180d35c18d8bfdcae53c649eea4653'

    if internet_on():
        print('Internet connection established\n')
        repo = 'http://github.com/UCLHp/Spot_Analysis'
        githash = get_last_master_commit(repo)
        if not githash == selfhash:
            print('VERSION NOT CONFIRMED')
            print('Please check latest version on GitHub')
            input('Press enter to continue')
        else:
            print("Version Confirmed\n")

    else:
        print('No internet connection detected')
        print('VERSION NOT CONFIRMED')
        print('Please check latest version on GitHub')
        input('Press enter to continue')

if __name__ == '__main__':
    check_version()
