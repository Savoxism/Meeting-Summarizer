import os
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI
import itertools
import threading
import time
import sys

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

client = OpenAI(api_key=OPENAI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

media = Path('audio_files')

def spinner(message, event):
    spinner_cycle = itertools.cycle(['|', '/', '-', '\\'])
    while not event.is_set():
        sys.stdout.write(f'\r{message} {next(spinner_cycle)}')
        sys.stdout.flush()
        time.sleep(0.1)
        
def generate_transcript(audio_file):
    print("Generating trasncript...")
    stop_event = threading.Event()
    t = threading.Thread(target=spinner, args=("Processing transcription...", stop_event))
    t.start()
    
    try:
        prompt = "Generate a transcript of the speech."
        transcript_response = model.generate_content([prompt, audio_file])
        transcript = transcript_response.text
    finally:
        stop_event.set()
        t.join()
        
    return transcript

def summarize_transcript(transcript):
    print("Summarizing the transcript with GPT-4...")
    stop_event = threading.Event()
    t = threading.Thread(target=spinner, args=("Summarizing...", stop_event))
    t.start()
    
    try:
        requirement = '''
        You are an expert at summarizing transcripts. In the given transcript, I want you to produce a detailed report that meets these requirements:
        + A quick summary of the meeting/ lecture
        + What should be done (there should be at least 5 points)
        + Key date and deadlines (if any)
        
        It must strictly follow this format
            Summary: 5-10 sentences
            What Should Be Done:
            - Complete the pending documentation.
            - Review the code changes.
            - Plan the next sprint.
            - Organize a team meeting for review.
            - Assign new tasks for next sprint.

            Upcoming Tasks and Deadlines:
            - Documentation Update: March 18, 2024
            - Code Review: March 20, 2024
            - Sprint Planning: March 22, 2024    
        '''

        gpt4_prompt = f"Summarize the content of this transcript from a meeting:\n\n{transcript}\n\n"

        gpt4_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": requirement},
                {"role": "user", "content": gpt4_prompt}
            ],
            max_tokens=400,
            temperature=0.3,
        )
        summary = gpt4_response.choices[0].message.content
    finally:
        stop_event.set()
        t.join()

    return summary

def generate_pdf(summary, output_path="summary_report.pdf"):
    print("Generating PDF file...")
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph("Summary Report", styles['Title']))
    elements.append(Spacer(1, 12))

    # Parsing the predefined format in the summary string
    sections = summary.split("\n\n")

    # Process the "Summary" section
    elements.append(Paragraph("Summary:", styles['Heading2']))
    summary_text = sections[0].replace("Summary:", "").strip()  # Clean up the "Summary" text
    elements.append(Paragraph(summary_text, styles['BodyText']))
    elements.append(Spacer(1, 12))

    # Process the "What Should Be Done" section
    elements.append(Paragraph("What Should Be Done:", styles['Heading2']))
    what_should_be_done = sections[1].replace("What Should Be Done:", "").strip()
    bullet_points = [point.strip() for point in what_should_be_done.split("\n") if point.strip()]
    if bullet_points:
        elements.append(ListFlowable([ListItem(Paragraph(f"- {point}", styles['BodyText'])) for point in bullet_points], bulletType='bullet'))
    elements.append(Spacer(1, 12))

    # Process the "Upcoming Tasks and Deadlines" section
    if len(sections) > 2:
        elements.append(Paragraph("Upcoming Tasks and Deadlines:", styles['Heading2']))
        tasks = [task.strip() for task in sections[2].replace("Upcoming Tasks and Deadlines:", "").strip().split("\n") if task.strip()]
        for task in tasks:
            elements.append(Paragraph(f"• {task}", styles['BodyText']))
    
    elements.append(Spacer(1, 12))

    # Build PDF
    doc.build(elements)
    print(f"PDF saved at: {output_path}")

##############################
# Upload the audio file using the File API
print("Uploading the file...")
stop_event = threading.Event()
t = threading.Thread(target=spinner, args=("Uploading...", stop_event))
t.start()

try:
    myfile = genai.upload_file(media / "y2mate.com - Stanford CS224N NLP with Deep Learning  2023  Lecture 8  SelfAttention and Transformers.mp3")
finally:
    stop_event.set()
    t.join()
    
print(f"\nUploaded file: {myfile}")

# Generate the transcript
transcript = generate_transcript(myfile)
# print(f"\nTranscript: {transcript}")

# Summarize the transcript
summary = summarize_transcript(transcript)
print("\nSummary in tabular format:")
print(summary)

generate_pdf(summary, output_path="summary_report.pdf")