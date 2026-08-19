import os
import time
import re
import traceback
import pyautogui
import pyperclip

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


USERNAME = os.getenv("NAUKRI_USERNAME", "akshay96dehankar@gmail.com")
PASSWORD = os.getenv("NAUKRI_PASSWORD", "9850329727ad")

SEARCH_TEXT = "data engineer, 3 year"

SEARCH_X, SEARCH_Y = 698, 175
CHATGPT_X, CHATGPT_Y = 700, 700
CHATGPT_COPY_X, CHATGPT_COPY_Y = 377, 282
NAUKRI_ANSWER_X, NAUKRI_ANSWER_Y = 1100, 465

CHATGPT_WAIT = 8
QUESTION_TIMEOUT = 20


def wait_click(driver, xpath, timeout=15):
    WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    ).click()


def visible(el):
    try:
        r = el.getBoundingClientRect()
        s = getComputedStyle(el)
        return r.width > 0 and r.height > 0 and s.display != "none" \
            and s.visibility != "hidden" and s.opacity != "0"
    except:
        return False


def question(driver):
    script = r"""
    const visible = el => {
        if (!el) return false;
        const r = el.getBoundingClientRect();
        const s = getComputedStyle(el);
        return r.width > 0 && r.height > 0 &&
               s.display !== "none" &&
               s.visibility !== "hidden" &&
               s.opacity !== "0";
    };

    const clean = t => (t || "")
        .replace(/\r/g, "")
        .replace(/[ \t]+/g, " ")
        .trim();

    const result = [];

    for (const el of document.querySelectorAll("body *")) {
        if (!visible(el)) continue;

        const r = el.getBoundingClientRect();

        if (r.left < innerWidth * .60 ||
            r.right > innerWidth + 10 ||
            r.top < 100 ||
            r.bottom > innerHeight + 10 ||
            r.width < 250) continue;

        for (const line of clean(el.innerText || el.textContent)
            .split(/\n+/)
            .map(x => x.trim())
            .filter(Boolean)) {

            if (line.includes("?") && line.length >= 5 && line.length <= 500) {
                const q = line.substring(0, line.indexOf("?") + 1).trim();
                if (!result.includes(q)) result.push(q);
            }
        }
    }

    return result.sort((a, b) => a.length - b.length)[0] || "";
    """

    try:
        return (driver.execute_script(script) or "").strip()
    except:
        return ""


def fingerprint(text):
    return re.sub(r"\s+", " ", text.strip().lower()) if text else ""


def wait_question_change(driver, old, timeout=QUESTION_TIMEOUT):
    old_fp = fingerprint(old)
    end = time.time() + timeout
    last = ""

    while time.time() < end:
        current = question(driver)

        if current:
            last = current
            if fingerprint(current) != old_fp:
                return current

        time.sleep(.5)

    return last


def yes_no(driver):
    script = r"""
    const visible = el => {
        const r = el.getBoundingClientRect();
        const s = getComputedStyle(el);
        return r.width > 0 && r.height > 0 &&
               s.display !== "none" &&
               s.visibility !== "hidden" &&
               s.opacity !== "0";
    };

    const text = el => (el.innerText || el.textContent ||
                        el.value || "").trim().toLowerCase();

    for (const r of document.querySelectorAll("input[type=radio]")) {
        if (!visible(r) || r.getBoundingClientRect().left < innerWidth * .60)
            continue;

        let p = r;

        for (let i = 0; i < 8 && p; i++, p = p.parentElement) {
            const t = text(p);
            if (t.includes("yes") && t.includes("no")) return true;
        }
    }

    let yes = false, no = false;

    for (const el of document.querySelectorAll(
        "button,label,[role=radio],[role=option],span,div"
    )) {
        if (!visible(el) ||
            el.getBoundingClientRect().left < innerWidth * .60)
            continue;

        const t = text(el);

        if (t === "yes") yes = true;
        if (t === "no") no = true;

        if (yes && no) return true;
    }

    return false;
    """

    try:
        return bool(driver.execute_script(script))
    except:
        return False


def click_yes(driver):
    script = r"""
    const visible = el => {
        const r = el.getBoundingClientRect();
        const s = getComputedStyle(el);
        return r.width > 0 && r.height > 0 &&
               s.display !== "none" &&
               s.visibility !== "hidden" &&
               s.opacity !== "0";
    };

    const text = el => (el.innerText || el.textContent ||
                        el.value || "").trim().toLowerCase();

    for (const r of document.querySelectorAll("input[type=radio]")) {
        if (!visible(r) || r.getBoundingClientRect().left < innerWidth * .60)
            continue;

        let p = r;

        for (let i = 0; i < 8 && p; i++, p = p.parentElement) {
            const t = text(p);

            if (t.includes("yes") && t.includes("no")) {
                r.click();
                r.dispatchEvent(new Event("change", {bubbles:true}));
                return true;
            }
        }
    }

    for (const el of document.querySelectorAll(
        "label,button,[role=radio],[role=option],span,div"
    )) {
        if (!visible(el) ||
            el.getBoundingClientRect().left < innerWidth * .60 ||
            text(el) !== "yes")
            continue;

        let p = el;

        for (let i = 0; i < 8 && p; i++, p = p.parentElement) {
            if (!text(p).includes("yes") || !text(p).includes("no"))
                continue;

            const radio = p.querySelector("input[type=radio]");

            if (radio) {
                radio.click();
                radio.dispatchEvent(
                    new Event("change", {bubbles:true})
                );
                return true;
            }

            for (const label of p.querySelectorAll("label")) {
                if (text(label).includes("yes")) {
                    label.click();
                    return true;
                }
            }

            for (const el2 of p.querySelectorAll(
                "[role=radio],[role=option]"
            )) {
                if (text(el2) === "yes" ||
                    (el2.getAttribute("aria-label") || "").toLowerCase() === "yes") {
                    el2.click();
                    return true;
                }
            }
        }
    }

    return false;
    """

    try:
        return bool(driver.execute_script(script))
    except:
        return False


