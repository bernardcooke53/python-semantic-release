import base64
import mimetypes
import os
import re
from unittest import mock
from urllib.parse import urlencode

import pytest
import requests_mock
from requests import Session

from semantic_release.hvcs.gitea import Gitea
from semantic_release.hvcs.token_auth import TokenAuth
from tests.const import EXAMPLE_REPO_NAME, EXAMPLE_REPO_OWNER
from tests.helper import netrc_file


@pytest.fixture
def default_gitea_client():
    remote_url = f"git@gitea.com:{EXAMPLE_REPO_OWNER}/{EXAMPLE_REPO_NAME}.git"
    yield Gitea(remote_url=remote_url)


@pytest.mark.parametrize(
    (
        "patched_os_environ, hvcs_domain, hvcs_api_domain, token_var, "
        "expected_hvcs_domain, expected_hvcs_api_domain, expected_token"
    ),
    [
        ({}, None, None, "", Gitea.DEFAULT_DOMAIN, Gitea.DEFAULT_API_DOMAIN, None),
        (
            {"GITEA_SERVER_URL": "https://special.custom.server/vcs/"},
            None,
            None,
            "",
            "special.custom.server/vcs/",
            Gitea.DEFAULT_API_DOMAIN,
            None,
        ),
        (
            {"GITEA_API_URL": "https://api.special.custom.server/"},
            None,
            None,
            "",
            Gitea.DEFAULT_DOMAIN,
            "api.special.custom.server/",
            None,
        ),
        (
            {},
            None,
            None,
            "GITEA_TOKEN",
            Gitea.DEFAULT_DOMAIN,
            Gitea.DEFAULT_API_DOMAIN,
            None,
        ),
        (
            {"GH_TOKEN": "abc123"},
            None,
            None,
            "GITEA_TOKEN",
            Gitea.DEFAULT_DOMAIN,
            Gitea.DEFAULT_API_DOMAIN,
            None,
        ),
        (
            {"GL_TOKEN": "abc123"},
            None,
            None,
            "GITEA_TOKEN",
            Gitea.DEFAULT_DOMAIN,
            Gitea.DEFAULT_API_DOMAIN,
            None,
        ),
        (
            {"GITEA_TOKEN": "aabbcc"},
            None,
            None,
            "GITEA_TOKEN",
            Gitea.DEFAULT_DOMAIN,
            Gitea.DEFAULT_API_DOMAIN,
            "aabbcc",
        ),
        (
            {"PSR__GIT_TOKEN": "aabbcc"},
            None,
            None,
            "PSR__GIT_TOKEN",
            Gitea.DEFAULT_DOMAIN,
            Gitea.DEFAULT_API_DOMAIN,
            "aabbcc",
        ),
        (
            {"GITEA_SERVER_URL": "https://special.custom.server/vcs/"},
            "https://example.com",
            None,
            "",
            "https://example.com",
            Gitea.DEFAULT_API_DOMAIN,
            None,
        ),
        (
            {"GITEA_API_URL": "https://api.special.custom.server/"},
            None,
            "https://api.example.com",
            "",
            Gitea.DEFAULT_DOMAIN,
            "https://api.example.com",
            None,
        ),
    ],
)
@pytest.mark.parametrize(
    "remote_url",
    [
        f"git@gitea.com:{EXAMPLE_REPO_OWNER}/{EXAMPLE_REPO_NAME}.git",
        f"https://gitea.com/{EXAMPLE_REPO_OWNER}/{EXAMPLE_REPO_NAME}.git",
    ],
)
def test_gitea_client_init(
    patched_os_environ,
    hvcs_domain,
    hvcs_api_domain,
    token_var,
    expected_hvcs_domain,
    expected_hvcs_api_domain,
    expected_token,
    remote_url,
):
    with mock.patch.dict(os.environ, patched_os_environ, clear=True):
        client = Gitea(
            remote_url=remote_url,
            hvcs_domain=hvcs_domain,
            hvcs_api_domain=hvcs_api_domain,
            token_var=token_var,
        )

        assert client.hvcs_domain == expected_hvcs_domain
        assert client.hvcs_api_domain == expected_hvcs_api_domain
        assert client.api_url == f"https://{client.hvcs_api_domain}"
        assert client.token == expected_token
        assert client._remote_url == remote_url
        assert hasattr(client, "session") and isinstance(
            getattr(client, "session", None), Session
        )


def test_gitea_get_repository_owner_and_name(default_gitea_client):
    assert (
        default_gitea_client._get_repository_owner_and_name()
        == super(Gitea, default_gitea_client)._get_repository_owner_and_name()
    )


