from playwright.sync_api import Page, expect


class ConfirmDialog:
    """The in-page dialog that asks before deleting or cancelling something."""

    def __init__(self, page: Page) -> None:
        self.root = page.get_by_test_id("confirm-dialog")
        self.message = page.get_by_test_id("confirm-message")
        self.yes = page.get_by_test_id("confirm-yes")
        self.no = page.get_by_test_id("confirm-no")

    def accept(self, expected_text: str = "") -> None:
        expect(self.root, "the confirmation dialog did not open").to_be_visible()
        if expected_text:
            expect(self.message).to_contain_text(expected_text)
        self.yes.click()
