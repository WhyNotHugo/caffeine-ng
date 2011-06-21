from bzrlib import branch, urlutils

def pre_commit_script(local, master, old_revno, old_revid, future_revno, future_revid, tree_delta, future_tree):
    """This hook will execute precommit script from root path of the bazaar
    branch. Commit will be canceled if precommit fails."""

    import os, subprocess
    from bzrlib import errors

    base = urlutils.local_path_from_url((local if local else master).base)
    script = os.path.join(base, "precommit")
    # this hook only makes sense if a precommit file exist.
    if not os.path.exists(script):
        return
    try:
        subprocess.check_call(script)

    # if precommit fails (process return not zero) cancel commit.
    except subprocess.CalledProcessError:
        raise errors.BzrError("pre commit check failed.")

branch.Branch.hooks.install_named_hook(
        'pre_commit', pre_commit_script,
        'pre_commit_script (runs "precommit" script in branch root)')


