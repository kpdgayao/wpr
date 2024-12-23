# Weekly Productivity Report (WPR) Application

A Streamlit-based dashboard application for tracking and analyzing team productivity metrics.

## Features

- Weekly productivity tracking and reporting
- Team and individual performance analytics
- Project progress visualization
- AI-powered HR analysis
- Email report generation
- Interactive CEO dashboard

## Setup

1. Create and activate a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:
```
ANTHROPIC_API_KEY=your_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
MAILJET_API_KEY=your_mailjet_key
MAILJET_SECRET_KEY=your_mailjet_secret
```

## Usage

Run the main application:
```bash
streamlit run main.py
```

Run the CEO dashboard:
```bash
streamlit run dashboard.py
```

## Project Structure

- `config/`: Configuration and constants
- `core/`: Core business logic and data handlers
- `ui/`: UI components and visualizations
- `utils/`: Utility functions and helpers

## Dependencies

See `requirements.txt` for a complete list of dependencies.