def click_save(driver):
    script = r"""
    const visible = el => {
        const r = el.getBoundingClientRect();
        const s = getComputedStyle(el);
        return r.width > 0 && r.height > 0 &&
               s.display !== "none" &&
               s.visibility !== "hidden" &&
               s.opacity !== "0";
    };

    const text = el => (el.innerText || el.textContent ||
                        el.value || "").trim().toLowerCase();

    const buttons = [...document.querySelectorAll(
        "button,input[type=button],input[type=submit],a,div,span"
    )].filter(el =>
        visible(el) &&
        el.getBoundingClientRect().left >= innerWidth * .60 &&
        text(el) === "save"
    );

    if (!buttons.length) return false;

    buttons.sort(
        (a,b) =>
        b.getBoundingClientRect().top -
        a.getBoundingClientRect().top
    );

    buttons[0].click();
    return true;
    """

    try:
        return bool(driver.execute_script(script))
    except:
        return False


def extract_answer(text):
    if not text:
        return ""

    lines = [
        x.strip() for x in
        text.replace("\r", "").split("\n")
        if x.strip()
    ]

    ignored = {
        "copy", "copied", "regenerate", "edit",
        "read aloud", "good response", "bad response",
        "more", "share"
    }

    lines = [
        x for x in lines
        if x.lower() not in ignored and not x.startswith("```")
    ]

    for line in reversed(lines):
        x = line.strip("\"' *").strip().lower()

        if x == "yes":
            return "Yes"

        if x == "no":
            return "No"

    for line in reversed(lines):
        m = re.search(
            r"\b(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\b",
            line,
            re.I
        )

        if m:
            return f"{m.group(1)} Years"

    return lines[-1].strip("\"'") if lines else ""


def copy_chatgpt_response():
    time.sleep(CHATGPT_WAIT)

    pyperclip.copy("")

    pyautogui.click(
        CHATGPT_COPY_X,
        CHATGPT_COPY_Y
    )

    time.sleep(1.5)

    text = pyperclip.paste().strip()

    print("ChatGPT response:")
    print(text)

    return extract_answer(text)


def ask_chatgpt(q):
    prompt = f"""I am filling a job application.

Read the question/options below.

Give ONLY the exact answer to the question.

If the answer is a number of years, return ONLY the number of years, such as "3 Years".

If the question is Yes/No, return ONLY "Yes" or "No".

Do not explain.
Do not add extra words.
Do not use Markdown.
Do not add punctuation.

Question/options:

{q}"""

    pyperclip.copy(prompt)

    pyautogui.hotkey("alt", "tab")
    time.sleep(2)

    pyautogui.click(CHATGPT_X, CHATGPT_Y)
    time.sleep(.5)

    pyautogui.hotkey("ctrl", "a")
    pyautogui.hotkey("ctrl", "v")
    pyautogui.press("enter")

    print("Question sent to ChatGPT.")

    answer = copy_chatgpt_response()

    pyautogui.hotkey("alt", "tab")
    time.sleep(2)

    return answer


def focus_answer_field(driver):
    script = r"""
    const visible = el => {
        const r = el.getBoundingClientRect();
        const s = getComputedStyle(el);
        return r.width > 0 && r.height > 0 &&
               s.display !== "none" &&
               s.visibility !== "hidden" &&
               s.opacity !== "0";
    };

    const fields = [...document.querySelectorAll(
        "textarea,input:not([type=hidden]),[contenteditable=true]"
    )].filter(visible)
     .filter(el => el.getBoundingClientRect().left > innerWidth * .55);

    if (!fields.length) return false;

    const field =
        fields.find(el =>
            el.tagName.toLowerCase() === "textarea" ||
            el.isContentEditable
        ) || fields[0];

    field.scrollIntoView({block:"center"});
    field.focus();

    return true;
    """

    try:
        return bool(driver.execute_script(script))
    except:
        return False


def field_focused(driver):
    try:
        return bool(driver.execute_script("""
            const e = document.activeElement;
            return e &&
                (
                    e.tagName.toLowerCase() === "input" ||
                    e.tagName.toLowerCase() === "textarea" ||
                    e.isContentEditable
                );
        """))
    except:
        return False


