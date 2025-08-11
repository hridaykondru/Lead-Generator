import base64
from dotenv import load_dotenv
import os
import pandas as pd
import requests
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# --- CONFIGURATION ---
# IMPORTANT: Replace these with your actual email credentials.
# For Gmail, you may need to generate an "App Password".
# It is recommended to use environment variables instead of hardcoding.
load_dotenv(dotenv_path='variables.env')  # Load environment variables from .env file
SMTP_SERVER = 'smtp.gmail.com'  # Example for Gmail
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv('email_address')
EMAIL_PASSWORD = os.getenv('email_password')

# Gemini API Configuration
# NOTE: The execution environment will handle the API key automatically.
# If running locally, you would set your API key here.
GEMINI_API_KEY = os.getenv('gemini_api_key')
GEMINI_API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}'

# --- STEP 1: LOAD AND PREPARE DATA ---

def load_influencer_data(filepath='influencers.csv'):
    """
    Loads influencer data from a CSV file into a pandas DataFrame.
    
    Args:
        filepath (str): The path to the CSV file.
        
    Returns:
        pandas.DataFrame: The loaded data, or None if the file is not found.
    """
    try:
        # To run this script, create a file named 'influencers.csv' with the
        # columns you described: id,username,full_name,age,gender,email,
        # country,category,followers,engagement,avg_likes,avg_comments,follower_growth_rate
        #
        # Example CSV content:
        # id,username,full_name,age,gender,email,country,category,followers,engagement,avg_likes,avg_comments,follower_growth_rate
        # 257,alex257,Alex Johnson,29,nonbinary,alex257@example.com,India,Technology,73418,0.0587,3802,423,0.0342
        # 258,casey258,Casey Williams,35,female,casey258@example.com,USA,Technology,150230,0.081,10901,1220,0.051
        # 259,riley259,Riley Brown,22,male,riley259@example.com,India,Fitness,25000,0.12,2700,300,0.08
        
        df = pd.read_csv(filepath)
        print(f"Successfully loaded {len(df)} records from {filepath}")
        return df
    except FileNotFoundError:
        print(f"Error: The file {filepath} was not found.")
        print("Please ensure you have created the 'influencers.csv' file in the same directory.")
        return None

# --- STEP 2: CALL GEMINI API FOR ANALYSIS AND EMAIL GENERATION ---

def get_ai_recommendations(filtered_data, k):
    """
    Sends data to the Gemini API to get top influencers and generated emails.

    Args:
        filtered_data (pandas.DataFrame): The pre-filtered DataFrame of influencers.
        k (int): The number of top influencers to retrieve.

    Returns:
        list: A list of dictionaries, where each dictionary contains
              the name, email, subject, and body for an email. Returns None on failure.
    """
    print(f"\nSending data for {len(filtered_data)} influencers to the Gemini API...")

    # Convert dataframe to a JSON string for the prompt
    data_json_string = filtered_data.to_json(orient='records', indent=2)

    prompt = f"""
        You are a highly-discerning talent scout for 'GAIMfes', a prestigious cultural festival hosted by IIM Ahmedabad.
        Your objective is to analyze the following list of influencers based on their data. Your analysis should consider a holistic view: high follower count is good, but high engagement and follower growth are even better. Calculate an internal 'overall_score' for each influencer to represent their potential impact and brand alignment for our event.

        After scoring, identify the top {k} influencers from the provided list.

        For ONLY these top {k} influencers, you must generate a personalized email inviting them to be a featured guest.
        The tone must be professional, respectful, and convey the prestige of the event.

        Event Details:
        - Event Name: IIM Ahmedabad Cultural Fest 'GAIMfes'
        - Location: IIM Ahmedabad Campus, Gujarat, India
        - Theme: A confluence of modern digital culture, traditional arts, and intellectual exchange.

        Your final output MUST be a single, valid JSON array containing exactly {k} objects.
        Do not include any text, notes, or markdown formatting before or after the JSON array.
        Each object in the array must follow this exact structure:
        {{
          "name": "The influencer's full_name",
          "email": "The influencer's email address",
          "subject": "A compelling, personalized email subject line",
          "body": "The core message of the email ONLY. It must not include a salutation (like 'Dear...') or a closing (like 'Regards...'), as those are already in the template. Start the body with a phrase like 'The GAIMfes team at IIM Ahmedabad has been following your work...' to set a formal tone. Reference their specific content category (e.g., 'your insightful content in the technology space'). Explain why their voice is a perfect fit for our event. The body must be a single string with newline characters (\\n) for paragraph breaks and must not contain any placeholders like [Your Name] or [Your Title]."
        }}

        Here is the influencer data in JSON format:
        {data_json_string}
    """

    headers = {'Content-Type': 'application/json'}
    payload = json.dumps({
        "contents": [{
            "role": "user",
            "parts": [{ "text": prompt }]
        }]
    })

    try:
        response = requests.post(GEMINI_API_URL, headers=headers, data=payload)
        response.raise_for_status()  # Raises an exception for bad status codes (4xx or 5xx)
        
        result = response.json()
        
        # Extract the text and parse it as JSON
        json_string = result['candidates'][0]['content']['parts'][0]['text'].replace('```json', '').replace('```', '').replace('\xa0', ' ').strip()
        recommended_influencers = json.loads(json_string)
        
        print(f"Successfully received {len(recommended_influencers)} recommendations from the AI.")
        return recommended_influencers

    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API: {e}")
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"Error parsing Gemini API response: {e}")
        print("Received response:", response.text)

    return None

