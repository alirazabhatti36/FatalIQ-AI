from flask import Flask, request, send_file, send_from_directory, render_template, jsonify, redirect
from docx2pdf import convert as docx_to_pdf
from pdf2docx import Converter as PDFToWordConverter
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from PIL import Image
import pytesseract
import pandas as pd
import PyPDF2
import docx
import os, re, io, zipfile, shutil
import json

# Try to import optional dependencies for Render compatibility
try:
    import fitz  # PyMuPDF - for PDF to Image (no external dependencies)
except ImportError:
    fitz = None

try:
    import easyocr  # For OCR (no Tesseract needed)
except ImportError:
    easyocr = None

# --- LinkedIn Optimizer import HATAYA ---
# from linkedin_optimizer import analyze_linkedin_profile, fetch_profile_from_url

# Tesseract path (Sirf Image OCR ke liye, agar Render pe nahi hai toh error dega)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

app = Flask(__name__)
UPLOAD = 'uploads'
os.makedirs(UPLOAD, exist_ok=True)

def save(file, name):
    path = os.path.join(UPLOAD, name)
    file.save(path)
    return path

def extract_text_from_docx(path):
    d = docx.Document(path)
    return ' '.join([p.text for p in d.paragraphs])

def extract_text_from_pdf(path):
    text = ''
    with open(path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ''
    return text

# ─────────────────────────────────────────
#  PAGES (MAIN)
# ─────────────────────────────────────────
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/converter')
def converter():
    return render_template('converter.html')

@app.route('/resume-ats')
def resume_ats():
    return render_template('resume-ats.html')

@app.route('/hr-helper')
def hr_helper():
    return render_template('hr-helper.html')

# ─────────────────────────────────────────
#  NEW PAGES - PRIVACY POLICY, TERMS, ETC.
# ─────────────────────────────────────────

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy-policy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/blogs')
def blogs():
    return render_template('blogs.html')

@app.route('/disclaimer')
def disclaimer():
    return render_template('disclaimer.html')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(app.root_path, 'sitemap.xml', mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    return send_from_directory(app.root_path, 'robots.txt', mimetype='text/plain')

@app.route('/404')
def custom_404_page():
    return send_from_directory(app.root_path, '404.html')

@app.errorhandler(404)
def not_found(_error):
    return send_from_directory(app.root_path, '404.html'), 404

@app.route('/favicon.svg')
def favicon_svg():
    return send_from_directory(app.root_path, 'favicon.svg', mimetype='image/svg+xml')

@app.route('/favicon.ico')
def favicon_ico():
    return send_from_directory(app.root_path, 'favicon.svg', mimetype='image/svg+xml')

# ─────────────────────────────────────────
#  OLD ROUTES REDIRECT
# ─────────────────────────────────────────

@app.route('/resume')
def resume_old():
    return redirect('/resume-ats')

@app.route('/ats')
def ats_old():
    return redirect('/hr-helper')

# ─────────────────────────────────────────
#  RESUME BUILDER - DOCX EXPORT
# ─────────────────────────────────────────
@app.route('/export-resume-docx', methods=['POST'])
def export_resume_docx():
    try:
        from docx.shared import Inches, Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        
        data = request.json
        
        doc = docx.Document()
        
        # Title
        title = doc.add_heading(data.get('name', 'Resume'), 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Contact
        contact_parts = []
        if data.get('email'):
            contact_parts.append(data.get('email'))
        if data.get('phone'):
            contact_parts.append(data.get('phone'))
        if data.get('location'):
            contact_parts.append(data.get('location'))
        if data.get('linkedin'):
            contact_parts.append(data.get('linkedin'))
        
        if contact_parts:
            contact = doc.add_paragraph(' | '.join(contact_parts))
            contact.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph()
        
        # Summary
        if data.get('summary'):
            doc.add_heading('Professional Summary', level=1)
            doc.add_paragraph(data.get('summary'))
        
        # Education
        if data.get('education'):
            doc.add_heading('Education', level=1)
            for edu in data.get('education'):
                if edu.get('degree') or edu.get('school'):
                    p = doc.add_paragraph()
                    degree_text = edu.get('degree', '')
                    school_text = edu.get('school', '')
                    if degree_text and school_text:
                        p.add_run(f"{degree_text} - {school_text}").bold = True
                    elif degree_text:
                        p.add_run(degree_text).bold = True
                    elif school_text:
                        p.add_run(school_text).bold = True
                    
                    year_text = edu.get('year', '')
                    gpa_text = edu.get('gpa', '')
                    if year_text or gpa_text:
                        info = []
                        if year_text:
                            info.append(year_text)
                        if gpa_text:
                            info.append(f"GPA: {gpa_text}")
                        doc.add_paragraph(' | '.join(info))
                    doc.add_paragraph()
        
        # Experience
        if data.get('experience'):
            doc.add_heading('Work Experience', level=1)
            for exp in data.get('experience'):
                if exp.get('title') or exp.get('company'):
                    p = doc.add_paragraph()
                    title_text = exp.get('title', '')
                    company_text = exp.get('company', '')
                    if title_text and company_text:
                        p.add_run(f"{title_text} at {company_text}").bold = True
                    elif title_text:
                        p.add_run(title_text).bold = True
                    elif company_text:
                        p.add_run(company_text).bold = True
                    
                    if exp.get('duration'):
                        doc.add_paragraph(exp.get('duration'))
                    
                    if exp.get('description'):
                        doc.add_paragraph(exp.get('description'), style='List Bullet')
                    doc.add_paragraph()
        
        # Skills
        if data.get('skills'):
            doc.add_heading('Skills', level=1)
            skills_list = [s.strip() for s in data.get('skills').split(',') if s.strip()]
            doc.add_paragraph(', '.join(skills_list))
        
        # Custom Sections
        if data.get('customSections'):
            for section in data.get('customSections'):
                if section.get('title') and section.get('items'):
                    doc.add_heading(section.get('title'), level=1)
                    for item in section.get('items'):
                        if item.get('text'):
                            doc.add_paragraph(item.get('text'), style='List Bullet')
        
        # Save to bytes
        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)
        
        return send_file(
            file_stream,
            as_attachment=True,
            download_name='resume.docx',
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────
#  OFFICE CONVERTERS
# ─────────────────────────────────────────
@app.route('/word-to-pdf', methods=['POST'])
def word_to_pdf():
    try:
        p = save(request.files['file'], 'input.docx')
        docx_to_pdf(p, os.path.join(UPLOAD,'output.pdf'))
        return send_file(os.path.join(UPLOAD,'output.pdf'), as_attachment=True, download_name='converted.pdf')
    except Exception as e:
        return jsonify({'error': f'Word to PDF failed: {str(e)}'}), 500

@app.route('/pdf-to-word', methods=['POST'])
def pdf_to_word():
    try:
        p = save(request.files['file'], 'input.pdf')
        cv = PDFToWordConverter(p)
        out = os.path.join(UPLOAD,'output.docx')
        cv.convert(out); cv.close()
        return send_file(out, as_attachment=True, download_name='converted.docx')
    except Exception as e:
        return jsonify({'error': f'PDF to Word failed: {str(e)}'}), 500

@app.route('/ppt-to-pdf', methods=['POST'])
def ppt_to_pdf():
    try:
        p = save(request.files['file'], 'input.pptx')
        import comtypes.client
        ppt = comtypes.client.CreateObject("Powerpoint.Application")
        ppt.Visible = 1
        deck = ppt.Presentations.Open(os.path.abspath(p))
        out  = os.path.abspath(os.path.join(UPLOAD,'output.pdf'))
        deck.SaveAs(out, 32); deck.Close(); ppt.Quit()
        return send_file(out, as_attachment=True, download_name='converted.pdf')
    except Exception as e:
        return jsonify({'error': f'PPT to PDF failed: {str(e)}'}), 500

@app.route('/excel-to-pdf', methods=['POST'])
def excel_to_pdf():
    try:
        p = save(request.files['file'], 'input.xlsx')
        import comtypes.client
        xl  = comtypes.client.CreateObject("Excel.Application")
        xl.Visible = 0
        wb  = xl.Workbooks.Open(os.path.abspath(p))
        out = os.path.abspath(os.path.join(UPLOAD,'output.pdf'))
        wb.ExportAsFixedFormat(0, out); wb.Close(False); xl.Quit()
        return send_file(out, as_attachment=True, download_name='converted.pdf')
    except Exception as e:
        return jsonify({'error': f'Excel to PDF failed: {str(e)}'}), 500

@app.route('/rtf-to-docx', methods=['POST'])
def rtf_to_docx():
    try:
        p = save(request.files['file'], 'input.rtf')
        import comtypes.client
        word = comtypes.client.CreateObject("Word.Application")
        word.Visible = 0
        doc  = word.Documents.Open(os.path.abspath(p))
        out  = os.path.abspath(os.path.join(UPLOAD,'output.docx'))
        doc.SaveAs2(out, 16); doc.Close(); word.Quit()
        return send_file(out, as_attachment=True, download_name='converted.docx')
    except Exception as e:
        return jsonify({'error': f'RTF to DOCX failed: {str(e)}'}), 500

# ─────────────────────────────────────────
#  PDF TOOLS
# ─────────────────────────────────────────
@app.route('/merge-pdf', methods=['POST'])
def merge_pdf():
    files  = request.files.getlist('files')
    writer = PyPDF2.PdfWriter()
    for f in files:
        p = save(f, f.filename)
        reader = PyPDF2.PdfReader(p)
        for page in reader.pages:
            writer.add_page(page)
    out = os.path.join(UPLOAD,'merged.pdf')
    with open(out,'wb') as o:
        writer.write(o)
    return send_file(out, as_attachment=True, download_name='merged.pdf')

@app.route('/split-pdf', methods=['POST'])
def split_pdf():
    p      = save(request.files['file'], 'input.pdf')
    reader = PyPDF2.PdfReader(p)
    zpath  = os.path.join(UPLOAD,'split_pages.zip')
    with zipfile.ZipFile(zpath,'w') as zf:
        for i, page in enumerate(reader.pages):
            writer = PyPDF2.PdfWriter()
            writer.add_page(page)
            ppath = os.path.join(UPLOAD, f'page_{i+1}.pdf')
            with open(ppath,'wb') as f:
                writer.write(f)
            zf.write(ppath, f'page_{i+1}.pdf')
    return send_file(zpath, as_attachment=True, download_name='split_pages.zip')

@app.route('/compress-pdf', methods=['POST'])
def compress_pdf():
    p      = save(request.files['file'], 'input.pdf')
    reader = PyPDF2.PdfReader(p)
    writer = PyPDF2.PdfWriter()
    for page in reader.pages:
        page.compress_content_streams()
        writer.add_page(page)
    out = os.path.join(UPLOAD,'compressed.pdf')
    with open(out,'wb') as f:
        writer.write(f)
    return send_file(out, as_attachment=True, download_name='compressed.pdf')

@app.route('/rotate-pdf', methods=['POST'])
def rotate_pdf():
    p       = save(request.files['file'], 'input.pdf')
    degrees = int(request.form.get('degrees', 90))
    reader  = PyPDF2.PdfReader(p)
    writer  = PyPDF2.PdfWriter()
    for page in reader.pages:
        page.rotate(degrees)
        writer.add_page(page)
    out = os.path.join(UPLOAD,'rotated.pdf')
    with open(out,'wb') as f:
        writer.write(f)
    return send_file(out, as_attachment=True, download_name='rotated.pdf')

@app.route('/lock-pdf', methods=['POST'])
def lock_pdf():
    p        = save(request.files['file'], 'input.pdf')
    password = request.form.get('password', '1234')
    reader   = PyPDF2.PdfReader(p)
    writer   = PyPDF2.PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    out = os.path.join(UPLOAD,'locked.pdf')
    with open(out,'wb') as f:
        writer.write(f)
    return send_file(out, as_attachment=True, download_name='locked.pdf')

@app.route('/unlock-pdf', methods=['POST'])
def unlock_pdf():
    p        = save(request.files['file'], 'input.pdf')
    password = request.form.get('password', '')
    reader   = PyPDF2.PdfReader(p)
    if reader.is_encrypted:
        reader.decrypt(password)
    writer = PyPDF2.PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    out = os.path.join(UPLOAD,'unlocked.pdf')
    with open(out,'wb') as f:
        writer.write(f)
    return send_file(out, as_attachment=True, download_name='unlocked.pdf')

@app.route('/watermark-pdf', methods=['POST'])
def watermark_pdf():
    p    = save(request.files['file'], 'input.pdf')
    text = request.form.get('watermark', 'CONFIDENTIAL')
    reader = PyPDF2.PdfReader(p)
    writer = PyPDF2.PdfWriter()
    wm_path = os.path.join(UPLOAD,'wm.pdf')
    c = SimpleDocTemplate(wm_path, pagesize=A4)
    style = ParagraphStyle('wm', fontSize=40, textColor=colors.Color(0.7,0.7,0.7,0.4),
        fontName='Helvetica-Bold')
    c.build([Paragraph(text, style)])
    wm_reader = PyPDF2.PdfReader(wm_path)
    wm_page   = wm_reader.pages[0]
    for page in reader.pages:
        page.merge_page(wm_page)
        writer.add_page(page)
    out = os.path.join(UPLOAD,'watermarked.pdf')
    with open(out,'wb') as f:
        writer.write(f)
    return send_file(out, as_attachment=True, download_name='watermarked.pdf')

@app.route('/delete-pages', methods=['POST'])
def delete_pages():
    p     = save(request.files['file'], 'input.pdf')
    pages = request.form.get('pages', '')
    to_delete = set()
    for part in pages.split(','):
        part = part.strip()
        if '-' in part:
            a,b = part.split('-')
            to_delete.update(range(int(a)-1, int(b)))
        elif part:
            to_delete.add(int(part)-1)
    reader = PyPDF2.PdfReader(p)
    writer = PyPDF2.PdfWriter()
    for i, page in enumerate(reader.pages):
        if i not in to_delete:
            writer.add_page(page)
    out = os.path.join(UPLOAD,'deleted.pdf')
    with open(out,'wb') as f:
        writer.write(f)
    return send_file(out, as_attachment=True, download_name='deleted_pages.pdf')

@app.route('/extract-pages', methods=['POST'])
def extract_pages():
    p     = save(request.files['file'], 'input.pdf')
    pages = request.form.get('pages', '')
    to_keep = set()
    for part in pages.split(','):
        part = part.strip()
        if '-' in part:
            a,b = part.split('-')
            to_keep.update(range(int(a)-1, int(b)))
        elif part:
            to_keep.add(int(part)-1)
    reader = PyPDF2.PdfReader(p)
    writer = PyPDF2.PdfWriter()
    for i, page in enumerate(reader.pages):
        if i in to_keep:
            writer.add_page(page)
    out = os.path.join(UPLOAD,'extracted.pdf')
    with open(out,'wb') as f:
        writer.write(f)
    return send_file(out, as_attachment=True, download_name='extracted_pages.pdf')

# ─────────────────────────────────────────
#  PDF TO IMAGE - Using PyMuPDF (No system dependencies)
# ─────────────────────────────────────────
@app.route('/pdf-to-image', methods=['POST'])
def pdf_to_image():
    try:
        import fitz
        p = save(request.files['file'], 'input.pdf')
        doc = fitz.open(p)
        zpath = os.path.join(UPLOAD, 'pdf_images.zip')
        with zipfile.ZipFile(zpath, 'w') as zf:
            for i, page in enumerate(doc):
                pix = page.get_pixmap()
                ipath = os.path.join(UPLOAD, f'page_{i+1}.jpg')
                pix.save(ipath)
                zf.write(ipath, f'page_{i+1}.jpg')
        doc.close()
        return send_file(zpath, as_attachment=True, download_name='pdf_images.zip')
    except Exception as e:
        return jsonify({'error': f'PDF to Image failed: {str(e)}. Try: pip install PyMuPDF'}), 500

@app.route('/pdf-to-txt', methods=['POST'])
def pdf_to_txt():
    p    = save(request.files['file'], 'input.pdf')
    text = extract_text_from_pdf(p)
    out  = os.path.join(UPLOAD,'output.txt')
    with open(out,'w', encoding='utf-8') as f:
        f.write(text)
    return send_file(out, as_attachment=True, download_name='converted.txt')

@app.route('/txt-to-pdf', methods=['POST'])
def txt_to_pdf():
    p = save(request.files['file'], 'input.txt')
    with open(p,'r', encoding='utf-8') as f:
        text = f.read()
    out = os.path.join(UPLOAD,'output.pdf')
    doc = SimpleDocTemplate(out, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    style = ParagraphStyle('body', fontSize=11, leading=16)
    story = [Paragraph(line or ' ', style) for line in text.split('\n')]
    doc.build(story)
    return send_file(out, as_attachment=True, download_name='converted.pdf')

@app.route('/add-page-numbers', methods=['POST'])
def add_page_numbers():
    p      = save(request.files['file'], 'input.pdf')
    reader = PyPDF2.PdfReader(p)
    writer = PyPDF2.PdfWriter()
    total  = len(reader.pages)
    for i, page in enumerate(reader.pages):
        pn_path = os.path.join(UPLOAD, f'pn_{i}.pdf')
        pn_doc  = SimpleDocTemplate(pn_path, pagesize=A4,
            rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
        style = ParagraphStyle('pn', fontSize=9, textColor=colors.grey)
        pn_doc.build([Spacer(1, 26*cm), Paragraph(f'Page {i+1} of {total}', style)])
        pn_reader = PyPDF2.PdfReader(pn_path)
        page.merge_page(pn_reader.pages[0])
        writer.add_page(page)
    out = os.path.join(UPLOAD,'numbered.pdf')
    with open(out,'wb') as f:
        writer.write(f)
    return send_file(out, as_attachment=True, download_name='numbered.pdf')

# ─────────────────────────────────────────
#  IMAGE TOOLS
# ─────────────────────────────────────────
@app.route('/image-to-pdf', methods=['POST'])
def image_to_pdf():
    p   = save(request.files['file'], 'input_img.png')
    img = Image.open(p).convert('RGB')
    out = os.path.join(UPLOAD,'output.pdf')
    img.save(out,'PDF')
    return send_file(out, as_attachment=True, download_name='converted.pdf')

# ─────────────────────────────────────────
#  IMAGE TO WORD - Using EasyOCR (No Tesseract needed)
# ─────────────────────────────────────────
@app.route('/image-to-word', methods=['POST'])
def image_to_word():
    try:
        import easyocr
        p = save(request.files['file'], 'input_img.png')
        reader = easyocr.Reader(['en'])
        result = reader.readtext(p)
        text = ' '.join([item[1] for item in result])
        
        d = docx.Document()
        d.add_heading('Extracted Text', 0)
        for line in text.split('\n'):
            if line.strip():
                d.add_paragraph(line.strip())
        out = os.path.join(UPLOAD, 'output.docx')
        d.save(out)
        return send_file(out, as_attachment=True, download_name='converted.docx')
    except Exception as e:
        return jsonify({'error': f'OCR to Word failed: {str(e)}. Try: pip install easyocr'}), 500

@app.route('/image-to-excel', methods=['POST'])
def image_to_excel():
    try:
        import easyocr
        p = save(request.files['file'], 'input_img.png')
        reader = easyocr.Reader(['en'])
        result = reader.readtext(p)
        text = ' '.join([item[1] for item in result])
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        rows = [re.split(r'\t|  {2,}', l) for l in lines]
        out = os.path.join(UPLOAD, 'output.xlsx')
        pd.DataFrame(rows).to_excel(out, index=False, header=False)
        return send_file(out, as_attachment=True, download_name='converted.xlsx')
    except Exception as e:
        return jsonify({'error': f'OCR to Excel failed: {str(e)}. Try: pip install easyocr'}), 500

@app.route('/ocr-to-text', methods=['POST'])
def ocr_to_text():
    try:
        import easyocr
        p = save(request.files['file'], 'input_img.png')
        reader = easyocr.Reader(['en'])
        result = reader.readtext(p)
        text = ' '.join([item[1] for item in result])
        
        out = os.path.join(UPLOAD, 'ocr_output.txt')
        with open(out, 'w', encoding='utf-8') as f:
            f.write(text)
        return send_file(out, as_attachment=True, download_name='ocr_text.txt')
    except Exception as e:
        return jsonify({'error': f'OCR to Text failed: {str(e)}. Try: pip install easyocr'}), 500

@app.route('/jpg-to-png', methods=['POST'])
def jpg_to_png():
    p   = save(request.files['file'], 'input.jpg')
    out = os.path.join(UPLOAD,'output.png')
    Image.open(p).save(out,'PNG')
    return send_file(out, as_attachment=True, download_name='converted.png')

@app.route('/png-to-jpg', methods=['POST'])
def png_to_jpg():
    p   = save(request.files['file'], 'input.png')
    out = os.path.join(UPLOAD,'output.jpg')
    Image.open(p).convert('RGB').save(out,'JPEG')
    return send_file(out, as_attachment=True, download_name='converted.jpg')

@app.route('/webp-to-png', methods=['POST'])
def webp_to_png():
    p   = save(request.files['file'], 'input.webp')
    out = os.path.join(UPLOAD,'output.png')
    Image.open(p).save(out,'PNG')
    return send_file(out, as_attachment=True, download_name='converted.png')

@app.route('/svg-to-png', methods=['POST'])
def svg_to_png():
    try:
        import cairosvg
        p   = save(request.files['file'], 'input.svg')
        out = os.path.join(UPLOAD,'output.png')
        cairosvg.svg2png(url=p, write_to=out)
        return send_file(out, as_attachment=True, download_name='converted.png')
    except Exception as e:
        return jsonify({'error': f'SVG to PNG failed: {str(e)}. Try: pip install cairosvg'}), 500

@app.route('/compress-image', methods=['POST'])
def compress_image():
    p       = save(request.files['file'], 'input_img.png')
    quality = int(request.form.get('quality', 60))
    img     = Image.open(p).convert('RGB')
    out     = os.path.join(UPLOAD,'compressed.jpg')
    img.save(out,'JPEG', quality=quality)
    return send_file(out, as_attachment=True, download_name='compressed.jpg')

# ─────────────────────────────────────────
#  ATS (for HR Helper)
# ─────────────────────────────────────────
@app.route('/ats-score', methods=['POST'])
def ats_score():
    resume_file = request.files['resume']
    job_desc    = request.form.get('job_desc', '')
    filename    = resume_file.filename
    ext         = filename.rsplit('.',1)[-1]
    p           = save(resume_file, filename)
    resume_text = extract_text_from_pdf(p) if ext=='pdf' else extract_text_from_docx(p)
    resume_words = set(re.findall(r'\b\w+\b', resume_text.lower()))
    job_words    = set(re.findall(r'\b\w+\b', job_desc.lower()))
    stop = {'the','and','for','are','with','this','that','you','your','have','from',
            'will','can','was','they','their','been','has','but','not','all','our',
            'its','also','more','when','which','a','an','in','of','to','is','on','at'}
    job_keywords = job_words - stop
    if not job_keywords:
        return jsonify({'score':0,'matched':[],'missing':[],'filename':filename})
    matched = sorted(job_keywords & resume_words)
    missing = sorted(job_keywords - resume_words)
    score   = round(len(matched)/len(job_keywords)*100)
    return jsonify({'score':score,'matched':matched,'missing':missing,'filename':filename})

@app.route('/download-resume/<filename>')
def download_resume(filename):
    path = os.path.join(UPLOAD, filename)
    return send_file(path, as_attachment=True, download_name=filename)

# ─────────────────────────────────────────
#  OLD RESUME MAKER (kept for compatibility)
# ─────────────────────────────────────────
@app.route('/make-resume', methods=['POST'])
def make_resume():
    data = request.json
    out  = os.path.join(UPLOAD,'my_resume.pdf')
    doc  = SimpleDocTemplate(out, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    name_s    = ParagraphStyle('n', fontSize=24, fontName='Helvetica-Bold', textColor=colors.HexColor('#2d3748'), spaceAfter=4)
    contact_s = ParagraphStyle('c', fontSize=10, fontName='Helvetica',     textColor=colors.HexColor('#718096'), spaceAfter=2)
    section_s = ParagraphStyle('s', fontSize=13, fontName='Helvetica-Bold', textColor=colors.HexColor('#2b6cb0'), spaceBefore=14, spaceAfter=4)
    body_s    = ParagraphStyle('b', fontSize=10, fontName='Helvetica',     textColor=colors.HexColor('#2d3748'), spaceAfter=3, leading=15)
    bold_s    = ParagraphStyle('bl',fontSize=10, fontName='Helvetica-Bold', textColor=colors.HexColor('#2d3748'), spaceAfter=1)
    hr = lambda: HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceAfter=5)
    story = []
    story.append(Paragraph(data.get('name',''), name_s))
    story.append(Paragraph(' | '.join(filter(None,[data.get('email',''),data.get('phone',''),data.get('location',''),data.get('linkedin','')])), contact_s))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2b6cb0'), spaceAfter=8))
    if data.get('summary'):
        story += [Paragraph('PROFESSIONAL SUMMARY',section_s), hr(), Paragraph(data['summary'],body_s)]
    if data.get('education'):
        story += [Paragraph('EDUCATION',section_s), hr()]
        for e in data['education']:
            story += [Paragraph(f"{e.get('degree','')} — {e.get('school','')}",bold_s), Paragraph(f"{e.get('year','')}  {e.get('gpa','')}",body_s)]
    if data.get('experience'):
        story += [Paragraph('WORK EXPERIENCE',section_s), hr()]
        for e in data['experience']:
            story += [Paragraph(f"{e.get('title','')} — {e.get('company','')}",bold_s), Paragraph(e.get('duration',''),body_s), Paragraph(e.get('description',''),body_s), Spacer(1,4)]
    if data.get('skills'):
        story += [Paragraph('SKILLS',section_s), hr(), Paragraph(data['skills'],body_s)]
    if data.get('projects'):
        story += [Paragraph('PROJECTS',section_s), hr()]
        for p in data['projects']:
            story += [Paragraph(p.get('title',''),bold_s), Paragraph(p.get('description',''),body_s), Spacer(1,4)]
    doc.build(story)
    return send_file(out, as_attachment=True, download_name='my_resume.pdf')

# ─────────────────────────────────────────
#  LINKEDIN - File Upload API
# ─────────────────────────────────────────
@app.route('/upload-linkedin-file', methods=['POST'])
def upload_linkedin_file():
    try:
        file = request.files['file']
        if not file:
            return jsonify({'error': 'No file uploaded'}), 400
        
        filename = file.filename
        ext = filename.rsplit('.', 1)[-1].lower()
        path = save(file, filename)
        
        if ext == 'pdf':
            text = extract_text_from_pdf(path)
        elif ext == 'docx':
            text = extract_text_from_docx(path)
        elif ext == 'txt':
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            return jsonify({'error': 'Unsupported file type'}), 400
        
        return jsonify({'text': text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────
#  RUN SERVER ON PORT 5001
# ─────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=5001)
