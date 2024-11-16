# core/email_handler.py
import logging
from mailjet_rest import Client
from typing import Dict, Any, List
from datetime import datetime

class EmailHandler:
    def __init__(self, api_key: str, api_secret: str):
        """Initialize Mailjet client"""
        try:
            self.client = Client(auth=(api_key, api_secret), version='v3.1')
            self.sender_email = "go@iol.ph"
            self.sender_name = "IOL Inc."
            logging.info("Email handler initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize email handler: {str(e)}")
            raise

    def send_email(self, to_email: str, to_name: str, subject: str, 
                  html_content: str) -> Dict[str, Any]:
        """Send email using Mailjet"""
        try:
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
                    "Subject": subject,
                    "HTMLPart": html_content
                }]
            }
            
            result = self.client.send.create(data=data)
            logging.info(f"Email sent successfully to {to_email}")
            return result
        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            raise

    def format_wpr_email(self, name: str, week_number: int, 
                        ai_analysis: str, hr_analysis: Dict[str, Any] = None) -> str:
        """Format WPR email content with optional HR analysis"""
        current_date = datetime.now().strftime("%B %d, %Y")
        
        email_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                    .header {{ color: #2E86C1; margin-bottom: 20px; }}
                    .content {{ margin: 20px 0; }}
                    .footer {{ margin-top: 30px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Weekly Productivity Report Summary</h1>
                        <h2>Week {week_number}</h2>
                        <p>Date: {current_date}</p>
                    </div>
                    
                    <div class="content">
                        <p>Dear {name},</p>
                        {ai_analysis}
                    </div>
        """
        
        # Add HR analysis if available
        if hr_analysis:
            email_content += self._format_hr_analysis_section(hr_analysis)
        
        email_content += """
                    <div class="footer">
                        <p>Best regards,<br>IOL Inc.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return email_content

    def _format_hr_analysis_section(self, hr_analysis: Dict[str, Any]) -> str:
        """Format HR analysis section for email"""
        return f"""
            <div class="section">
                <h2 style="color: #2E86C1;">HR Analysis Summary</h2>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <h3 style="color: #2471A3;">Performance Metrics</h3>
                    <ul style="list-style-type: none; padding-left: 0;">
                        <li>Productivity Score: {hr_analysis['performance_metrics']['productivity_score']}/4</li>
                        <li>Task Completion Rate: {hr_analysis['performance_metrics']['task_completion_rate']}%</li>
                        <li>Project Progress: {hr_analysis['performance_metrics']['project_progress']}%</li>
                        <li>Collaboration Score: {hr_analysis['performance_metrics']['collaboration_score']}/4</li>
                    </ul>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <h3 style="color: #2471A3;">Key Recommendations</h3>
                    {self._format_list(hr_analysis['growth_recommendations']['immediate_actions'], True)}
                </div>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <h3 style="color: #2471A3;">Wellness Status</h3>
                    <ul style="list-style-type: none; padding-left: 0;">
                        <li>Work-Life Balance: {hr_analysis['wellness_indicators']['work_life_balance']}</li>
                        <li>Workload: {hr_analysis['wellness_indicators']['workload_assessment']}</li>
                        <li>Engagement: {hr_analysis['wellness_indicators']['engagement_level']}</li>
                    </ul>
                </div>
            </div>
        """

    def _format_list(self, items: List[str], as_recommendations: bool = False) -> str:
        """Format list items for email"""
        if not items:
            return "<p>None</p>"
        
        if as_recommendations:
            return "".join([
                f'<div style="padding: 10px; background-color: #E8F6F3; '
                f'border-radius: 5px; margin: 5px 0;">• {item}</div>' 
                for item in items
            ])
        
        return "<ul>" + "".join([f"<li>{item}</li>" for item in items]) + "</ul>"