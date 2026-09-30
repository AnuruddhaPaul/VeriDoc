"""Generate the fictional 'Northwind Robotics Employee Handbook' used by the demo and eval set.

Every fact in it is invented, so an answer that is not in the PDF can only come from the
model's imagination or training data - exactly what VeriDoc is built to catch.
"""

import sys
from pathlib import Path

import fitz

PAGES = [
    (
        "1. Leave Policy",
        "All full-time employees receive 25 days of paid annual leave per calendar year. Unused leave "
        "may be carried over, up to a maximum of 5 days, and must be used by 31 March of the following "
        "year. Employees receive 10 days of paid sick leave per year. A medical certificate is required "
        "when sick leave exceeds 3 consecutive days.\n\n"
        "Parental leave is 16 weeks at full pay for the primary caregiver and 6 weeks at full pay for "
        "the secondary caregiver. Parental leave can be taken at any time within the first 12 months "
        "after the birth or adoption of a child.",
    ),
    (
        "2. Remote Work",
        "Employees may work remotely up to 3 days per week, with the manager's agreement on which days. "
        "Everyone must be available during core hours, 10:00 to 15:00 in their local time zone. "
        "New employees must work on-site for the first 4 weeks while they are onboarded.\n\n"
        "The company pays a one-time home-office stipend of 600 USD after the probation period is "
        "complete. The stipend covers a desk, a chair or a monitor and cannot be used for other items.",
    ),
    (
        "3. Travel and Expenses",
        "Domestic business travel meals are reimbursed up to 60 USD per day. Employees fly economy "
        "class for any flight shorter than 6 hours; premium economy is allowed for longer flights. "
        "Hotel stays are booked through the company travel portal.\n\n"
        "Expense reports must be submitted within 30 days of the expense. Reports submitted later "
        "than 30 days require written approval from a department head before they are reimbursed.",
    ),
    (
        "4. Information Security",
        "Passwords must be at least 14 characters long and must be changed every 180 days. "
        "Multi-factor authentication is mandatory for all company systems. A lost or stolen laptop or "
        "phone must be reported to the security team within 2 hours of discovery.\n\n"
        "Employees must never share credentials, and confidential documents may only be stored on "
        "the company-approved cloud drive.",
    ),
    (
        "5. Benefits and Learning",
        "The company matches employee retirement contributions up to 4 percent of salary. "
        "Health insurance starts on the first day of the month after the employee joins. "
        "Each employee has a learning budget of 1,500 USD per year for courses, books and "
        "conferences, and unused budget does not roll over to the next year.\n\n"
        "The employee referral bonus is 2,000 USD, paid after the referred hire completes 6 months.",
    ),
]


def build(path: Path) -> None:
    doc = fitz.open()
    for title, body in PAGES:
        page = doc.new_page()
        page.insert_text((72, 80), title, fontsize=18, fontname="hebo")
        page.insert_textbox(fitz.Rect(72, 110, 523, 760), body, fontsize=11, fontname="helv", lineheight=1.4)
        page.insert_text((72, 810), "Northwind Robotics - Employee Handbook (fictional)", fontsize=8)
    doc.save(path)


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("northwind_handbook.pdf")
    build(out)
    print(f"wrote {out}")