@pytest.mark.parametrize(
    "use_token, token, _remote_url, expected",
    [
        (
            False,
            "",
            "git@gitea.com:custom/example.git",
            "git@gitea.com:custom/example.git",
        ),
        (
            True,
            "",
            "git@gitea.com:custom/example.git",
            "git@gitea.com:custom/example.git",
        ),
        (
            False,
            "aabbcc",
            "git@gitea.com:custom/example.git",
            "git@gitea.com:custom/example.git",
        ),
        (
            True,
            "aabbcc",
            "git@gitea.com:custom/example.git",
            "https://aabbcc@gitea.com/custom/example.git",
        ),
        (
            False,
            "aabbcc",
            "git@gitea.com:custom/example.git",
            "git@gitea.com:custom/example.git",
        ),
        (
            True,
            "aabbcc",
            "git@gitea.com:custom/example.git",
            "https://aabbcc@gitea.com/custom/example.git",
        ),
    ],
)
def test_remote_url(default_gitea_client, use_token, token, _remote_url, expected):
    default_gitea_client._remote_url = _remote_url
    default_gitea_client.token = token
    assert default_gitea_client.remote_url(use_token=use_token) == expected


def test_commit_hash_url(default_gitea_client):
    sha = "hashashash"
    assert default_gitea_client.commit_hash_url(
        sha
    ) == "https://{domain}/{owner}/{repo}/commit/{sha}".format(
        domain=default_gitea_client.hvcs_domain,
        owner=default_gitea_client.owner,
        repo=default_gitea_client.repo_name,
        sha=sha,
    )


@pytest.mark.parametrize("pr_number", (420, "420"))
def test_pull_request_url(default_gitea_client, pr_number):
    assert default_gitea_client.pull_request_url(
        pr_number=pr_number
    ) == "https://{domain}/{owner}/{repo}/pulls/{pr_number}".format(
        domain=default_gitea_client.hvcs_domain,
        owner=default_gitea_client.owner,
        repo=default_gitea_client.repo_name,
        pr_number=pr_number,
    )


def test_asset_upload_url(default_gitea_client):
    assert default_gitea_client.asset_upload_url(
        release_id=420
    ) == "https://{domain}/repos/{owner}/{repo}/releases/{release_id}/assets".format(
        domain=default_gitea_client.hvcs_api_domain,
        owner=default_gitea_client.owner,
        repo=default_gitea_client.repo_name,
        release_id=420,
    )


############
# Tests which need http response mocking
############


gitea_matcher = re.compile(rf"^https://{Gitea.DEFAULT_DOMAIN}")
gitea_api_matcher = re.compile(rf"^https://{Gitea.DEFAULT_API_DOMAIN}")


@pytest.mark.parametrize(
    "resp_payload, status_code, expected",
    [
        ({"status": "success"}, 200, True),
        ({"status": "pending"}, 200, False),
        ({"status": "failed"}, 200, False),
        ([{"status": "success"}] * 2, 200, True),
        ([{"status": "pending"}] * 2, 200, False),
        ([{"status": "failed"}] * 2, 200, False),
        ({}, 404, False),
    ],
)
def test_check_build_status(default_gitea_client, resp_payload, status_code, expected):
    ref = "refA"
    with requests_mock.Mocker(session=default_gitea_client.session) as m:
        m.register_uri(
            "GET", gitea_api_matcher, json=resp_payload, status_code=status_code
        )
        assert default_gitea_client.check_build_status(ref) == expected
        assert m.called
        assert len(m.request_history) == 1
        assert m.last_request.method == "GET"
        assert (
            m.last_request.url
            == "{api_url}/repos/{owner}/{repo_name}/statuses/{ref}".format(
                api_url=default_gitea_client.api_url,
                owner=default_gitea_client.owner,
                repo_name=default_gitea_client.repo_name,
                ref=ref,
            )
        )


@pytest.mark.parametrize(
    "status_code, expected",
    [
        (201, True),
        (400, False),
        (409, False),
    ],
)
@pytest.mark.parametrize("prerelease", (True, False))
def test_create_release(default_gitea_client, status_code, prerelease, expected):
    tag = "v1.0.0"
    changelog = "# TODO: Changelog"
    with requests_mock.Mocker(session=default_gitea_client.session) as m:
        m.register_uri(
            "POST", gitea_api_matcher, json={"status": "ok"}, status_code=status_code
        )
        assert (
            default_gitea_client.create_release(tag, changelog, prerelease) == expected
        )
        assert m.called
        assert len(m.request_history) == 1
        assert m.last_request.method == "POST"
        assert (
            m.last_request.url
            == "{api_url}/repos/{owner}/{repo_name}/releases".format(
                api_url=default_gitea_client.api_url,
                owner=default_gitea_client.owner,
                repo_name=default_gitea_client.repo_name,
            )
        )
        assert m.last_request.json() == {
            "tag_name": tag,
            "name": tag,
            "body": changelog,
            "draft": False,
            "prerelease": prerelease,
        }


