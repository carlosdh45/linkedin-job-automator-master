import asyncio
import random
import logging
from pathlib import Path
from src import db
from src.cv_parser import CVProfile
from src.answer_generator import AnswerGenerator, AnswerGeneratorError

logger = logging.getLogger(__name__)

EASY_APPLY_SELECTORS = [
    'button.jobs-apply-button:has-text("Easy Apply")',
    '[aria-label*="Easy Apply"]',
    'button[data-job-id]:has-text("Easy Apply")',
    'button:has-text("Easy Apply")',
]

EXTERNAL_APPLY_SELECTORS = [
    # Explicit "Apply on company website" text
    'button:has-text("Apply on company website")',
    'a:has-text("Apply on company website")',
    # jobs-apply-button class without Easy Apply label
    'button.jobs-apply-button:not([aria-label*="Easy Apply"])',
    # aria-label "Apply to X" without Easy Apply
    '[aria-label*="Apply to"]:not([aria-label*="Easy Apply"])',
    '[aria-label*="apply to"]:not([aria-label*="Easy Apply"])',
    # Anchor-based apply links
    'a.jobs-apply-button',
    'a[href*="/jobs/apply/"]',
    # Generic apply button (not Easy Apply)
    'button:has-text("Apply"):not(:has-text("Easy"))',
    'a:has-text("Apply"):not(:has-text("Easy"))',
]

PREMIUM_SELECTORS = [
    'button:has-text("Upgrade to Premium")',
    'button:has-text("See who LinkedIn")',
    '[aria-label*="Premium"]',
    '.jobs-premium-applicants-insight',
]

CV_FIELD_MAP = {
    "first name": "first_name",
    "last name": "last_name",
    "email": "email",
    "phone": "phone",
    "mobile": "phone",
    "city": "location",
    "location": "location",
    "linkedin": "linkedin_url",
    "github": "github_url",
    "website": "github_url",
    "portfolio": "github_url",
}


class LinkedInApplierError(Exception):
    pass


class LinkedInApplier:
    def __init__(self, config: dict, cv_profile: CVProfile, answer_gen: AnswerGenerator, db_path: str):
        self.config = config
        self.cv_profile = cv_profile
        self.answer_gen = answer_gen
        self.db_path = db_path
        self.session_path = config["linkedin"]["session_path"]
        self.delay_min = config["application"]["delay_min"]
        self.delay_max = config["application"]["delay_max"]
        self.max_steps = config["application"]["max_modal_steps"]
        self.headless = config["application"]["headless"]

    async def run(self, jobs: list) -> dict:
        from playwright.async_api import async_playwright

        max_apps = self.config["application"]["max_applications_per_run"]
        stats = {"applied": 0, "skipped": 0, "failed": 0, "manual_review": 0, "external_apply": 0}

        async with async_playwright() as p:
            context, page = await self._launch_browser(p)
            try:
                if not await self._is_session_valid(page):
                    success = await self._login(page)
                    if not success:
                        logger.error("Login failed. Aborting.")
                        return stats
                    await self._save_session(context)

                count = 0
                for job in jobs:
                    if count >= max_apps:
                        logger.info(f"Reached max_applications_per_run ({max_apps}). Stopping.")
                        break

                    url = job.get("Job LinkedIn URL", "").strip()
                    company = job.get("Company Name", "").strip()
                    title = job.get("Job Title", "").strip()
                    location = job.get("Location", "").strip()
                    domain = job.get("Company Domain", "").strip()

                    logger.info(f"Processing: {title} at {company}")
                    status = "skipped"
                    notes = ""
                    external_url = ""

                    try:
                        status, notes, external_url = await self._apply_to_job(page, job)
                    except Exception as e:
                        logger.error(f"Unhandled error on {url}: {e}")
                        status = "failed"
                        notes = str(e)

                    db.record_job(
                        self.db_path, url, company, title, location,
                        domain=domain, status=status,
                        external_url=external_url, notes=notes,
                    )
                    stats[status] = stats.get(status, 0) + 1
                    count += 1
                    logger.info(f"  → {status}" + (f": {notes}" if notes else ""))
                    await self._random_delay()

            finally:
                await self._save_session(context)
                await context.close()

        return stats

    async def _launch_browser(self, playwright):
        session_file = Path(self.session_path)
        storage_state = str(session_file) if session_file.exists() else None

        browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = await browser.new_context(
            storage_state=storage_state,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = await context.new_page()
        return context, page

    async def _is_session_valid(self, page) -> bool:
        try:
            await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(2)
            return "feed" in page.url and "login" not in page.url
        except Exception:
            return False

    async def _login(self, page) -> bool:
        try:
            await page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
            await asyncio.sleep(1)
            await page.fill("#username", self.config["linkedin"]["email"])
            await asyncio.sleep(0.5)
            await page.fill("#password", self.config["linkedin"]["password"])
            await asyncio.sleep(0.5)
            await page.click('button[type="submit"]')
            await asyncio.sleep(3)

            if "/checkpoint/" in page.url or "challenge" in page.url:
                print("\n⚠️  CAPTCHA or security check detected.")
                print("   Solve it in the browser window, then press Enter here to continue...")
                import sys
                sys.stdin.readline()
                await asyncio.sleep(2)

            if "feed" in page.url or "mynetwork" in page.url:
                logger.info("Login successful.")
                return True

            logger.error(f"Login may have failed. Current URL: {page.url}")
            return False
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    async def _apply_to_job(self, page, job: dict) -> tuple:
        url = job.get("Job LinkedIn URL", "").strip()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        except Exception as e:
            return "failed", f"page load timeout: {e}", ""

        await asyncio.sleep(2)

        # Check we're on a valid job page — if LinkedIn redirected away, bail early
        if "/jobs/view/" not in page.url and "linkedin.com" not in page.url:
            return "failed", f"unexpected redirect: {page.url}", ""

        # Wait briefly for any of several known job card selectors (non-fatal if absent)
        JOB_CARD_SELECTORS = [
            ".jobs-unified-top-card",
            ".job-details-jobs-unified-top-card",
            ".jobs-details__main-content",
            "[data-test-job-title]",
            "h1.t-24",
            ".jobs-apply-button",
        ]
        card_found = False
        for sel in JOB_CARD_SELECTORS:
            try:
                await page.wait_for_selector(sel, timeout=4000)
                card_found = True
                break
            except Exception:
                continue

        # If nothing loaded at all (likely expired/removed job), skip it
        if not card_found:
            page_text = await page.inner_text("body")
            if "no longer accepting" in page_text.lower() or "job has been removed" in page_text.lower():
                return "skipped", "job no longer accepting applications", ""
            if "/jobs/view/" not in page.url:
                return "skipped", "redirected away from job page", ""
            # Page loaded but card structure unknown — proceed and try apply button anyway

        # Scroll down slightly to make sticky apply bar visible, then scroll back up
        await page.evaluate("window.scrollBy(0, 300)")
        await asyncio.sleep(0.8)
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(0.5)

        # Check if job is Premium-gated (no apply button will appear)
        premium_gate = await _find_first(page, PREMIUM_SELECTORS, timeout=1500)
        if premium_gate:
            return "skipped", "premium required", ""

        easy_apply_btn = await _find_first(page, EASY_APPLY_SELECTORS, timeout=3000)

        if easy_apply_btn:
            db.record_job(
                self.db_path,
                url,
                job.get("Company Name", ""),
                job.get("Job Title", ""),
                job.get("Location", ""),
                domain=job.get("Company Domain", ""),
                status="in_progress",
            )
            try:
                await easy_apply_btn.click()
                await asyncio.sleep(2)
                MODAL_SELECTORS = [
                    '.jobs-easy-apply-modal',
                    '[data-test-modal-container]',
                    '.artdeco-modal',
                    '[role="dialog"]',
                    '.job-details-easy-apply-modal',
                    '[aria-labelledby="jobs-apply-header"]',
                ]
                modal_found = False
                for msel in MODAL_SELECTORS:
                    try:
                        await page.wait_for_selector(msel, timeout=3000)
                        modal_found = True
                        break
                    except Exception:
                        continue
                if not modal_found:
                    return "failed", "modal did not open", ""

                status = await self._run_modal_flow(page, job)
                return status, "", ""
            except Exception as e:
                return "failed", f"easy apply error: {e}", ""

        external_btn = await _find_first(page, EXTERNAL_APPLY_SELECTORS, timeout=4000)
        if external_btn:
            external_url = await _extract_external_url(page, external_btn)
            return "external_apply", "", external_url

        # Last resort: check page text for "no longer accepting" before logging as unknown
        page_text = await page.inner_text("body")
        if "no longer accepting" in page_text.lower() or "job has been removed" in page_text.lower():
            return "skipped", "job no longer accepting applications", ""

        return "skipped", "no apply button found", ""

    async def _run_modal_flow(self, page, job: dict) -> str:
        for step_num in range(1, self.max_steps + 2):
            if step_num > self.max_steps:
                await _dismiss_modal(page)
                return "manual_review"

            result = await self._handle_modal_step(page, step_num)

            if result == "error":
                return "failed"
            elif result == "manual_review":
                await _dismiss_modal(page)
                return "manual_review"
            elif result == "submit":
                await asyncio.sleep(1)
                confirm_btn = page.locator('button:has-text("Submit application")')
                try:
                    await confirm_btn.wait_for(timeout=3000)
                    await confirm_btn.click()
                except Exception:
                    pass
                await asyncio.sleep(2)
                return "applied"
            elif result == "next":
                next_btn = page.locator('button:has-text("Next"), button:has-text("Continue")')
                try:
                    await next_btn.first.click()
                    await asyncio.sleep(1.5)
                except Exception:
                    return "manual_review"

        return "manual_review"

    async def _handle_modal_step(self, page, step_num: int) -> str:
        await asyncio.sleep(1)

        field_groups = await page.query_selector_all(
            ".jobs-easy-apply-form-section__grouping, .fb-form-element"
        )

        for group in field_groups:
            try:
                await self._fill_field_group(page, group)
            except AnswerGeneratorError:
                return "manual_review"
            except Exception as e:
                logger.warning(f"Field fill error (step {step_num}): {e}")

        if await _button_visible(page, 'button:has-text("Submit application")'):
            return "submit"
        if await _button_visible(page, 'button:has-text("Review")'):
            review_btn = page.locator('button:has-text("Review")')
            await review_btn.click()
            await asyncio.sleep(1.5)
            if await _button_visible(page, 'button:has-text("Submit application")'):
                return "submit"
            return "manual_review"
        if await _button_visible(page, 'button:has-text("Next"), button:has-text("Continue")'):
            return "next"

        return "manual_review"

    async def _fill_field_group(self, page, group) -> None:
        label_el = await group.query_selector("label, legend, .fb-form-element-label")
        label = (await label_el.inner_text()).strip() if label_el else ""
        label_lower = label.lower()

        file_input = await group.query_selector('input[type="file"]')
        if file_input:
            await self._handle_file_upload(file_input)
            return

        radio_inputs = await group.query_selector_all('input[type="radio"]')
        if radio_inputs:
            await self._fill_radio_group(group, label)
            return

        select_el = await group.query_selector("select")
        if select_el:
            await self._fill_dropdown(select_el, label)
            return

        combobox = await group.query_selector('[role="combobox"], [role="listbox"]')
        if combobox:
            await self._fill_combobox(combobox, label)
            return

        text_input = await group.query_selector(
            'input[type="text"], input[type="email"], input[type="tel"], '
            'input[type="number"], input:not([type])'
        )
        if text_input:
            existing = await text_input.input_value()
            cv_value = self._cv_value_for_label(label_lower)
            if cv_value and not existing:
                await text_input.fill(cv_value)
            elif not existing:
                answer = await asyncio.to_thread(self.answer_gen.answer, label, field_type="text")
                await text_input.fill(answer)
            return

        textarea = await group.query_selector("textarea")
        if textarea:
            existing = await textarea.input_value()
            if not existing:
                answer = await asyncio.to_thread(
                    self.answer_gen.answer, label, field_type="textarea", max_chars=1000
                )
                await textarea.fill(answer)

    def _cv_value_for_label(self, label_lower: str) -> str:
        for key, attr in CV_FIELD_MAP.items():
            if key in label_lower:
                if attr == "first_name":
                    parts = self.cv_profile.name.split()
                    return parts[0] if parts else ""
                elif attr == "last_name":
                    parts = self.cv_profile.name.split()
                    return parts[-1] if len(parts) > 1 else ""
                else:
                    return getattr(self.cv_profile, attr, "") or ""
        return ""

    async def _fill_radio_group(self, group, label: str) -> None:
        radio_inputs = await group.query_selector_all('input[type="radio"]')
        options = []
        for radio in radio_inputs:
            radio_label = await group.query_selector(f'label[for="{await radio.get_attribute("id")}"]')
            if radio_label:
                options.append(await radio_label.inner_text())

        if not options:
            return

        answer = await asyncio.to_thread(
            self.answer_gen.answer, label, field_type="radio", options=options
        )
        for radio in radio_inputs:
            radio_label_el = await group.query_selector(
                f'label[for="{await radio.get_attribute("id")}"]'
            )
            if radio_label_el:
                radio_text = await radio_label_el.inner_text()
                if answer.lower() in radio_text.lower() or radio_text.lower() in answer.lower():
                    await radio.click()
                    return

        await radio_inputs[0].click()

    async def _fill_dropdown(self, select_el, label: str) -> None:
        options = await select_el.query_selector_all("option")
        option_texts = []
        for opt in options:
            text = (await opt.inner_text()).strip()
            val = await opt.get_attribute("value")
            if text and val and val not in ("", "Select an option", "-1"):
                option_texts.append(text)

        if not option_texts:
            return

        answer = await asyncio.to_thread(
            self.answer_gen.answer, label, field_type="dropdown", options=option_texts
        )
        for opt_text in option_texts:
            if answer.lower() in opt_text.lower() or opt_text.lower() in answer.lower():
                await select_el.select_option(label=opt_text)
                return

        await select_el.select_option(index=1)

    async def _fill_combobox(self, combobox, label: str) -> None:
        answer = await asyncio.to_thread(self.answer_gen.answer, label, field_type="text")
        try:
            await combobox.click()
            await asyncio.sleep(0.5)
            await combobox.fill(answer)
            await asyncio.sleep(0.8)
            option = combobox.page().locator('[role="option"]').first
            await option.click()
        except Exception:
            pass

    async def _handle_file_upload(self, file_input) -> None:
        cv_path = self.cv_profile.cv_path
        if cv_path and Path(cv_path).exists():
            await file_input.set_input_files(cv_path)

    async def _random_delay(self) -> None:
        await asyncio.sleep(random.uniform(self.delay_min, self.delay_max))

    async def _save_session(self, context) -> None:
        session_path = Path(self.session_path)
        session_path.parent.mkdir(parents=True, exist_ok=True)
        await context.storage_state(path=str(session_path))


async def _find_first(page, selectors: list, timeout: int = 3000):
    for sel in selectors:
        try:
            el = page.locator(sel).first
            await el.wait_for(state="visible", timeout=timeout)
            return el
        except Exception:
            continue
    return None


async def _button_visible(page, selector: str) -> bool:
    try:
        el = page.locator(selector).first
        return await el.is_visible()
    except Exception:
        return False


async def _dismiss_modal(page) -> None:
    for sel in ['button[aria-label="Dismiss"]', 'button:has-text("Dismiss")', '[data-test-modal-close-btn]']:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible():
                await btn.click()
                return
        except Exception:
            continue
    try:
        await page.keyboard.press("Escape")
    except Exception:
        pass


async def _extract_external_url(page, apply_btn) -> str:
    try:
        href = await apply_btn.get_attribute("href")
        if href and href.startswith("http"):
            return href
    except Exception:
        pass
    try:
        async with page.expect_popup(timeout=3000) as popup_info:
            await apply_btn.click()
        popup = await popup_info.value
        url = popup.url
        await popup.close()
        return url
    except Exception:
        return ""
