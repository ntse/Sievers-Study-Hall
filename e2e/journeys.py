from playwright.sync_api import expect


def sign_in(page, credentials, base_url):
    page.goto("/signin?lang=en")
    page.locator("#email").fill(credentials[0])
    page.locator("#password").fill(credentials[1])
    page.get_by_role("button", name="Sign in", exact=True).click()
    expect(page).to_have_url(base_url + "/")
    page.goto("/settings?lang=en")
    expect(page.get_by_role("button", name="Sign out", exact=True)).to_be_visible()
    expect(page.locator("body")).to_contain_text(credentials[0])


def sign_out(page):
    page.goto("/settings?lang=en")
    page.get_by_role("button", name="Sign out", exact=True).click()
    page.goto("/settings?lang=en")
    expect(page.get_by_role("button", name="Sign out", exact=True)).to_have_count(0)


def start_exercise(page, exercise):
    response = page.goto("/guidance" + exercise["path"])
    assert response.status == 200
    link = page.locator(f'a[href="{exercise["path"]}"]')
    if link.count():
        link.click()
    expect(page.locator("#input-answer")).to_be_visible()


def reset_exercise(page, exercise):
    page.goto("/guidance" + exercise["path"])
    page.locator(f'form[action="/reset{exercise["path"]}"] button').click()
    expect(page.locator(".question-count")).to_contain_text(
        f"0/{len(exercise['answers'])}"
    )


def set_feedback(page, enabled):
    with page.expect_response(
        lambda r: r.url.endswith("/api/settings") and r.request.method == "GET"
    ) as loaded:
        page.goto("/settings?lang=en")
    original = loaded.value.json()["feedback_enabled"]
    toggle = page.locator("#intermediate-feedback-page-toggle")
    expect(toggle).to_be_checked(checked=original)
    if original != enabled:
        with page.expect_response(
            lambda r: r.url.endswith("/api/settings") and r.request.method == "POST"
        ) as saved:
            page.locator("label.switch").filter(has=toggle).click()
        assert saved.value.ok
        assert saved.value.json()["feedback_enabled"] == enabled
    return original


def submit_answer(page, answer):
    page.locator("#input-answer").fill(answer)
    with page.expect_navigation() as navigation:
        page.locator("#input-submit-button").click()
    assert navigation.value.status == 200


def complete_exercise(page, exercise, base_url):
    answers = exercise["answers"]
    seen = set()
    for index in range(len(answers)):
        question_id = page.locator('input[name="nr"]').input_value()
        assert question_id in answers, (
            "Deployed exercise content differs from the tested revision"
        )
        assert question_id not in seen, "Correct answers must advance progress"
        seen.add(question_id)
        submit_answer(page, answers[question_id])
        expect(page).to_have_url(base_url + "/feedback" + exercise["path"])
        expect(page.locator(".feedback-correct-container")).to_be_visible()
        if index < len(answers) - 1:
            expect(page.locator(".question-count")).to_contain_text(
                f"{index + 1}/{len(answers)}"
            )
            page.locator(".next-question-button").click()
    assert seen == set(answers)
    expect(page.locator(".completion-summary")).to_be_visible()
    expect(page.locator(".next-exercise-button-container a")).to_be_visible()
