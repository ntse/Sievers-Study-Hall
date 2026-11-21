import pytest
from playwright.sync_api import expect

from e2e.journeys import reset_exercise, set_feedback, start_exercise, submit_answer


def test_incorrect_answer_does_not_advance_progress(page, exercise, feedback_enabled):
    start_exercise(page, exercise)
    submit_answer(page, "definitely-incorrect")
    expect(page.locator(".feedback-incorrect-container")).to_be_visible()
    expect(page.locator(".question-count")).to_contain_text(
        f"0/{len(exercise['answers'])}"
    )
    page.locator(".next-question-button").click()
    question_id = page.locator('input[name="nr"]').input_value()
    submit_answer(page, exercise["answers"][question_id])
    expect(page.locator(".feedback-correct-container")).to_be_visible()
    expect(page.locator(".question-count")).to_contain_text(
        f"1/{len(exercise['answers'])}"
    )


def test_guest_progress_survives_reload_and_can_reset(page, exercise, feedback_enabled):
    start_exercise(page, exercise)
    question_id = page.locator('input[name="nr"]').input_value()
    submit_answer(page, exercise["answers"][question_id])
    page.reload()
    expect(page.locator(".question-count")).to_contain_text(
        f"1/{len(exercise['answers'])}"
    )
    reset_exercise(page, exercise)
    start_exercise(page, exercise)
    expect(page.locator(".question-count")).to_contain_text(
        f"0/{len(exercise['answers'])}"
    )


@pytest.mark.account
def test_signed_in_partial_progress_survives_login(
    page, base_url, exercise, credentials, clean_account_exercise, feedback_enabled
):
    from e2e.journeys import sign_in, sign_out

    start_exercise(page, exercise)
    question_id = page.locator('input[name="nr"]').input_value()
    submit_answer(page, exercise["answers"][question_id])
    sign_out(page)
    sign_in(page, credentials, base_url)
    start_exercise(page, exercise)
    expect(page.locator(".question-count")).to_contain_text(
        f"1/{len(exercise['answers'])}"
    )
    assert page.locator('input[name="nr"]').input_value() != question_id


def test_feedback_can_be_disabled(page, base_url, exercise, feedback_enabled):
    set_feedback(page, False)
    page.reload()
    expect(page.locator("#intermediate-feedback-page-toggle")).not_to_be_checked()
    start_exercise(page, exercise)
    question_id = page.locator('input[name="nr"]').input_value()
    submit_answer(page, exercise["answers"][question_id])
    expect(page).to_have_url(base_url + exercise["path"])
    expect(page.locator(".question-count")).to_contain_text(
        f"1/{len(exercise['answers'])}"
    )
    expect(page.locator("#input-answer")).to_be_visible()
