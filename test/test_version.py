import requests
from urllib.request import urlopen, URLError

URL = "https://github.com/UCLHp/pdd-analysis"
MASTER_HASH = "64ea656a7c35c61c05d8d2597992a4317443f9f8"

# MASTER_HASH should be updated for each release of a new executable.
# If this is not updated after a further commit to the master branch
# a warning will be flagged to the user.



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
        response=urlopen(URL,timeout=20)
        return True
    except URLError as err: pass
    return False


def check_version():
    print('Checking latest version release...\n')

    if internet_on():
        print('Internet connection established\n')
        repo = URL
        githash = get_last_master_commit(repo)
        if not githash == MASTER_HASH:
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
