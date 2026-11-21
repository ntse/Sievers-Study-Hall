import pytest
from playwright.sync_api import expect

from e2e.journeys import sign_out


@pytest.mark.smoke
def test_home_and_login_are_reachable(page, base_url):
    response = page.goto("/?lang=en")
    assert response.status == 200
    expect(page.get_by_role("link", name="Logo")).to_be_visible()
    response = page.goto("/signin?lang=en")
    assert response.status == 200
    expect(page.locator("#email")).to_be_visible()
    expect(page.locator("#password")).to_have_attribute("type", "password")


def test_invalid_credentials_are_rejected(page, base_url):
    page.goto("/signin?lang=en")
    page.locator("#email").fill("nonexistent-e2e-user@example.invalid")
    page.locator("#password").fill("invalid-e2e-password")
    page.get_by_role("button", name="Sign in", exact=True).click()
    expect(page).to_have_url(base_url + "/signin")
    expect(page.get_by_text("Invalid email or password.")).to_be_visible()
    page.goto("/settings?lang=en")
    expect(page.get_by_role("button", name="Sign out", exact=True)).to_have_count(0)


@pytest.mark.account
def test_login_redirect_and_logout(signed_in, base_url):
    signed_in.goto("/signin")
    expect(signed_in).to_have_url(base_url + "/settings")
    sign_out(signed_in)
    signed_in.goto("/signin?lang=en")
    expect(signed_in.locator("#email")).to_be_visible()
