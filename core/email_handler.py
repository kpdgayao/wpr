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

    def send_email(self, to_email: str, to_name: str, subject: str, html_content: str) -> Dict[str, Any]:
        """Send email using Mailjet"""
        try:
            logging.info(f"Preparing to send email to {to_email}")
            
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
            
            # Log email attempt
            logging.info(f"Sending email to {to_email} with subject: {subject}")
            
            # Send email with timeout
            result = self.client.send.create(data=data)
            
            # Validate response
            if result.status_code not in [200, 201]:
                raise ValueError(f"Email API returned status code: {result.status_code}")
                
            logging.info(f"Email sent successfully to {to_email}")
            return result
        except Exception as e:
            error_msg = f"Failed to send email to {to_email}: {str(e)}"
            logging.error(error_msg)
            if hasattr(e, '__dict__'):
                logging.error(f"Detailed error: {e.__dict__}")
            raise

    def format_hr_analysis_email(self, name: str, week_number: int, hr_analysis: Dict[str, Any]) -> str:
        """Format WPR email content with HR analysis"""
        try:
            # Validate hr_analysis structure
            required_fields = ['performance_metrics', 'growth_recommendations']
            for field in required_fields:
                if field not in hr_analysis:
                    raise ValueError(f"Missing required field in HR analysis: {field}")
            
            current_date = datetime.now().strftime("%B %d, %Y")
            
            # Get metrics with safe fallbacks
            performance_metrics = hr_analysis.get('performance_metrics', {})
            growth_recommendations = hr_analysis.get('growth_recommendations', {})
            
            productivity_score = performance_metrics.get('productivity_score', 'N/A')
            task_completion = performance_metrics.get('task_completion_rate', 'N/A')
            project_progress = performance_metrics.get('project_progress', 'N/A')
            
            immediate_actions = growth_recommendations.get('immediate_actions', [])
            
            email_content = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                        .header {{ color: #2E86C1; margin-bottom: 20px; }}
                        .section {{ margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 5px; }}
                        .footer {{ margin-top: 30px; color: #666; font-size: 0.9em; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>Weekly Performance Analysis</h1>
                            <h2>Week {week_number} - {current_date}</h2>
                        </div>
                        
                        <div class="section">
                            <p>Dear {name},</p>
                            <p>Here is your weekly performance analysis summary.</p>
                            
                            <h3>Performance Metrics</h3>
                            <ul>
                                <li>Productivity Score: {productivity_score}</li>
                                <li>Task Completion Rate: {task_completion}%</li>
                                <li>Project Progress: {project_progress}%</li>
                            </ul>
                            
                            <h3>Growth Recommendations</h3>
                            <ul>
                            {"".join([f"<li>{rec}</li>" for rec in immediate_actions])}
                            </ul>
                        </div>
                        
                        <div class="footer">
                            <p>Best regards,<br>IOL Inc.</p>
                        </div>
                    </div>
                </body>
            </html>
            """
            return email_content
        except Exception as e:
            logging.error(f"Error formatting email content: {str(e)}")
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
        try:
            # Extract metrics with safe fallbacks
            metrics = hr_analysis.get('performance_metrics', {})
            growth = hr_analysis.get('growth_recommendations', {})
            wellness = hr_analysis.get('wellness_indicators', {})
            
            return f"""
                <div class="section">
                    <h2 style="color: #2E86C1;">HR Analysis Summary</h2>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                        <h3 style="color: #2471A3;">Performance Metrics</h3>
                        <ul style="list-style-type: none; padding-left: 0;">
                            <li>Productivity Score: {metrics.get('productivity_score', 'N/A')}/4</li>
                            <li>Task Completion Rate: {metrics.get('task_completion_rate', 'N/A')}%</li>
                            <li>Project Progress: {metrics.get('project_progress', 'N/A')}%</li>
                            <li>Collaboration Score: {metrics.get('collaboration_score', 'N/A')}/4</li>
                        </ul>
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                        <h3 style="color: #2471A3;">Key Recommendations</h3>
                        {self._format_list(growth.get('immediate_actions', []), True)}
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                        <h3 style="color: #2471A3;">Wellness Status</h3>
                        <ul style="list-style-type: none; padding-left: 0;">
                            <li>Work-Life Balance: {wellness.get('work_life_balance', 'N/A')}</li>
                            <li>Workload: {wellness.get('workload_assessment', 'N/A')}</li>
                            <li>Engagement: {wellness.get('engagement_level', 'N/A')}</li>
                        </ul>
                    </div>
                </div>
            """
        except Exception as e:
            logging.error(f"Error formatting HR analysis section: {str(e)}")
            raise

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