def enter_answer(driver, answer):
    if not answer:
        return False

    if not focus_answer_field(driver):
        pyautogui.click(
            NAUKRI_ANSWER_X,
            NAUKRI_ANSWER_Y
        )
        time.sleep(.5)

    if not field_focused(driver):
        pyautogui.click(
            NAUKRI_ANSWER_X,
            NAUKRI_ANSWER_Y
        )
        time.sleep(.5)

    if not field_focused(driver):
        print("Answer field not focused.")
        return False

    pyperclip.copy(answer)

    pyautogui.hotkey("ctrl", "a")
    pyautogui.hotkey("ctrl", "v")

    time.sleep(1)

    return click_save(driver)


def process_panel(driver):
    processed = set()

    while True:
        time.sleep(1)

        q = question(driver)

        if not q:
            return True

        fp = fingerprint(q)

        if fp in processed:
            q = wait_question_change(driver, q)

            if not q or fingerprint(q) in processed:
                continue

            fp = fingerprint(q)

        processed.add(fp)

        print("\nQUESTION:", q)

        if yes_no(driver):
            print("Yes/No detected.")
            success = click_yes(driver) and click_save(driver)

        else:
            print("Sending to ChatGPT...")
            answer = ask_chatgpt(q)
            print("ANSWER:", answer)
            success = enter_answer(driver, answer)

        if not success:
            print("Failed to process question.")
            return False

        next_q = wait_question_change(driver, q)

        if not next_q:
            return True


def find_apply(driver):
    xpath = """
    //button[contains(
        translate(normalize-space(.),
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        'abcdefghijklmnopqrstuvwxyz'),'apply')]
    |
    //a[contains(
        translate(normalize-space(.),
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        'abcdefghijklmnopqrstuvwxyz'),'apply')]
    """

    for el in driver.find_elements(By.XPATH, xpath):
        try:
            if el.is_displayed() and el.is_enabled():
                return el
        except:
            pass

    return None


def login(driver):
    driver.get("https://www.naukri.com/")
    time.sleep(5)

    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
            "'abcdefghijklmnopqrstuvwxyz'),'login')]"
            " | "
            "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
            "'abcdefghijklmnopqrstuvwxyz'),'login')]"
        ))
    ).click()

    email = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((
            By.XPATH,
            "//input[@type='email' or "
            "contains(translate(@placeholder,"
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'email') or "
            "contains(translate(@placeholder,"
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'username')]"
        ))
    )

    email.send_keys(USERNAME)

    driver.find_element(
        By.XPATH,
        "//input[@type='password']"
    ).send_keys(PASSWORD)

    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
            "'abcdefghijklmnopqrstuvwxyz'),'login')]"
        ))
    ).click()

    time.sleep(6)


def close_job(driver, listing):
    try:
        if len(driver.window_handles) > 1:
            if driver.current_window_handle != listing:
                driver.close()

            driver.switch_to.window(listing)

    except Exception as e:
        print("Close error:", e)


def main():
    driver = webdriver.Chrome()
    driver.maximize_window()

    try:
        login(driver)

        time.sleep(3)

        pyautogui.click(SEARCH_X, SEARCH_Y)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.write(SEARCH_TEXT, interval=.03)
        pyautogui.press("enter")

        time.sleep(5)

        try:
            wait_click(
                driver,
                "//*[normalize-space()='Recommended']",
                5
            )

            wait_click(
                driver,
                "//*[normalize-space()='Date']",
                5
            )

        except:
            pass

        time.sleep(4)

        jobs = driver.find_elements(
            By.XPATH,
            "//a[contains(@class,'title')]"
        )

        urls = list(dict.fromkeys(
            j.get_attribute("href")
            for j in jobs
            if j.get_attribute("href")
        ))

        print(f"Jobs found: {len(urls)}")

        listing = driver.current_window_handle

        for i, url in enumerate(urls, 1):
            print(f"\n========== JOB {i}/{len(urls)} ==========")

            driver.switch_to.window(listing)

            driver.execute_script(
                "window.open(arguments[0], '_blank');",
                url
            )

            time.sleep(4)

            if len(driver.window_handles) < 2:
                continue

            driver.switch_to.window(
                driver.window_handles[-1]
            )

            apply = find_apply(driver)

            if not apply:
                print("Apply not found.")
                close_job(driver, listing)
                continue

            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});",
                    apply
                )

                time.sleep(1)

                try:
                    apply.click()
                except:
                    driver.execute_script(
                        "arguments[0].click();",
                        apply
                    )

                print("Apply clicked.")

            except Exception as e:
                print("Apply error:", e)
                close_job(driver, listing)
                continue

            time.sleep(3)

            process_panel(driver)

            close_job(driver, listing)
            time.sleep(2)

    except Exception as e:
        print("ERROR:", e)
        traceback.print_exc()

    finally:
        input("\nPress Enter to close Chrome...")
        driver.quit()


if __name__ == "__main__":
    main()