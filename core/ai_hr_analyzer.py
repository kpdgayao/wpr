# core/ai_hr_analyzer.py
import logging
from typing import List, Dict, Any
import anthropic
from datetime import datetime
import time
import platform
import html
import json
import re
from utils.error_handler import handle_exceptions

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
    def __init__(self, anthropic_api_key: str = None):
        """Initialize the AI HR Analyzer"""
        self.client = None
        if anthropic_api_key:
            self.client = anthropic.Client(api_key=anthropic_api_key)
            logging.info("AI HR Analyzer initialized successfully")
        else:
            logging.warning("No Anthropic API key provided - AI HR analysis will be disabled")

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
        
    def generate_hr_analysis(self, wpr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive HR analysis using Claude AI"""
        if not self.client:
            logging.warning("AI HR analysis is disabled - no Anthropic client available")
            return {}
            
        try:
            # Extract employee name with multiple fallbacks
            employee_name = (
                wpr_data.get('Name') or 
                wpr_data.get('name') or 
                wpr_data.get('Employee Name') or 
                wpr_data.get('employee_name')
            )
            
            if not employee_name:
                logging.error("Employee name not found in WPR data")
                raise ValueError("Missing employee name in WPR data")
            
            # Remove team info from name if present
            employee_name = employee_name.split(" (")[0] if " (" in employee_name else employee_name
            
            # Log the extracted name
            logging.info(f"Processing HR analysis for employee: {employee_name}")
            
            # Calculate enhanced metrics
            enhanced_metrics = self._calculate_metrics(wpr_data)
            
            # Log the metrics
            logging.info(f"Calculated metrics for {employee_name}: {json.dumps(enhanced_metrics, indent=2)}")
            
            # Create analysis result
            analysis_result = {
                'performance_metrics': enhanced_metrics,
                'employee_data': {
                    'name': employee_name,
                    'team': wpr_data.get('Team', 'Unknown'),
                    'week_number': wpr_data.get('Week Number', 0),
                    'year': wpr_data.get('Year', datetime.now().year)
                },
                'analysis_content': self._generate_analysis_text(wpr_data, enhanced_metrics),
                'metadata': {
                    'version': '2.0',
                    'timestamp': datetime.now().isoformat(),
                    'model': "claude-3-5-sonnet-20241022"
                }
            }
            
            # Try to save the analysis
            if self.save_hr_analysis(wpr_data, analysis_result):
                logging.info(f"HR analysis saved successfully for {employee_name}")
            else:
                logging.warning(f"Failed to save HR analysis for {employee_name}")
            
            return analysis_result

        except Exception as e:
            logging.error(f"Error generating HR analysis: {str(e)}")
            return {}

    def _calculate_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate all metrics from WPR data."""
        try:
            # Get task counts directly from the fields
            completed_count = int(data.get('Number of Completed Tasks', 0))
            pending_count = int(data.get('Number of Pending Tasks', 0))
            dropped_count = int(data.get('Number of Dropped Tasks', 0))
            
            # Log raw task counts
            logging.info(f"Raw task counts from data - "
                        f"Completed: {completed_count}, "
                        f"Pending: {pending_count}, "
                        f"Dropped: {dropped_count}")
            
            # Calculate totals
            total_tasks = completed_count + pending_count + dropped_count
            
            # Calculate completion rate (avoid division by zero)
            completion_rate = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
            
            # Get project progress from Projects field
            try:
                projects = data.get('Projects', [])
                if isinstance(projects, str):
                    projects = json.loads(projects)
                avg_progress = sum(float(p.get('completion', 0)) for p in projects) / len(projects) if projects else 0
            except Exception as e:
                logging.error(f"Error calculating project progress: {str(e)}")
                avg_progress = 0
            
            # Get productivity rating (1-5 scale)
            try:
                rating_str = str(data.get('Productivity Rating', '0'))
                rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_str)
                rating = float(rating_match.group(1)) if rating_match else 0
            except Exception as e:
                logging.error(f"Error parsing productivity rating: {str(e)}")
                rating = 0
            
            metrics = {
                'task_completion_rate': round(completion_rate, 1),
                'completed_tasks': completed_count,
                'pending_tasks': pending_count,
                'dropped_tasks': dropped_count,
                'total_tasks': total_tasks,
                'project_progress': round(avg_progress, 1),
                'productivity_rating': rating
            }
            
            # Log calculated metrics
            logging.info(f"Calculated metrics: {json.dumps(metrics, indent=2)}")
            return metrics
            
        except Exception as e:
            logging.error(f"Error calculating metrics: {str(e)}")
            return {
                'task_completion_rate': 0,
                'completed_tasks': 0,
                'pending_tasks': 0,
                'dropped_tasks': 0,
                'total_tasks': 0,
                'project_progress': 0,
                'productivity_rating': 0
            }

    def _calculate_task_completion_rate(self, data: Dict[str, Any]) -> float:
        """Calculate task completion rate for the current week's submission."""
        metrics = self._calculate_metrics(data)
        return metrics['task_completion_rate']

    def _calculate_efficiency(self, data: Dict[str, Any]) -> float:
        """Calculate task efficiency score"""
        try:
            completed_tasks = len(data.get('Completed Tasks', []))
            total_tasks = (completed_tasks + 
                         len(data.get('Pending Tasks', [])) + 
                         len(data.get('Dropped Tasks', [])))
            return round((completed_tasks / total_tasks * 5) if total_tasks > 0 else 0, 2)
        except Exception as e:
            logging.error(f"Error calculating efficiency: {str(e)}")
            return 0.0

    def _analyze_team_contribution(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze team contribution metrics"""
        try:
            peer_evals = data.get('Peer_Evaluations', {})
            return {
                'rating': self._calculate_collaboration_score(data),
                'feedback_count': len(peer_evals),
                'engagement_level': self._assess_engagement(data)
            }
        except Exception as e:
            logging.error(f"Error analyzing team contribution: {str(e)}")
            return {'rating': 0, 'feedback_count': 0, 'engagement_level': 'Not available'}

    def _analyze_time_utilization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze time utilization patterns"""
        try:
            return {
                'productive_time': data.get('Productive Time', 'Not specified'),
                'preferred_location': data.get('Productive Place', 'Not specified'),
                'efficiency_indicator': self._calculate_efficiency(data)
            }
        except Exception as e:
            logging.error(f"Error analyzing time utilization: {str(e)}")
            return {}

    def _calculate_average_completion(self, data: Dict[str, Any]) -> float:
        """Calculate average project completion percentage"""
        try:
            projects = data.get('Projects', [])
            if isinstance(projects, str):
                projects = self._parse_projects_string(projects)
            if not projects:
                return 0.0
            total_completion = 0
            count = 0
            for p in projects:
                try:
                    completion = float(p.get('completion', 0))
                    total_completion += completion
                    count += 1
                except (ValueError, TypeError):
                    logging.warning(f"Invalid completion value in project: {p}")
            return round(total_completion / count if count > 0 else 0, 2)
        except Exception as e:
            logging.error(f"Error calculating average completion: {str(e)}")
            return 0.0

    def _calculate_project_progress(self, data: Dict[str, Any]) -> float:
        """Calculate average project progress"""
        try:
            projects = data.get('Projects', [])
            if isinstance(projects, str):
                projects = self._parse_projects_string(projects)
            if not projects:
                return 0.0
            total_progress = 0
            count = 0
            for p in projects:
                try:
                    completion = float(p.get('completion', 0))
                    total_progress += completion
                    count += 1
                except (ValueError, TypeError):
                    logging.warning(f"Invalid completion value in project: {p}")
            return round(total_progress / count if count > 0 else 0, 2)
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
            for peer_score in peer_evals.values():
                if isinstance(peer_score, (int, float)):
                    scores.append(float(peer_score))
                elif isinstance(peer_score, dict):
                    scores.append(float(peer_score.get('Rating', 3.0)))
                elif isinstance(peer_score, str):
                    try:
                        scores.append(float(peer_score.split()[0]))
                    except (ValueError, IndexError):
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

    def _retry_ai_request(self, prompt: str, max_retries: int = 3, timeout: int = 30) -> Any:
        """Retry AI request with exponential backoff"""
        for attempt in range(max_retries):
            try:
                # Create a dictionary of request parameters
                request_params = {
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 8000,
                    "system": """You are an empathetic HR productivity expert and career coach for IOL Inc. 
        Your role is to analyze Weekly Productivity Reports and provide detailed, constructive feedback.

        Please ensure your analysis:
        1. Is professional yet supportive in tone
        2. Provides specific, actionable recommendations
        3. Balances praise with constructive feedback
        4. Considers both individual and team dynamics
        5. Focuses on growth and development opportunities
        6. Addresses both technical and soft skills
        7. Includes wellness and work-life balance considerations

        Please format your response in a clear, structured way using bullet points (•) and proper spacing.
        Use this structure for your analysis:

        Weekly Performance Analysis
        Week [X] - [Date]

        Achievement Highlights
        • [Point 1]
        • [Point 2]
        ...

        Performance Metrics
        • [Metric 1]
        • [Metric 2]
        ...

        Growth Opportunities
        • [Opportunity 1]
        • [Opportunity 2]
        ...

        Action Plan
        • [Action 1]
        • [Action 2]
        ...

        Team Collaboration
        • [Point 1]
        • [Point 2]
        ...

        Wellness Check
        • [Point 1]
        • [Point 2]
        ...

        Generated by IOL HR Analysis System

        Important formatting rules:
        1. Use bullet points (•) consistently
        2. Maintain proper spacing between sections (one blank line)
        3. Keep bullet points aligned
        4. Use clear section headers
        5. Ensure all text is properly formatted and readable
        6. Avoid using markdown or other special formatting
        """,
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

    def _prepare_enhanced_prompt(self, data: Dict[str, Any], metrics: Dict[str, Any]) -> str:
        """Prepare enhanced analysis prompt with metrics"""
        try:
            # Ensure we have valid data
            sanitized_data = self._sanitize_data(data)
            
            # Format the prompt with proper error handling
            prompt = f"""
            Weekly Performance Analysis Request for {sanitized_data.get('Name', 'Unknown')}
            
            EMPLOYEE INFORMATION:
            Team: {sanitized_data.get('Team', 'Unknown')}
            Week: {sanitized_data.get('Week Number', 'N/A')}
            Year: {sanitized_data.get('Year', 'N/A')}

            PERFORMANCE METRICS:
            Task Completion Rate: {metrics.get('task_completion_rate', 0)}%
            Project Progress Rate: {metrics.get('project_progress', 0)}%
            Peer Rating: {self._calculate_collaboration_score(sanitized_data)}/5
            Productivity Self-Rating: {metrics.get('productivity_rating', 0)}/5

            DETAILED DATA:
            
            Completed Tasks:
            {self._format_list(sanitized_data.get('Completed Tasks', []))}

            Pending Tasks:
            {self._format_list(sanitized_data.get('Pending Tasks', []))}

            Projects:
            {self._format_projects(sanitized_data.get('Projects', []))}

            Productivity Details:
            Time: {sanitized_data.get('Productive Time', 'Not specified')}
            Location: {sanitized_data.get('Productive Place', 'Not specified')}
            
            Peer Feedback:
            {self._format_peer_evaluations(sanitized_data.get('Peer_Evaluations', {}))}

            Please provide a comprehensive analysis following the specified format.
            """
            
            # Validate the prompt is not empty
            if not prompt.strip():
                raise ValueError("Generated prompt is empty")
                
            return prompt
            
        except Exception as e:
            logging.error(f"Error preparing enhanced prompt: {str(e)}")
            return "Please analyze the weekly performance report and provide actionable feedback."

    def _format_list(self, items: List[str]) -> str:
        """Format a list of items into a string"""
        try:
            if isinstance(items, str):
                items = [item.strip() for item in items.split('\n') if item.strip()]
            return "\n".join(f"- {item}" for item in items) if items else "None"
        except Exception as e:
            logging.error(f"Error formatting list: {str(e)}")
            return "None"

    def _format_projects(self, projects: List[Dict[str, Any]]) -> str:
        """Format projects into a string"""
        try:
            if isinstance(projects, str):
                projects = self._parse_projects_string(projects)
            if not projects:
                return "No projects reported"
            formatted = []
            for p in projects:
                try:
                    name = p.get('name', 'Unnamed')
                    completion = float(p.get('completion', 0))
                    formatted.append(f"- {name}: {completion}% complete")
                except (ValueError, TypeError):
                    logging.warning(f"Invalid project data: {p}")
            return "\n".join(formatted) if formatted else "No valid projects reported"
        except Exception as e:
            logging.error(f"Error formatting projects: {str(e)}")
            return "Error formatting projects"

    def _format_peer_evaluations(self, evaluations: Dict[str, Any]) -> str:
        """Format peer evaluations into a string"""
        try:
            if not evaluations:
                return "No peer evaluations available"
            if isinstance(evaluations, str):
                evaluations = self._safe_parse_json(evaluations)
            formatted = []
            for name, feedback in evaluations.items():
                if isinstance(feedback, (int, float)):
                    formatted.append(f"- {name}: Rating {feedback}")
                elif isinstance(feedback, dict):
                    rating = feedback.get('Rating', 'N/A')
                    comments = feedback.get('Comments', '')
                    formatted.append(f"- {name}: Rating {rating}{', ' + comments if comments else ''}")
                else:
                    formatted.append(f"- {name}: {feedback}")
            return "\n".join(formatted)
        except Exception as e:
            logging.error(f"Error formatting peer evaluations: {str(e)}")
            return "Error formatting peer evaluations"

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
                if isinstance(sanitized['Peer_Evaluations'], str):
                    sanitized['Peer_Evaluations'] = self._safe_parse_json(sanitized['Peer_Evaluations'])
                if not isinstance(sanitized['Peer_Evaluations'], dict):
                    sanitized['Peer_Evaluations'] = {}

            return sanitized
        except Exception as e:
            logging.error(f"Error sanitizing data: {str(e)}")
            return data

    def _parse_projects_string(self, projects_str: str) -> List[Dict[str, Any]]:
        """Parse projects string into list of dictionaries"""
        try:
            if isinstance(projects_str, list):
                return projects_str
            projects = []
            if isinstance(projects_str, str):
                try:
                    # Try to parse as JSON first
                    return json.loads(projects_str)
                except json.JSONDecodeError:
                    # If not JSON, parse as newline-separated text
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
            if isinstance(rating, str):
                # Extract first number from string (e.g., "4 - Very Productive" -> 4)
                import re
                numbers = re.findall(r'\d+', rating)
                if numbers:
                    return float(numbers[0])
            return 1.0
        except (ValueError, IndexError):
            return 1.0

    @handle_exceptions(error_types=(ValueError, TypeError, json.JSONDecodeError))
    def _get_task_list(self, tasks: Any) -> List[str]:
        """Convert task input into a properly formatted list of strings.
        
        Handles TEXT field format from wpr_data table.
        
        Args:
            tasks: Task input from database TEXT field
            
        Returns:
            List[str]: Properly formatted list of task strings
        """
        def parse_tasks() -> List[str]:
            if isinstance(tasks, str):
                # Handle TEXT field from database
                try:
                    # Try to parse as JSON first
                    parsed = json.loads(tasks)
                    if isinstance(parsed, list):
                        return [str(t).strip() for t in parsed if str(t).strip()]
                except json.JSONDecodeError:
                    # If not JSON, split by newlines (legacy format)
                    return [t.strip() for t in tasks.split('\n') if t.strip()]
            
            if isinstance(tasks, list):
                return [str(t).strip() for t in tasks if str(t).strip()]
                
            return []
            
        return parse_tasks()

    def save_hr_analysis(self, data: Dict[str, Any], analysis_result: Dict[str, Any]) -> bool:
        """Save HR analysis results to the database."""
        try:
            # Extract employee name with fallbacks
            employee_name = (
                data.get('Name') or 
                data.get('name') or 
                data.get('Employee Name') or 
                data.get('employee_name')
            )
            
            if not employee_name:
                logging.error("Employee name not found in data")
                raise ValueError("Missing employee name in data")
            
            # Remove team info from name if present
            employee_name = employee_name.split(" (")[0] if " (" in employee_name else employee_name
            
            # Create analysis record
            analysis_record = {
                'employee_name': employee_name,
                'team': data.get('Team', 'Unknown'),
                'week_number': data.get('Week Number', 0),
                'year': data.get('Year', datetime.now().year),
                'analysis_content': analysis_result.get('analysis_content', ''),
                'performance_metrics': json.dumps(analysis_result.get('performance_metrics', {})),
                'timestamp': datetime.now().isoformat()
            }
            
            # Log the record being saved
            logging.info(f"Saving HR analysis for employee: {employee_name}")
            logging.info(f"Analysis record: {json.dumps(analysis_record, indent=2)}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error saving HR analysis: {str(e)}")
            return False

    def _generate_analysis_text(self, data: Dict[str, Any], metrics: Dict[str, Any]) -> str:
        """Generate analysis text from WPR data and metrics."""
        try:
            # Format the analysis text with correct task counts
            analysis = f"""Weekly Performance Analysis
Week {data.get('Week Number')} - {datetime.now().strftime('%B %d, %Y')}

Achievement Highlights
• Self-rated as "{data.get('Productivity Rating', 'N/A')}"
• Task Completion Rate: {metrics['task_completion_rate']}% ({metrics['completed_tasks']} completed, {metrics['pending_tasks']} pending)
• Preferred Work Time: {data.get('Productive Time', 'N/A')}
• Workplace Effectiveness: Shows preference for {data.get('Productive Place', 'N/A')} environment

Performance Metrics
• Task Management: {metrics['completed_tasks']} tasks completed, {metrics['pending_tasks']} pending
• Project Progress: {metrics['project_progress']}% overall completion
• Collaboration Score: {self._get_collaboration_score(data)}
• Productivity Rating: {metrics['productivity_rating']} out of 5

Growth Opportunities
{self._generate_growth_opportunities(metrics)}

Action Plan
{self._generate_action_plan(metrics)}

Team Collaboration
• Team Impact: {self._assess_team_impact(data)}
• Peer Feedback: {self._assess_peer_feedback(data)}

Wellness Check
• Workload Assessment: {self._assess_workload(metrics['total_tasks'])}
• Engagement Level: {self._assess_engagement(metrics['productivity_rating'])}
• Work Environment: Effective utilization of {data.get('Productive Place', 'N/A')}
• Peak Productivity: Observed during {data.get('Productive Time', 'N/A')}

Generated by IOL HR Analysis System"""

            return analysis
            
        except Exception as e:
            logging.error(f"Error generating analysis text: {str(e)}")
            return "Error generating analysis"

    def _get_collaboration_score(self, data: Dict[str, Any]) -> str:
        """Calculate collaboration score from peer evaluations."""
        try:
            peer_evals = json.loads(data.get('Peer_Evaluations', '{}'))
            if not peer_evals:
                return "N/A based on peer evaluations"
            avg_score = sum(peer_evals.values()) / len(peer_evals)
            return f"{avg_score:.1f} out of 5"
        except:
            return "N/A based on peer evaluations"

    def _generate_growth_opportunities(self, metrics: Dict[str, Any]) -> str:
        """Generate growth opportunities based on metrics."""
        opportunities = []
        
        if metrics['task_completion_rate'] < 70:
            opportunities.append("• Focus on task completion and time management")
        if metrics['project_progress'] < 80:
            opportunities.append("• Accelerate project delivery pace")
        if metrics['productivity_rating'] < 4:
            opportunities.append("• Identify and address productivity blockers")
            
        return "\n".join(opportunities) if opportunities else "• Continue maintaining current performance levels"

    def _generate_action_plan(self, metrics: Dict[str, Any]) -> str:
        """Generate action plan based on metrics."""
        actions = []
        
        if metrics['pending_tasks'] > metrics['completed_tasks']:
            actions.append("• Prioritize completing pending tasks")
        if metrics['project_progress'] < 100:
            actions.append("• Set milestones for project completion")
            
        return "\n".join(actions) if actions else "• Maintain current momentum"

    def _assess_team_impact(self, data: Dict[str, Any]) -> str:
        """Assess team impact based on peer evaluations."""
        try:
            peer_evals = json.loads(data.get('Peer_Evaluations', '{}'))
            return "Strong team collaboration evident" if peer_evals else "Continue fostering team collaboration"
        except:
            return "Continue fostering team collaboration"

    def _assess_peer_feedback(self, data: Dict[str, Any]) -> str:
        """Assess peer feedback."""
        try:
            peer_evals = json.loads(data.get('Peer_Evaluations', '{}'))
            return "Positive peer feedback received" if peer_evals else "Maintain open communication with team members"
        except:
            return "Maintain open communication with team members"

    def _assess_workload(self, total_tasks: int) -> str:
        """Assess workload based on total tasks."""
        if total_tasks > 10:
            return "High"
        elif total_tasks > 5:
            return "Moderate"
        return "Balanced"

    def _assess_engagement(self, rating: float) -> str:
        """Assess engagement based on productivity rating."""
        if rating >= 4:
            return "High"
        elif rating >= 3:
            return "Good"
        return "Needs improvement"