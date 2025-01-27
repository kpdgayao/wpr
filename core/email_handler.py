# core/email_handler.py
import logging
import requests
from typing import Dict, Any
from datetime import datetime
import json
import base64

class EmailHandler:
    def __init__(self, api_key: str, api_secret: str):
        """Initialize Mailjet client"""
        try:
            self.api_key = api_key
            self.api_secret = api_secret
            self.sender_email = "go@iol.ph"
            self.sender_name = "IOL Inc."
            self.base_url = "https://api.mailjet.com/v3.1"
            
            # Create base64 auth string
            auth = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()
            self.headers = {
                'Authorization': f'Basic {auth}',
                'Content-Type': 'application/json'
            }
            
            logging.info("Email handler initialized successfully")
                
        except Exception as e:
            logging.error(f"Failed to initialize email handler: {str(e)}")
            raise

    def send_wpr_notification(self, to_email: str, to_name: str, week_number: int, year: int, ai_analysis: str = None) -> bool:
        """Send WPR submission notification email"""
        try:
            logging.info(f"Preparing to send WPR notification to {to_email}")
            current_date = datetime.now().strftime("%B %d, %Y")
            
            # Create both text and HTML versions
            text_content = f"""
Dear {to_name},

Your Weekly Productivity Report for Week {week_number}, {year} has been successfully submitted on {current_date}.

You can view your submission and past reports in the WPR dashboard.

"""
            if ai_analysis:
                text_content += f"""
AI Analysis of Your Report:
{ai_analysis}
"""

            text_content += """
Best regards,
IOL Inc.
            """
            
            html_content = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ color: #2E86C1; margin-bottom: 20px; }}
                        .content {{ margin: 20px 0; }}
                        .analysis {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                        .footer {{ margin-top: 30px; color: #666; font-size: 0.9em; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>WPR Submission Confirmation</h2>
                        </div>
                        
                        <div class="content">
                            <p>Dear {to_name},</p>
                            <p>Your Weekly Productivity Report for Week {week_number}, {year} has been successfully submitted on {current_date}.</p>
                            <p>You can view your submission and past reports in the WPR dashboard.</p>
                        </div>
                        """
            
            if ai_analysis:
                html_content += f"""
                        <div class="analysis">
                            <h3>AI Analysis of Your Report</h3>
                            <div style="white-space: pre-wrap; font-family: Arial, sans-serif;">
                                <div style="font-family: Arial, sans-serif; line-height: 1.6; padding: 15px;">
                                    {ai_analysis.replace('•', '&#8226;').replace('\n', '<br>')}
                                </div>
                            </div>
                        </div>
                """
            
            html_content += """
                        <div class="footer">
                            <p>Best regards,<br>IOL Inc.</p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            data = {
                'Messages': [{
                    "From": {
                        "Email": self.sender_email,
                        "Name": self.sender_name
                    },
                    "To": [{
                        "Email": to_email,
                        "Name": to_name
                    }],
                    "Subject": f"WPR Submission Confirmation - Week {week_number}, {year}",
                    "TextPart": text_content,
                    "HTMLPart": html_content
                }]
            }
            
            logging.info(f"Sending email with data: {json.dumps(data, indent=2)}")
            logging.info(f"Using API Key: {self.api_key[:4]}...")
            
            # Make direct API call
            response = requests.post(
                f"{self.base_url}/send",
                headers=self.headers,
                json=data
            )
            
            logging.info(f"Mailjet API Response Status: {response.status_code}")
            logging.info(f"Mailjet API Response: {response.text}")
            
            if response.status_code in [200, 201]:
                try:
                    response_data = response.json()
                    sent_count = len(response_data.get('Messages', []))
                    if sent_count > 0:
                        success_msg = f"✅ Email notification sent successfully to {to_email}"
                        logging.info(success_msg)
                        print(success_msg)  # Display in Streamlit
                        return True
                    else:
                        error_msg = "❌ No messages were sent despite successful API call"
                        logging.error(error_msg)
                        print(error_msg)  # Display in Streamlit
                        return False
                except Exception as e:
                    error_msg = f"❌ Error parsing response: {str(e)}"
                    logging.error(error_msg)
                    print(error_msg)  # Display in Streamlit
                    return False
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('Messages', [{}])[0].get('Errors', [{}])[0].get('ErrorMessage', 'Unknown error')
                    full_error = f"❌ Failed to send email. Status: {response.status_code}, Error: {error_msg}"
                    logging.error(full_error)
                    print(full_error)  # Display in Streamlit
                except:
                    error_msg = f"❌ Failed to send email. Status: {response.status_code}, Response: {response.text}"
                    logging.error(error_msg)
                    print(error_msg)  # Display in Streamlit
                return False
                
        except Exception as e:
            error_msg = f"❌ Error sending WPR notification email: {str(e)}"
            logging.error(error_msg)
            logging.exception("Full traceback:")
            print(error_msg)  # Display in Streamlit
            return False