# --- STEP 3: CREATE AND SEND EMAILS ---

def create_html_email(influencer_details):
    """
    Creates a MIMEMultipart email object using an HTML template.
    
    Args:
        influencer_details (dict): A dictionary containing name, subject, and body.
        
    Returns:
        str: The full HTML content of the email.
    """
    # Convert newlines in the body to <br> tags for HTML rendering
    html_body = influencer_details['body'].replace('\n', '<br>')
    
    # Mock HTML Email Template
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            .header {{ 
                background: url('https://pbs.twimg.com/media/FnOix3MacAEz743.jpg:large') no-repeat center center; 
                background-size: cover;
                color: #ffffff; 
                padding: 60px 40px; 
                text-align: center; 
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
            }}            
            .header h1 {{ margin: 0; font-size: 30px; }}
            .header p {{ margin: 5px 0 0; font-size: 24px; }}
            .content {{ padding: 30px 40px; color: #333333; line-height: 1.6; }}
            .content p {{ margin: 0 0 15px; }}
            .footer {{ background-color: #f8f9fa; text-align: center; padding: 20px; font-size: 12px; color: #777777; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>IIM Ahmedabad</h1>
                <p>Invitation to GAIMfes Cultural Festival</p>
            </div>
            <div class="content">
                <p>Dear {influencer_details['name']},</p>
                {html_body}
                <p>We eagerly await the possibility of welcoming you to our campus.</p>
                <p>Warm regards,<br>The Organizing Committee<br>GAIMfes<br>IIM Ahmedabad</p>
            </div>
            <div class="footer">
                <p>Indian Institute of Management Ahmedabad, Vastrapur, Ahmedabad, Gujarat, India</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_template

def send_email(recipient_email, subject, html_content):
    """
    Sends an email using the configured SMTP settings.

    Args:
        recipient_email (str): The email address of the recipient.
        subject (str): The subject of the email.
        html_content (str): The HTML body of the email.
        
    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """
    if not EMAIL_ADDRESS or EMAIL_ADDRESS == 'your_email@gmail.com':
        print("\n--- SENDING SKIPPED ---")
        print(f"Recipient: {recipient_email}")
        print(f"Subject: {subject}")
        print("Reason: Email credentials are not configured in the script.")
        print("-----------------------\n")
        return False

    msg = MIMEMultipart('alternative')
    msg['From'] = f"IIM Ahmedabad Events <{EMAIL_ADDRESS}>"
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))
    # Uncomment the next line to see the generated HTML
    # print(msg.as_string())  
    try:
        print(f"Connecting to SMTP server to send email to {recipient_email}...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, recipient_email, msg.as_string())
        server.quit()
        print(f"Successfully sent email to {recipient_email}")
        return True
    except Exception as e:
        print(f"Error sending email to {recipient_email}: {e}")
        return False


# --- MAIN EXECUTION ---

if __name__ == "__main__":
    # 1. Load data
    all_influencers_df = load_influencer_data().iloc[0:5]

    if all_influencers_df is not None:
        # 2. Get user input for filtering
        unique_categories = all_influencers_df['category'].unique()
        print("\nAvailable Categories:", ", ".join(unique_categories))
        
        target_category = input("Enter the category you want to target: ")
        while target_category not in unique_categories:
            print("Invalid category. Please choose from the list above.")
            target_category = input("Enter the category you want to target: ")

        k_value = int(input("Enter the number of top influencers to contact (K): "))

        # 3. Filter the dataset
        filtered_df = all_influencers_df[all_influencers_df['category'] == target_category]

        if filtered_df.empty:
            print(f"No influencers found in the '{target_category}' category.")
        else:
            # 4. Get AI recommendations
            top_influencers = get_ai_recommendations(filtered_df, k_value)

            # 5. Send emails
            if top_influencers:
                print(f"\nPreparing to send {len(top_influencers)} emails...")
                for influencer in top_influencers:
                    html_email_content = create_html_email(influencer)
                    send_email(
                        recipient_email=influencer['email'],
                        subject=influencer['subject'],
                        html_content=html_email_content
                    )
                print("\nOutreach process complete.")