@pytest.mark.parametrize("token", (None, "super-token"))
def test_should_create_release_using_token_or_netrc(default_gitea_client, token):
    default_gitea_client.token = token
    default_gitea_client.session.auth = None if not token else TokenAuth(token)
    tag = "v1.0.0"
    changelog = "# TODO: Changelog"

    # Note write netrc file with DEFAULT_DOMAIN not DEFAULT_API_DOMAIN as can't
    # handle /api/v1 in file
    with requests_mock.Mocker(session=default_gitea_client.session) as m, netrc_file(
        machine=default_gitea_client.DEFAULT_DOMAIN
    ) as netrc, mock.patch.dict(os.environ, {"NETRC": netrc.name}, clear=True):

        m.register_uri("POST", gitea_api_matcher, json={}, status_code=201)
        assert default_gitea_client.create_release(tag, changelog)
        assert m.called
        assert len(m.request_history) == 1
        assert m.last_request.method == "POST"
        if not token:
            assert {
                "Authorization": "Basic "
                + base64.encodebytes(
                    f"{netrc.login_username}:{netrc.login_password}".encode()
                )
                .decode("ascii")
                .strip()
            }.items() <= m.last_request.headers.items()
        else:
            assert {
                "Authorization": f"token {token}"
            }.items() <= m.last_request.headers.items()
        assert (
            m.last_request.url
            == "{api_url}/repos/{owner}/{repo_name}/releases".format(
                api_url=default_gitea_client.api_url,
                owner=default_gitea_client.owner,
                repo_name=default_gitea_client.repo_name,
            )
        )
        assert m.last_request.json() == {
            "tag_name": tag,
            "name": tag,
            "body": changelog,
            "draft": False,
            "prerelease": False,
        }


def test_request_has_no_auth_header_if_no_token_or_netrc():
    with mock.patch.dict(os.environ, {}, clear=True):
        client = Gitea(remote_url="git@gitea.com:something/somewhere.git")

        with requests_mock.Mocker(session=client.session) as m:
            m.register_uri("POST", gitea_api_matcher, json={}, status_code=201)
            assert client.create_release("v1.0.0", "# TODO: Changelog")
            assert m.called
            assert len(m.request_history) == 1
            assert m.last_request.method == "POST"
            assert (
                m.last_request.url
                == "{api_url}/repos/{owner}/{repo_name}/releases".format(
                    api_url=client.api_url,
                    owner=client.owner,
                    repo_name=client.repo_name,
                )
            )
            assert "Authorization" not in m.last_request.headers


@pytest.mark.parametrize(
    "resp_payload, status_code, expected",
    [
        ({"id": 420}, 200, 420),
        ({}, 404, None),
    ],
)
def test_get_release_id_by_tag(
    default_gitea_client, resp_payload, status_code, expected
):
    tag = "v1.0.0"
    with requests_mock.Mocker(session=default_gitea_client.session) as m:
        m.register_uri(
            "GET", gitea_api_matcher, json=resp_payload, status_code=status_code
        )
        assert default_gitea_client.get_release_id_by_tag(tag) == expected
        assert m.called
        assert len(m.request_history) == 1
        assert m.last_request.method == "GET"
        assert (
            m.last_request.url
            == "{api_url}/repos/{owner}/{repo_name}/releases/tags/{tag}".format(
                api_url=default_gitea_client.api_url,
                owner=default_gitea_client.owner,
                repo_name=default_gitea_client.repo_name,
                tag=tag,
            )
        )


@pytest.mark.parametrize(
    "status_code, expected",
    [
        (201, True),
        (400, False),
        (404, False),
        (429, False),
        (500, False),
        (503, False),
    ],
)
def test_edit_release_changelog(default_gitea_client, status_code, expected):
    release_id = 420
    changelog = "# TODO: Changelog"
    with requests_mock.Mocker(session=default_gitea_client.session) as m:
        m.register_uri("PATCH", gitea_api_matcher, json={}, status_code=status_code)
        assert default_gitea_client.edit_release_changelog(420, changelog) == expected
        assert m.called
        assert len(m.request_history) == 1
        assert m.last_request.method == "PATCH"
        assert (
            m.last_request.url
            == "{api_url}/repos/{owner}/{repo_name}/releases/{release_id}".format(
                api_url=default_gitea_client.api_url,
                owner=default_gitea_client.owner,
                repo_name=default_gitea_client.repo_name,
                release_id=release_id,
            )
        )
        assert m.last_request.json() == {"body": changelog}


