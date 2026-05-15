from fpdf import FPDF
import markdown

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)

text = """
# Summary

This is a **test** string with *italics*.
And some ✨ emojis which might break Arial.
"""

cleaned = text.encode("ascii", "ignore").decode("ascii")

html = markdown.markdown(cleaned)
# Wait, HTMLMixin was removed in fpdf2 or moved?
# Actually in fpdf2, `write_html` prints from HTML.
try:
    pdf.write_html(html)
    pdf.output("test.pdf")
    print("Success")
except Exception as e:
    print("Error:", e)
