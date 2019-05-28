# Copyright (c) ACSONE SA/NV 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import subprocess

from .. import github
from ..manifest import bump_manifest_version, git_modified_addons
from ..queue import getLogger, task
from ..version_branch import make_merge_bot_branch
from .main_branch_bot import main_branch_bot_actions

_logger = getLogger(__name__)


@task()
def merge_bot_start(org, repo, pr, username, bumpversion=None, dry_run=False):
    # TODO error handling
    with github.login() as gh:
        if not github.git_user_can_push(gh.repository(org, repo), username):
            return
        target_branch = gh.pull_request(org, repo, pr).base.ref
    with github.temporary_clone(org, repo, target_branch):
        # create merge bot branch from PR and rebase it on target branch
        merge_bot_branch = make_merge_bot_branch(pr, target_branch)
        subprocess.check_output(
            ["git", "fetch", "origin", f"pull/{pr}/head:{merge_bot_branch}"]
        )
        subprocess.check_output(["git", "checkout", merge_bot_branch])
        subprocess.check_output(["git", "rebase", target_branch])
        # run main branch bot actions
        main_branch_bot_actions(org, repo, target_branch, dry_run)
        if bumpversion:
            for addon in git_modified_addons(".", target_branch):
                bump_manifest_version(addon, bumpversion, git_commit=True)
        # push
        subprocess.check_call(["git", "push", "--force", "origin", merge_bot_branch])


@task()
def merge_bot_status_error(org, repo, merge_bot_branch):
    # TODO
    pass


@task()
def merge_bot_status_ok(org, repo, merge_bot_branch):
    # TODO
    pass
