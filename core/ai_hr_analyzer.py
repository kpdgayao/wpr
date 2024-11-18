# core/ai_hr_analyzer.py
import logging
from typing import List, Dict, Any
import anthropic
from datetime import datetime
import time

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

            # Log analysis start
            logging.info(f"Starting HR analysis for {wpr_data['Name']} - Week {wpr_data['Week Number']}")
            
            # Prepare the prompt for HR analysis
            hr_analysis_prompt = self._prepare_hr_analysis_prompt(wpr_data)
            
            # Get AI response
            response = self._retry_ai_request(hr_analysis_prompt)

            # Parse and structure the AI response
            ai_response = response.content[0].text
            
            # Create structured analysis result
            analysis_result = {
                'performance_metrics': {
                    'productivity_score': float(wpr_data.get('Productivity Rating', '1').split()[0]),
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
                'analysis_timestamp': datetime.now().isoformat(),
                'employee_name': wpr_data['Name'],
                'week_number': wpr_data['Week Number'],
                'year': wpr_data['Year'],
                'team': wpr_data['Team']
            }

            logging.info(f"HR analysis completed successfully for {wpr_data['Name']}")
            return analysis_result

        except Exception as e:
            logging.error(f"Error generating HR analysis: {str(e)}")
            raise

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
            if not peer_evals:
                return 3.0  # Default score
            scores = [float(ev.get('Rating', 3)) for ev in peer_evals.values()]
            return round(sum(scores) / len(scores), 2)
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
        
    def _prepare_hr_analysis_prompt(self, wpr_data: Dict[str, Any]) -> str:
        """Prepare the prompt for HR analysis"""
        try:
            # Format the WPR data into a structured prompt
            prompt = f"""
            Please analyze this Weekly Productivity Report for {wpr_data['Name']} (Team: {wpr_data['Team']}) 
            for Week {wpr_data['Week Number']}, {wpr_data['Year']}.

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

            Please provide a comprehensive HR analysis including:
            1. Performance assessment
            2. Productivity trends
            3. Team collaboration evaluation
            4. Growth opportunities
            5. Risk factors
            6. Recommendations for improvement
            7. Wellness indicators
            8. Skill development needs
            """
            
            logging.info(f"HR analysis prompt prepared for {wpr_data['Name']}")
            return prompt

        except Exception as e:
            logging.error(f"Error preparing HR analysis prompt: {str(e)}")
            raise

    def _format_list(self, items: List[str]) -> str:
        """Format a list of items into a string"""
        if not items:
            return "None"
        return "\n".join(f"- {item}" for item in items)

    def _format_projects(self, projects: List[Dict[str, Any]]) -> str:
        """Format projects into a string"""
        if not projects:
            return "No projects reported"
        return "\n".join(f"- {p.get('name', 'Unnamed')}: {p.get('completion', 0)}% complete" 
                        for p in projects)

    def _format_peer_evaluations(self, evaluations: Dict[str, Any]) -> str:
        """Format peer evaluations into a string"""
        if not evaluations:
            return "No peer evaluations provided"
        return "\n".join(
            f"- {peer}: Rating {eval_data.get('Rating', 'N/A')}, "
            f"Comments: {eval_data.get('Comments', 'None')}"
            for peer, eval_data in evaluations.items()
        )

    def _retry_ai_request(self, prompt: str, max_retries: int = 3) -> Any:
        """Retry AI request with exponential backoff"""
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=4000,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                return response
            except Exception as e:
                if attempt == max_retries - 1:
                    logging.error(f"Failed to get AI response after {max_retries} attempts: {str(e)}")
                    raise
                logging.warning(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff