import os
import sys
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

model = genai.GenerativeModel("gemini-1.5-flash")

# response = model.generate_content(
#     "Tell me a story about a man who remains unfazed in face of massive setbacks. 500 words, his name is Andrew Tate, and he is a motivational speaker and was an ex-kickboxer ",
#     generation_config=genai.types.GenerationConfig(
#         candidate_count=1,
#         max_output_tokens=4000,
#         temperature=1.0,
#     ),
# )

# print(response.text)

chat = model.start_chat(
    history=[
        {"role": "user", "parts": "Hello"},
        {"role": "model", "parts": "Great to meet you. What would you like to know?"},
    ]     
)

# Function to interact with the chat
def interactive_chat():
    print("Chat has started. Type 'exit' to end the conversation.")
    while True:
        user_input = input("You: ")
        
        if user_input.lower() == "exit":
            print("Chat ended.")
            break
        
        response = chat.send_message(user_input)
        
        print("\n")
        
        print(f"Model: {response.text}")


interactive_chat()
        
