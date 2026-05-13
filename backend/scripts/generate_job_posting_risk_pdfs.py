import json
from pathlib import Path

from fpdf import FPDF


DATASET_DIR = Path("backend/sample_data/source_data/job_posting_risk_50")
FONT_REGULAR = Path("C:/Windows/Fonts/malgun.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/malgunbd.ttf")


class JobPostingPDF(FPDF):
    def header(self):
        self.set_fill_color(32, 47, 67)
        self.rect(0, 0, 210, 18, style="F")
        self.set_text_color(255, 255, 255)
        self.set_font("Malgun", "B", 10)
        self.set_xy(14, 6)
        self.cell(0, 6, "HR-COPILOT SAMPLE JOB POSTING", border=0, ln=0)
        self.ln(16)
        self.set_text_color(35, 35, 35)

    def footer(self):
        self.set_y(-14)
        self.set_font("Malgun", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 6, f"{self.page_no()}", align="C")


def text(pdf, value, size=10.5, style="", color=(45, 45, 45), line_height=6.2):
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Malgun", style, size)
    pdf.set_text_color(*color)
    pdf.multi_cell(0, line_height, value)


def section_title(pdf, title):
    pdf.ln(2)
    pdf.set_x(pdf.l_margin)
    pdf.set_fill_color(237, 242, 247)
    pdf.set_draw_color(210, 218, 228)
    pdf.set_text_color(35, 48, 68)
    pdf.set_font("Malgun", "B", 11)
    pdf.cell(0, 8, f"  {title}", border=1, ln=1, fill=True)
    pdf.ln(1)


def bullet_list(pdf, items):
    pdf.set_font("Malgun", "", 10)
    pdf.set_text_color(50, 50, 50)
    for item in items:
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 6.2, f"- {item}")
    pdf.ln(1)


def key_value_grid(pdf, source):
    rows = [
        ("회사명", source["company_name"], "고용형태", source["employment_type"]),
        ("직무군", source["job_group"], "경력", source["career_level"]),
        ("근무지", source["location"], "연봉", source["salary"]),
    ]
    label_w = 22
    value_w = 73
    row_h = 8
    pdf.set_draw_color(214, 221, 230)
    for left_label, left_value, right_label, right_value in rows:
        pdf.set_x(pdf.l_margin)
        pdf.set_fill_color(247, 249, 252)
        pdf.set_font("Malgun", "B", 9)
        pdf.set_text_color(55, 65, 81)
        pdf.cell(label_w, row_h, left_label, border=1, fill=True)
        pdf.set_font("Malgun", "", 9)
        pdf.set_text_color(35, 35, 35)
        pdf.cell(value_w, row_h, left_value, border=1)
        pdf.set_fill_color(247, 249, 252)
        pdf.set_font("Malgun", "B", 9)
        pdf.set_text_color(55, 65, 81)
        pdf.cell(label_w, row_h, right_label, border=1, fill=True)
        pdf.set_font("Malgun", "", 9)
        pdf.set_text_color(35, 35, 35)
        pdf.cell(0, row_h, right_value, border=1, ln=1)
    pdf.ln(4)


def render_case(case_dir):
    source = json.loads((case_dir / "source.json").read_text(encoding="utf-8"))

    pdf = JobPostingPDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(14, 14, 14)
    pdf.add_font("Malgun", "", str(FONT_REGULAR), uni=True)
    pdf.add_font("Malgun", "B", str(FONT_BOLD), uni=True)
    pdf.add_page()

    pdf.set_text_color(24, 31, 42)
    pdf.set_font("Malgun", "B", 18)
    pdf.multi_cell(0, 9, source["posting_title"])
    pdf.ln(1)
    pdf.set_font("Malgun", "", 10)
    pdf.set_text_color(95, 105, 120)
    pdf.cell(0, 6, f"{source['company_name']} | {source['case_id']}", ln=1)
    pdf.ln(4)

    key_value_grid(pdf, source)

    section_title(pdf, "채용공고")
    text(pdf, source["posting_body"], size=10.2, line_height=6.4)

    section_title(pdf, "자격요건")
    bullet_list(pdf, source["requirements"])

    section_title(pdf, "우대사항")
    bullet_list(pdf, source["preferred_qualifications"])

    section_title(pdf, "복지 및 근무환경")
    bullet_list(pdf, source["benefits"])

    section_title(pdf, "전형 절차")
    bullet_list(pdf, source["process"])

    pdf.set_y(-25)
    pdf.set_font("Malgun", "", 8)
    pdf.set_text_color(140, 140, 140)
    pdf.multi_cell(0, 5, "본 문서는 HR-COPILOT 채용공고 리스크 감지 테스트를 위한 가상 채용공고입니다.")

    output_dir = case_dir.parent if case_dir.parent != DATASET_DIR else case_dir
    output_path = output_dir / f"{source['case_id']}_job_posting.pdf"
    pdf.output(str(output_path))

    legacy_path = case_dir / "job_posting.pdf"
    if legacy_path.exists():
        legacy_path.unlink()
    nested_case_pdf = case_dir / f"{source['case_id']}_job_posting.pdf"
    if nested_case_pdf.exists() and nested_case_pdf != output_path:
        nested_case_pdf.unlink()


def main():
    if not DATASET_DIR.exists():
        raise FileNotFoundError(DATASET_DIR)
    if not FONT_REGULAR.exists() or not FONT_BOLD.exists():
        raise FileNotFoundError("Malgun Gothic font files were not found.")

    case_dirs = sorted(path.parent for path in DATASET_DIR.rglob("source.json"))
    for case_dir in case_dirs:
        render_case(case_dir)
    print(f"Generated {len(case_dirs)} PDFs in {DATASET_DIR}")


if __name__ == "__main__":
    main()
