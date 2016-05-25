import json
import os
from optparse import OptionParser
import requests
import sys
import logging as log

API_URL = 'https://api.github.com/repos/{}/{}/releases'
UPLOAD_URL = 'https://api.github.com/repos/{}/{}/releases'


class GitHubRelease(object):
    def __init__(self, in_user, in_owner, in_repo, in_password='x-oauth-basic'):
        self.user = in_user
        self.password = in_password
        self.repo = in_repo
        self.url = API_URL.format(in_owner, in_repo)
        self.upload_url = UPLOAD_URL.format(in_owner, in_repo)

    def get_releases(self):
        releases_response = requests.get(self.url, auth=(self.user, self.password))
        return json.loads(releases_response.text)

    def create_release(self, tag, name=None, description=None, draft=False, prerelease=False):
        data = {
            "tag_name": tag,
            "target_commitish": "master",
            "name": name if name else tag,
            "body": description if description else tag,
            "draft": draft,
            "prerelease": prerelease
        }
        json_data = json.dumps(data)
        response = requests.post(self.url, data=json_data, auth=(self.user, self.password))
        json_response = json.loads(response.text)
        if json_response.get('errors') or json_response.get('message'):
            log.error(response.text)
            return False
        else:
            print("Successfully created release {} for {}".format(tag, self.repo))
            return True

    def find_id_for_tag(self, release_id):
        all_releases = self.get_releases()
        for release in all_releases:
            if release.get('tag_name') == release_id:
                return release.get('id')
        return None

    def delete_release(self, tag_name):
        release_id = self.find_id_for_tag(tag_name)
        if not release_id:
            log.error("Could not find release for tag name: {}".format(tag_name))
            return False
        response = requests.delete('{}/{}'.format(self.url, release_id),
                                   auth=(self.user, self.password))
        response.raise_for_status()
        print "Successfully deleted release {}".format(tag_name)
        return True

    def upload_artifacts_for(self, tag_name):
        release_id = self.find_id_for_tag(tag_name)
        artifact_name = '{}-1.0.{}.tar.gz'.format(self.repo, os.environ['BUILD_NUMBER'])
        upload_url = '{}/{}/assets?name={}'.format(self.upload_url, release_id, artifact_name)
        f = open('/opt/deployments/{}'.format(artifact_name))
        upload_response = requests.post(upload_url,
                                        data=f,
                                        headers={'Content-Type': 'application/x-tar'},
                                        auth=(self.user, self.password))
        upload_response.raise_for_status()
        return True

    def download_artifacts_for(self, tag_name, artifact_name):
        release_id = self.find_id_for_tag(tag_name)
        all_assets_url = '{}/{}/assets'.format(self.url, release_id)
        all_assets = requests.get(url=all_assets_url, auth=(self.user, self.password))
        all_assets = json.loads(all_assets.text)
        for asset in all_assets:
            if asset['name'] == artifact_name:
                temp_file_name = '/tmp/{}'.format(artifact_name)
                print 'Archive file name: {}'.format(temp_file_name)
                with open(temp_file_name, 'wb') as handle:
                    asset_response = requests.get(url=asset['url'],
                                                  headers={'Accept': 'application/octet-stream'},
                                                  auth=(self.user, self.password))
                    asset_response.raise_for_status()
                    for block in asset_response.iter_content(1024):
                        if not block:
                            break
                        handle.write(block)

        return True

    def list_artifacts_for(self, tag_name):
        release_id = self.find_id_for_tag(tag_name)
        artifacts = requests.get('{}/{}/assets?'.format(self.url, release_id),
                                 auth=(self.user, self.password))
        print artifacts


if __name__ == "__main__":
    parser = OptionParser(usage='usage: %prog [options] arguments', add_help_option=False)
    parser.add_option("-c", "--create", action="store_true", dest="create")
    parser.add_option("-d", "--delete", action="store_true", dest="delete")
    parser.add_option("-u", "--upload_artifact", action="store_true", dest="upload_artifact")
    parser.add_option("-g", "--download_artifact", action="store_true", dest="download_artifact")
    parser.add_option("-l", "--list_artifacts", action="store_true", dest="list_artifacts")
    parser.add_option("-t", "--token", dest="git_hub_token")
    parser.add_option("-o", "--owner", dest="owner")
    parser.add_option("-r", "--repo", dest="repo")
    (options, args) = parser.parse_args()
    if options.git_hub_token is None or options.owner is None or options.repo is None:
        parser.print_help()
        print ''
        print 'Example:'
        print 'github_releases.py -t 23764532754287434 -o AutomationIntegration -r bpi'
        sys.exit(-1)
    elif not os.environ.get('BUILD_NUMBER'):
        print 'Please set BUILD_NUMBER environment variable'
        sys.exit(-1)

    gh_release = GitHubRelease(options.git_hub_token, options.owner, options.repo)
    try:
        if options.create:
            result = gh_release.create_release("v1.0.{}".format(os.environ['BUILD_NUMBER']))
        elif options.delete:
            for i in range(250, 280):
                try:
                    result = gh_release.delete_release("v1.0.{}".format(str(i)))
                except:
                    pass
        elif options.list_artifacts:
            result = gh_release.list_artifacts_for("v1.0.{}".format(os.environ['BUILD_NUMBER']))
        elif options.upload_artifact:
            result = gh_release.upload_artifacts_for("v1.0.{}".format(os.environ['BUILD_NUMBER']))
        elif options.download_artifact:
            result = gh_release.download_artifacts_for(os.environ['RELEASE_NAME'],
                                                       os.environ['ARTIFACT_NAME'])
        else:
            result = gh_release.get_releases()
            print('Releases: {}'.format(str(result)))

        if result:
            sys.exit()
        else:
            sys.exit(-2)
    except Exception as exc:
        log.error(exc.message)
        sys.exit(-2)