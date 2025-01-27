# WPR (Weekly Productivity Report) Application Architecture

## System Overview
The WPR application is a Streamlit-based web application designed to manage and analyze weekly productivity reports. It integrates with Supabase for data storage, Anthropic's Claude AI for analysis, and Mailjet for email notifications.

## System Architecture

### Core Components

1. **Frontend Layer (`ui/`)**
   - `components.py`: UI components and form elements
   - `hr_visualizations.py`: HR dashboard visualization components
   
2. **Application Layer (`./`)**
   - `main.py`: Main application entry point and business logic
   - `dashboard.py`: Analytics dashboard implementation

3. **Configuration Layer (`config/`)**
   - `constants.py`: Application-wide constants
   - `settings.py`: Environment and configuration management

4. **Core Services (`core/`)**
   - `database.py`: Database operations and queries
   - `email_handler.py`: Email notification service
   - `ai_hr_analyzer.py`: AI-powered HR analysis

5. **Utility Layer (`utils/`)**
   - `data_utils.py`: Data processing utilities
   - `ui_utils.py`: UI helper functions
   - `error_handler.py`: Centralized error handling

### Key Dependencies
- **Streamlit**: Web application framework
- **Supabase**: Database and authentication
- **Anthropic Claude**: AI analysis
- **Mailjet**: Email service
- **Pandas**: Data manipulation

## Database Architecture

### Tables

1. **wpr_data**
   ```sql
   CREATE TABLE wpr_data (
       id SERIAL PRIMARY KEY,
       name VARCHAR(255) NOT NULL,
       week_number INTEGER NOT NULL,
       year INTEGER NOT NULL,
       completed_tasks TEXT,
       pending_tasks TEXT,
       dropped_tasks TEXT,
       projects TEXT,
       productivity_rating VARCHAR(50),
       productivity_details TEXT,
       productive_time VARCHAR(50),
       productive_place VARCHAR(50),
       productivity_suggestions TEXT[],
       peer_evaluations JSONB,
       timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       UNIQUE(name, week_number, year)
   );
   ```

2. **hr_analysis**
   ```sql
   CREATE TABLE hr_analysis (
       id SERIAL PRIMARY KEY,
       wpr_id INTEGER REFERENCES wpr_data(id),
       performance_metrics JSONB,
       skill_assessment JSONB,
       growth_recommendations JSONB,
       wellness_indicators JSONB,
       risk_factors JSONB,
       timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

### Database Relationships
- One-to-One relationship between `wpr_data` and `hr_analysis`
- Each WPR entry can have one HR analysis record

### Data Flow
1. User submits weekly report → `wpr_data`
2. AI analyzes report → `hr_analysis`
3. Dashboard queries both tables for visualization

## Security Architecture

### Authentication
- Managed through Supabase authentication
- Environment variables for API keys and secrets

### Data Protection
- Sensitive data stored in environment variables
- API keys never exposed in client-side code
- Database access restricted through Supabase RLS policies

## Error Handling
- Centralized error handling through `error_handler.py`
- Consistent error logging and user feedback
- Graceful degradation for AI/email services

## Deployment Architecture
- Streamlit Cloud hosting
- Supabase managed database
- Environment-specific configurations
- Automatic SSL/TLS through Streamlit Cloud

## Future Considerations
1. **Scalability**
   - Database indexing for performance
   - Caching layer for frequent queries
   - Batch processing for AI analysis

2. **Monitoring**
   - Application metrics tracking
   - Error rate monitoring
   - Performance analytics

3. **Feature Extensions**
   - Team analytics dashboard
   - Integration with project management tools
   - Mobile-responsive design improvements
