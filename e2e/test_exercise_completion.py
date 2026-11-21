import pytest
from playwright.sync_api import expect

from e2e.journeys import complete_exercise, sign_in, sign_out, start_exercise


def test_guest_completes_exercise(page, base_url, exercise, feedback_enabled):
    start_exercise(page, exercise)
    complete_exercise(page, exercise, base_url)
    expect(page.locator(".signup-prompt-container")).to_be_visible()
    page.reload()
    expect(page.locator(".completion-summary")).to_be_visible()


@pytest.mark.account
def test_signed_in_completion_survives_login(
    page, base_url, exercise, credentials, clean_account_exercise, feedback_enabled
):
    start_exercise(page, exercise)
    complete_exercise(page, exercise, base_url)
    expect(page.locator(".signup-prompt-container")).to_have_count(0)
    sign_out(page)
    sign_in(page, credentials, base_url)
    page.goto(exercise["path"])
    expect(page.locator(".completion-summary")).to_be_visible()
