# core/ai_hr_analyzer.py
import logging
from typing import List, Dict, Any
import anthropic
from datetime import datetime
import time
import platform
import html
import json

# At the top of the file, after imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('hr_analysis.log')
    ]
)

class AIHRAnalyzer:
    def _safe_parse_json(self, json_str: str) -> Dict:
        """Safely parse JSON string with error handling"""
        try:
            if isinstance(json_str, dict):
                return json_str
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logging.warning(f"Failed to parse JSON: {str(e)}")
            return {}

    def _format_peer_evaluations(self, evaluations: Dict[str, Any]) -> str:
        """Format peer evaluations into a string"""
        try:
            # First try to parse if it's a JSON string
            if isinstance(evaluations, str):
                evaluations = self._safe_parse_json(evaluations)

            # Handle empty or invalid evaluations
            if not evaluations:
                return "No peer evaluations provided"

            formatted_evals = []
            for peer, eval_data in evaluations.items():
                # Handle case where eval_data might be a string or dict
                if isinstance(eval_data, str):
                    eval_data = self._safe_parse_json(eval_data) or {"Rating": eval_data}

                # Safely get rating and comments
                rating = eval_data.get('Rating', 'N/A') if isinstance(eval_data, dict) else eval_data
                comments = eval_data.get('Comments', 'None') if isinstance(eval_data, dict) else 'None'
                
                formatted_evals.append(
                    f"- {peer}: Rating {rating}, Comments: {comments}"
                )

            return "\n".join(formatted_evals) if formatted_evals else "No peer evaluations provided"
            
        except Exception as e:
            logging.error(f"Error formatting peer evaluations: {str(e)}")
            return "Error processing peer evaluations"
        
    def __init__(self, anthropic_api_key: str):
        self.client = anthropic.Client(api_key=anthropic_api_key)

    def generate_hr_analysis(self, wpr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate HR analysis using Claude AI"""
        try:
            # Validate input data
            required_fields = ['Name', 'Team', 'Week Number', 'Year']
            for field in required_fields:
                if field not in wpr_data:
                    raise ValueError(f"Missing required field: {field}")

            # Ensure all data fields are in the correct format
            wpr_data = self._sanitize_data(wpr_data)

            # Log analysis start
            logging.info(f"Starting HR analysis for {wpr_data['Name']} - Week {wpr_data['Week Number']}")
            
            # Prepare the prompt for HR analysis
            hr_analysis_prompt = self._prepare_hr_analysis_prompt(wpr_data)
            
            # Get AI response
            response = self._retry_ai_request(hr_analysis_prompt)
            
            # Validate AI response
            if not response or not response.content:
                raise ValueError("Empty response from AI service")
                
            ai_response = response.content[0].text
            
            # Validate response format
            if not ai_response or len(ai_response) < 100:
                raise ValueError("Invalid or too short AI response")
                
            ai_response = self._validate_html_response(ai_response)
            
            # Create structured analysis result
            analysis_result = {
                'performance_metrics': {
                    'productivity_score': self._parse_productivity_rating(wpr_data.get('Productivity Rating', '1')),
                    'task_completion_rate': self._calculate_task_completion_rate(wpr_data),
                    'project_progress': self._calculate_project_progress(wpr_data),
                    'collaboration_score': self._calculate_collaboration_score(wpr_data)
                },
                'skill_assessment': {
                    'technical_skills': self._extract_technical_skills(wpr_data),
                    'soft_skills': self._extract_soft_skills(wpr_data),
                    'development_areas': [],
                    'strengths': []
                },
                'wellness_indicators': {
                    'work_life_balance': 'Good',
                    'workload_assessment': self._assess_workload(wpr_data),
                    'engagement_level': self._assess_engagement(wpr_data)
                },
                'growth_recommendations': {
                    'immediate_actions': wpr_data.get('Productivity Suggestions', []),
                    'development_goals': [],
                    'training_needs': []
                },
                'team_dynamics': {
                    'collaboration_pattern': self._analyze_collaboration(wpr_data),
                    'peer_feedback_summary': self._summarize_peer_feedback(wpr_data),
                    'team_impact': ''
                },
                'risk_factors': {
                    'burnout_risk': 'Low',
                    'retention_risk': 'Low',
                    'performance_trend': 'Stable'
                },
                'completion_metrics': {
                'tasks_analyzed': len(wpr_data.get('Completed Tasks', [])) + 
                                len(wpr_data.get('Pending Tasks', [])) + 
                                len(wpr_data.get('Dropped Tasks', [])),
                'projects_analyzed': len(wpr_data.get('Projects', [])),
                'peer_evaluations_count': len(wpr_data.get('Peer_Evaluations', {})),
                'analysis_completion': 100.0  # Percentage of analysis completed
                },
                'analysis_timestamp': datetime.now().isoformat(),
                'employee_name': wpr_data.get('Name', 'Unknown'),  # Change from direct access
                'week_number': wpr_data.get('Week Number', 0),     # Change from direct access
                'year': wpr_data.get('Year', datetime.now().year), # Change from direct access
                'team': wpr_data.get('Team', 'Unknown'),           # Change from direct access
                'ai_analysis': ai_response,  # Include the AI analysis response
                'metadata': {
                    'version': '1.0',
                    'model': "claude-3-5-sonnet-20241022",
                    'analysis_timestamp': datetime.now().isoformat(),
                    'system_info': {
                        'python_version': platform.python_version(),
                        'anthropic_version': anthropic.__version__
                    }
                }
            }
            
            logging.info(f"Starting HR analysis for {wpr_data.get('Name', 'Unknown')} - Week {wpr_data.get('Week Number', 'N/A')}")
            return analysis_result

        except Exception as e:
            logging.error(f"Error generating HR analysis: {str(e)}")
            raise

    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize and validate input data"""
        try:
            sanitized = data.copy()
            
            # Ensure lists are actually lists
            list_fields = ['Completed Tasks', 'Pending Tasks', 'Dropped Tasks']
            for field in list_fields:
                if field in sanitized:
                    if isinstance(sanitized[field], str):
                        sanitized[field] = [task.strip() for task in sanitized[field].split('\n') if task.strip()]
                    elif not isinstance(sanitized[field], list):
                        sanitized[field] = []

            # Ensure Projects is properly formatted
            if 'Projects' in sanitized:
                if isinstance(sanitized['Projects'], str):
                    sanitized['Projects'] = self._parse_projects_string(sanitized['Projects'])
                elif not isinstance(sanitized['Projects'], list):
                    sanitized['Projects'] = []

            # Ensure Peer_Evaluations is a dictionary
            if 'Peer_Evaluations' in sanitized:
                if not isinstance(sanitized['Peer_Evaluations'], dict):
                    sanitized['Peer_Evaluations'] = {}

            return sanitized
        except Exception as e:
            logging.error(f"Error sanitizing data: {str(e)}")
            raise

    def _parse_projects_string(self, projects_str: str) -> List[Dict[str, Any]]:
        """Parse projects string into list of dictionaries"""
        try:
            projects = []
            lines = [line.strip() for line in projects_str.split('\n') if line.strip()]
            for line in lines:
                if ',' in line:
                    name, completion = line.split(',', 1)
                    completion = completion.strip().replace('%', '')
                    try:
                        completion = float(completion)
                    except ValueError:
                        completion = 0
                    projects.append({
                        'name': name.strip(),
                        'completion': completion
                    })
            return projects
        except Exception as e:
            logging.error(f"Error parsing projects string: {str(e)}")
            return []

    def _parse_productivity_rating(self, rating: str) -> float:
        """Parse productivity rating string to float"""
        try:
            if isinstance(rating, (int, float)):
                return float(rating)
            rating_str = rating.split()[0]
            return float(rating_str)
        except (ValueError, IndexError):
            return 1.0

    def _calculate_task_completion_rate(self, data: Dict[str, Any]) -> float:
        """Calculate task completion rate"""
        try:
            completed = len(data.get('Completed Tasks', []))
            total = (completed + 
                    len(data.get('Pending Tasks', [])) + 
                    len(data.get('Dropped Tasks', [])))
            return round((completed / total * 100) if total > 0 else 0, 2)
        except Exception as e:
            logging.error(f"Error calculating task completion rate: {str(e)}")
            return 0.0

    def _calculate_project_progress(self, data: Dict[str, Any]) -> float:
        """Calculate average project progress"""
        try:
            projects = data.get('Projects', [])
            if not projects:
                return 0.0
            total_progress = sum(p.get('completion', 0) for p in projects)
            return round(total_progress / len(projects), 2)
        except Exception as e:
            logging.error(f"Error calculating project progress: {str(e)}")
            return 0.0

    def _calculate_collaboration_score(self, data: Dict[str, Any]) -> float:
        """Calculate collaboration score based on peer evaluations"""
        try:
            peer_evals = data.get('Peer_Evaluations', {})
            if isinstance(peer_evals, str):
                peer_evals = self._safe_parse_json(peer_evals)
            if not peer_evals:
                return 3.0  # Default score
            
            scores = []
            for eval_data in peer_evals.values():
                if isinstance(eval_data, str):
                    try:
                        rating = float(eval_data.split()[0])
                        scores.append(rating)
                    except (ValueError, IndexError):
                        scores.append(3.0)
                elif isinstance(eval_data, dict):
                    try:
                        rating = float(eval_data.get('Rating', 3))
                        scores.append(rating)
                    except (ValueError, TypeError):
                        scores.append(3.0)
                else:
                    scores.append(3.0)
                    
            return round(sum(scores) / len(scores), 2) if scores else 3.0
        except Exception as e:
            logging.error(f"Error calculating collaboration score: {str(e)}")
            return 3.0

    def _extract_technical_skills(self, data: Dict[str, Any]) -> List[str]:
        """Extract technical skills from tasks and projects"""
        try:
            tasks = (
                data.get('Completed Tasks', []) + 
                data.get('Pending Tasks', [])
            )
            return list(set(task.split()[0] for task in tasks if task))
        except Exception as e:
            logging.error(f"Error extracting technical skills: {str(e)}")
            return []

    def _extract_soft_skills(self, data: Dict[str, Any]) -> List[str]:
        """Extract soft skills based on productivity details"""
        try:
            details = data.get('Productivity Details', '')
            words = details.lower().split()
            soft_skills = ['communication', 'leadership', 'teamwork', 'organization']
            return [skill for skill in soft_skills if skill in words]
        except Exception as e:
            logging.error(f"Error extracting soft skills: {str(e)}")
            return []

    def _assess_workload(self, data: Dict[str, Any]) -> str:
        """Assess workload based on tasks and productivity"""
        try:
            total_tasks = (
                len(data.get('Completed Tasks', [])) + 
                len(data.get('Pending Tasks', [])) + 
                len(data.get('Dropped Tasks', []))
            )
            if total_tasks > 10:
                return "Heavy"
            elif total_tasks > 5:
                return "Optimal"
            return "Light"
        except Exception as e:
            logging.error(f"Error assessing workload: {str(e)}")
            return "Optimal"

    def _assess_engagement(self, data: Dict[str, Any]) -> str:
        """Assess engagement level"""
        try:
            productivity_rating = float(data.get('Productivity Rating', '3').split()[0])
            if productivity_rating >= 3.5:
                return "High"
            elif productivity_rating >= 2.5:
                return "Moderate"
            return "Low"
        except Exception as e:
            logging.error(f"Error assessing engagement: {str(e)}")
            return "Moderate"

    def _analyze_collaboration(self, data: Dict[str, Any]) -> str:
        """Analyze collaboration patterns"""
        try:
            peer_evals = data.get('Peer_Evaluations', {})
            if not peer_evals:
                return "No peer evaluations provided"
            avg_rating = sum(float(ev.get('Rating', 3)) for ev in peer_evals.values()) / len(peer_evals)
            if avg_rating >= 3.5:
                return "Strong collaborator"
            elif avg_rating >= 2.5:
                return "Active team member"
            return "Needs improvement in collaboration"
        except Exception as e:
            logging.error(f"Error analyzing collaboration: {str(e)}")
            return "Unable to assess collaboration"

    def _summarize_peer_feedback(self, data: Dict[str, Any]) -> str:
        """Summarize peer feedback"""
        try:
            peer_evals = data.get('Peer_Evaluations', {})
            if not peer_evals:
                return "No peer feedback available"
            num_reviews = len(peer_evals)
            avg_rating = sum(float(ev.get('Rating', 3)) for ev in peer_evals.values()) / num_reviews
            return f"Average rating of {avg_rating:.1f} from {num_reviews} peers"
        except Exception as e:
            logging.error(f"Error summarizing peer feedback: {str(e)}")
            return "Unable to summarize peer feedback"

    def _format_list(self, items: List[str]) -> str:
        """Format a list of items into a string"""
        if not items:
            return "None"
        return "\n".join(f"- {item}" for item in items)

    def _format_projects(self, projects: List[Dict[str, Any]]) -> str:
        """Format projects into a string"""
        try:
            # If projects is a string, try to parse it into a list of dictionaries
            if isinstance(projects, str):
                # Split the string by newlines and parse each line
                project_lines = [p.strip() for p in projects.split('\n') if p.strip()]
                parsed_projects = []
                for line in project_lines:
                    if ',' in line:
                        name, completion = line.split(',', 1)
                        completion = completion.strip().replace('%', '')
                        try:
                            completion = float(completion)
                        except ValueError:
                            completion = 0
                        parsed_projects.append({
                            'name': name.strip(),
                            'completion': completion
                        })
                projects = parsed_projects

            # If projects is empty or invalid
            if not projects:
                return "No projects reported"

            # Format the projects
            return "\n".join(
                f"- {p.get('name', 'Unnamed')}: {p.get('completion', 0)}% complete" 
                for p in projects
            )
        except Exception as e:
            logging.error(f"Error formatting projects: {str(e)}")
            return "Error formatting projects"

    def _prepare_hr_analysis_prompt(self, wpr_data: Dict[str, Any]) -> str:
        """Prepare the prompt for HR analysis"""
        try:
            # Format the WPR data into a structured prompt
            prompt = f"""
            Please analyze this Weekly Productivity Report for {wpr_data.get('Name', 'Unknown')} (Team: {wpr_data.get('Team', 'Unknown')}) 
            for Week {wpr_data.get('Week Number', 'N/A')}, {wpr_data.get('Year', 'N/A')}.

            TASKS:
            Completed Tasks:
            {self._format_list(wpr_data.get('Completed Tasks', []))}

            Pending Tasks:
            {self._format_list(wpr_data.get('Pending Tasks', []))}

            Dropped Tasks:
            {self._format_list(wpr_data.get('Dropped Tasks', []))}

            PROJECTS:
            {self._format_projects(wpr_data.get('Projects', []))}

            PRODUCTIVITY:
            Rating: {wpr_data.get('Productivity Rating', 'Not specified')}
            Details: {wpr_data.get('Productivity Details', 'Not provided')}
            Most Productive Time: {wpr_data.get('Productive Time', 'Not specified')}
            Preferred Work Location: {wpr_data.get('Productive Place', 'Not specified')}

            PEER EVALUATIONS:
            {self._format_peer_evaluations(wpr_data.get('Peer_Evaluations', {}))}
            """
            
            logging.info(f"HR analysis prompt prepared for {wpr_data.get('Name', 'Unknown')}")
            return prompt

        except Exception as e:
            logging.error(f"Error preparing HR analysis prompt: {str(e)}")
            raise

    def _retry_ai_request(self, prompt: str, max_retries: int = 3, timeout: int = 30) -> Any:
        """Retry AI request with exponential backoff"""
        system_prompt = """You are an empathetic HR productivity expert and career coach for IOL Inc. 
        Your role is to analyze Weekly Productivity Reports and provide detailed, constructive feedback.

        Please ensure your analysis:
        1. Is professional yet supportive in tone
        2. Provides specific, actionable recommendations
        3. Balances praise with constructive feedback
        4. Considers both individual and team dynamics
        5. Focuses on growth and development opportunities
        6. Addresses both technical and soft skills
        7. Includes wellness and work-life balance considerations

        Format your response using the following HTML structure:
        <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2E86C1; border-bottom: 2px solid #2E86C1; padding-bottom: 10px;">Weekly Performance Analysis</h2>
            
            <div style="background-color: #EBF5FB; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <h3 style="color: #2471A3; margin-top: 0;">Achievement Highlights</h3>
                [Content]
            </div>
            
            <div style="background-color: #F4F6F7; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <h3 style="color: #2471A3; margin-top: 0;">Performance Metrics</h3>
                [Content]
            </div>
            
            <div style="background-color: #EBF5FB; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <h3 style="color: #2471A3; margin-top: 0;">Growth Opportunities</h3>
                [Content]
            </div>
            
            <div style="background-color: #F4F6F7; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <h3 style="color: #2471A3; margin-top: 0;">Action Plan</h3>
                [Content]
            </div>
            
            <div style="background-color: #EBF5FB; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <h3 style="color: #2471A3; margin-top: 0;">Team Collaboration</h3>
                [Content]
            </div>
            
            <div style="background-color: #F4F6F7; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <h3 style="color: #2471A3; margin-top: 0;">Wellness Check</h3>
                [Content]
            </div>
            
            <div style="border-top: 2px solid #2E86C1; margin-top: 20px; padding-top: 10px; font-style: italic; color: #2E86C1;">
                Generated by IOL HR Analysis System
            </div>
        </div>"""

        for attempt in range(max_retries):
            try:
                # Create a dictionary of request parameters
                request_params = {
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 4000,
                    "system": system_prompt,
                    "messages": [{
                        "role": "user",
                        "content": prompt
                    }]
                }

                # Add timeout if supported by the client
                try:
                    response = self.client.messages.create(**request_params, timeout=timeout)
                except TypeError:
                    # If timeout is not supported, fall back to default behavior
                    response = self.client.messages.create(**request_params)

                return response
                
            except Exception as e:
                if attempt == max_retries - 1:
                    logging.error(f"Failed to get AI response after {max_retries} attempts: {str(e)}")
                    raise
                logging.warning(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(2 ** attempt)

    def _validate_html_response(self, response: str) -> str:
        """Validate and clean HTML response"""
        try:
            if not response:
                return "<div>No analysis generated</div>"
            
            # Sanitize HTML content
            response = self._sanitize_html_content(response)
                
            # Ensure response has proper div wrapper
            if not response.strip().startswith('<div'):
                response = f'<div style="font-family: Arial, sans-serif;">{response}</div>'
                
            # Ensure all sections are present
            required_sections = ['Achievement Highlights', 'Performance Metrics', 
                            'Growth Opportunities', 'Action Plan', 
                            'Team Collaboration', 'Wellness Check']
                            
            for section in required_sections:
                if section not in response:
                    logging.warning(f"Missing section in AI response: {section}")
                    
            return response
        except Exception as e:
            logging.error(f"Error validating HTML response: {str(e)}")
            return "<div>Error in analysis generation</div>"
        
    def _sanitize_html_content(self, content: str) -> str:
        """Sanitize HTML content to prevent XSS"""
        try:
            # Basic HTML sanitization
            content = content.replace('<script>', '&lt;script&gt;')
            content = content.replace('</script>', '&lt;/script&gt;')
            content = content.replace('javascript:', '')
            content = content.replace('onerror=', '')
            content = content.replace('onclick=', '')
            return content
        except Exception as e:
            logging.error(f"Error sanitizing HTML content: {str(e)}")
            return ""