"""E2E tests for photo upload, carousel, and photo management."""

import base64

import pytest
from django.urls import reverse
from playwright.sync_api import Page, expect

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]

_PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


@pytest.fixture
def test_image(tmp_path) -> str:
    """Write a minimal valid PNG to a temp file and return the path."""
    path = tmp_path / "test.png"
    path.write_bytes(_PNG_1X1)
    return str(path)


@pytest.fixture
def two_images(tmp_path) -> list[str]:
    """Write two minimal valid PNGs and return their paths."""
    paths = []
    for name in ("img1.png", "img2.png"):
        p = tmp_path / name
        p.write_bytes(_PNG_1X1)
        paths.append(str(p))
    return paths


def _create_post_with_images(
    page: Page, live_server, title: str, images: list[str]
) -> None:
    """Helper: create a post with uploaded photos via the UI."""
    page.goto(f"{live_server.url}{reverse('posts:post_create')}")
    page.fill('[name="title"]', title)
    page.locator('input[name="photos"]').set_input_files(images)
    page.get_by_role("button", name="Save").click()


# ---------------------------------------------------------------------------
# Upload widget
# ---------------------------------------------------------------------------


def test_photo_upload_shows_preview(auth_page: Page, live_server, test_image):
    """Selecting a file renders a data-URL preview before submission."""
    auth_page.goto(f"{live_server.url}{reverse('posts:post_create')}")
    auth_page.locator('input[name="photos"]').set_input_files(test_image)
    expect(auth_page.locator('[x-data] img[src^="data:"]').first).to_be_visible()


def test_photo_upload_remove_preview(auth_page: Page, live_server, test_image):
    """Clicking the remove button on a preview hides it."""
    auth_page.goto(f"{live_server.url}{reverse('posts:post_create')}")
    auth_page.locator('input[name="photos"]').set_input_files(test_image)
    # Preview is visible
    expect(auth_page.locator('[x-data] img[src^="data:"]').first).to_be_visible()
    # Remove it (small × button on the thumbnail)
    auth_page.locator("[x-data] .relative button").first.click()
    # Preview grid is gone
    expect(auth_page.locator('[x-data] img[src^="data:"]')).to_have_count(0)


def test_create_post_with_photos_persists(auth_page: Page, live_server, test_image):
    """Submitting the create form with photos redirects to the detail page with the grid."""
    _create_post_with_images(auth_page, live_server, "My Photo Post", [test_image])
    expect(auth_page.locator("h1")).to_contain_text("My Photo Post")
    expect(auth_page.locator("button[data-photo-url]").first).to_be_visible()


def test_first_uploaded_photo_is_cover(auth_page: Page, live_server, two_images):
    """The first photo uploaded becomes the cover in the edit view."""
    _create_post_with_images(auth_page, live_server, "Cover Test", two_images)
    auth_page.get_by_role("link", name="Edit").click()
    expect(auth_page.locator("#post-photos span", has_text="Cover")).to_have_count(1)


# ---------------------------------------------------------------------------
# Carousel
# ---------------------------------------------------------------------------


def test_carousel_opens_on_thumbnail_click(auth_page: Page, live_server, test_image):
    """Clicking a thumbnail opens the full-screen carousel modal."""
    _create_post_with_images(auth_page, live_server, "Carousel Open", [test_image])
    auth_page.locator("button[data-photo-url]").first.click()
    expect(auth_page.locator(".fixed.inset-0")).to_be_visible()
    expect(auth_page.locator(".fixed.inset-0 img")).to_be_visible()


def test_carousel_closes_with_escape(auth_page: Page, live_server, test_image):
    """Pressing Escape closes the carousel modal."""
    _create_post_with_images(auth_page, live_server, "Carousel Escape", [test_image])
    auth_page.locator("button[data-photo-url]").first.click()
    expect(auth_page.locator(".fixed.inset-0")).to_be_visible()
    auth_page.keyboard.press("Escape")
    expect(auth_page.locator(".fixed.inset-0")).not_to_be_visible()


def test_carousel_closes_with_close_button(auth_page: Page, live_server, test_image):
    """Clicking the × button closes the carousel modal."""
    _create_post_with_images(auth_page, live_server, "Carousel Close Btn", [test_image])
    auth_page.locator("button[data-photo-url]").first.click()
    expect(auth_page.locator(".fixed.inset-0")).to_be_visible()
    auth_page.locator(".fixed.inset-0 button[aria-label]").first.click()
    expect(auth_page.locator(".fixed.inset-0")).not_to_be_visible()


def test_carousel_arrow_key_navigation(auth_page: Page, live_server, two_images):
    """Arrow keys advance through photos in the carousel."""
    _create_post_with_images(auth_page, live_server, "Carousel Nav", two_images)
    # Open on first photo
    auth_page.locator("button[data-photo-url]").first.click()
    first_src = auth_page.locator(".fixed.inset-0 img").get_attribute("src")
    # Navigate to next
    auth_page.keyboard.press("ArrowRight")
    second_src = auth_page.locator(".fixed.inset-0 img").get_attribute("src")
    assert first_src != second_src
    # Navigate back
    auth_page.keyboard.press("ArrowLeft")
    back_src = auth_page.locator(".fixed.inset-0 img").get_attribute("src")
    assert back_src == first_src


# ---------------------------------------------------------------------------
# Edit: photo management
# ---------------------------------------------------------------------------


def test_edit_delete_photo(auth_page: Page, live_server, test_image):
    """Clicking the delete button on an existing photo removes it from the edit grid."""
    _create_post_with_images(auth_page, live_server, "Edit Delete", [test_image])
    auth_page.get_by_role("link", name="Edit").click()
    expect(auth_page.locator("#post-photos")).to_be_visible()
    auth_page.locator("#post-photos button[hx-delete]").first.click()
    expect(auth_page.locator("#post-photos .relative")).to_have_count(0)


def test_edit_set_cover_photo(auth_page: Page, live_server, two_images):
    """Clicking 'Set cover' on a non-cover photo makes it the cover."""
    _create_post_with_images(auth_page, live_server, "Set Cover", two_images)
    auth_page.get_by_role("link", name="Edit").click()
    # Initially one cover badge
    expect(auth_page.locator("#post-photos span", has_text="Cover")).to_have_count(1)
    # Click set cover on the non-cover photo
    auth_page.locator("#post-photos button[hx-post]").first.click()
    # Still exactly one cover badge
    expect(auth_page.locator("#post-photos span", has_text="Cover")).to_have_count(1)