# Note - mocking as the logic for the create/update of a release
# is covered by testing above, no point re-testing.
@pytest.mark.parametrize(
    "create_release_success, release_id, edit_release_success, expected",
    [
        (True, 420, True, True),
        (True, 420, False, True),
        (False, 420, True, True),
        (False, 420, False, False),
        (False, None, True, False),
        (False, None, False, False),
    ],
)
def test_create_or_update_release(
    default_gitea_client,
    create_release_success,
    release_id,
    edit_release_success,
    expected,
):
    tag = "v1.0.0"
    changelog = "# TODO: Changelog"
    with mock.patch.object(
        default_gitea_client, "create_release"
    ) as mock_create_release, mock.patch.object(
        default_gitea_client, "get_release_id_by_tag"
    ) as mock_get_release_id_by_tag, mock.patch.object(
        default_gitea_client, "edit_release_changelog"
    ) as mock_edit_release_changelog:
        mock_create_release.return_value = create_release_success
        mock_get_release_id_by_tag.return_value = release_id
        mock_edit_release_changelog.return_value = edit_release_success
        # client = Gitea(remote_url="git@gitea.com:something/somewhere.git")
        assert default_gitea_client.create_or_update_release(tag, changelog) == expected
        mock_create_release.assert_called_once_with(tag, changelog)
        if not create_release_success:
            mock_get_release_id_by_tag.assert_called_once_with(tag)
        if not create_release_success and release_id:
            mock_edit_release_changelog.assert_called_once_with(release_id, changelog)
        elif not create_release_success and not release_id:
            mock_edit_release_changelog.assert_not_called()


@pytest.mark.parametrize(
    "status_code, expected",
    [
        (201, True),
        (400, False),
        (500, False),
        (503, False),
    ],
)
def test_upload_asset(
    default_gitea_client, example_changelog_md, status_code, expected
):
    release_id = 420
    urlparams = {"name": example_changelog_md.name}
    with requests_mock.Mocker(session=default_gitea_client.session) as m:
        m.register_uri(
            "POST", gitea_api_matcher, json={"status": "ok"}, status_code=status_code
        )
        assert (
            default_gitea_client.upload_asset(
                release_id=release_id,
                file=example_changelog_md.resolve(),
                label="doesn't matter could be None",
            )
            == expected
        )
        assert m.called
        assert len(m.request_history) == 1
        assert m.last_request.method == "POST"
        assert m.last_request.url == "{url}?{params}".format(
            url=default_gitea_client.asset_upload_url(release_id),
            params=urlencode(urlparams),
        )

        # TODO: this feels brittle
        changelog_text = m.last_request.body.split(b"\r\n")[4]
        assert changelog_text == example_changelog_md.read_bytes()


# Note - mocking as the logic for uploading an asset
# is covered by testing above, no point re-testing.
def test_upload_dists_when_release_id_not_found(default_gitea_client):
    tag = "v1.0.0"
    path = "doesn't matter"
    with mock.patch.object(
        default_gitea_client, "get_release_id_by_tag"
    ) as mock_get_release_id_by_tag, mock.patch.object(
        default_gitea_client, "upload_asset"
    ) as mock_upload_asset:
        mock_get_release_id_by_tag.return_value = None
        assert not default_gitea_client.upload_dists(tag, path)
        mock_get_release_id_by_tag.assert_called_once_with(tag=tag)
        mock_upload_asset.assert_not_called()


@pytest.mark.parametrize(
    "files, upload_statuses, expected",
    [
        (["foo.zip", "bar.whl"], [True, False], False),
        (["foo.whl", "foo.egg", "foo.tar.gz"], [True, True, True], True),
        # What if not built?
        ([], [], True),
        # What if wrong directory/other stuff in output dir/subfolder?
        (["specialconfig.yaml", "something.whl", "desc.md"], [True, True, True], True),
    ],
)
def test_upload_dists_when_release_id_found(
    default_gitea_client, files, upload_statuses, expected
):
    release_id = 420
    tag = "doesn't matter"
    path = "doesn't matter"
    with mock.patch.object(
        default_gitea_client, "get_release_id_by_tag"
    ) as mock_get_release_id_by_tag, mock.patch.object(
        default_gitea_client, "upload_asset"
    ) as mock_upload_asset, mock.patch.object(
        os, "listdir"
    ) as mock_os_listdir, mock.patch.object(
        os.path, "isfile"
    ) as mock_os_path_isfile:
        # Skip check as the filenames deliberately don't exists for testing
        mock_os_path_isfile.return_value = True
        mock_os_listdir.return_value = files
        mock_get_release_id_by_tag.return_value = release_id

        mock_upload_asset.side_effect = upload_statuses
        assert default_gitea_client.upload_dists(tag, path) == expected
        mock_get_release_id_by_tag.assert_called_once_with(tag=tag)
        assert [
            mock.call(release_id, os.path.join(path, fn)) for fn in files
        ] == mock_upload_asset.call_args_list
