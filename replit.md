# AI Travel Agent

## Overview

This is a Streamlit-based AI Travel Agent application that helps users plan trips using multiple AI agents and third-party APIs. The system leverages CrewAI for multi-agent orchestration, Groq's LLM for AI capabilities, and integrates with Amadeus for flight data and Google Places for location information. The application provides an interactive web interface for users to input travel preferences and receive comprehensive travel plans.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit for rapid web application development
- **Interface**: Single-page application with interactive forms and real-time responses
- **User Experience**: Direct input forms for travel preferences with immediate AI-generated results

### Backend Architecture
- **AI Framework**: CrewAI for multi-agent system coordination
- **LLM Integration**: Groq's Llama-3.1-8b-instant model for natural language processing
- **Agent Pattern**: Multiple specialized AI agents working collaboratively on travel planning tasks
- **Error Handling**: Retry mechanism for rate-limited API calls with exponential backoff

### Data Processing
- **Response Parsing**: JSON extraction from LLM responses with fallback parsing
- **Data Formatting**: Tabulate library for structured data presentation
- **Configuration**: Environment variable-based configuration for API credentials

### Deployment Strategy
- **Primary Target**: Cloud platforms supporting long-running Python servers (DigitalOcean App Platform, AWS EC2)
- **Infrastructure**: Containerized deployment with environment variable injection
- **Scalability**: Single-instance deployment suitable for moderate traffic

## External Dependencies

### AI Services
- **Groq API**: Primary LLM provider using Llama-3.1-8b-instant model for natural language processing
- **CrewAI**: Multi-agent framework for coordinating specialized AI agents

### Travel APIs
- **Amadeus API**: Flight search, pricing, and booking data integration
- **Google Places API**: Location data, points of interest, and geographical information

### Infrastructure Services
- **DigitalOcean App Platform**: Recommended deployment platform for production hosting
- **AWS EC2**: Alternative deployment option with manual server management

### Development Dependencies
- **Streamlit**: Web application framework for Python
- **Python-dotenv**: Environment variable management
- **Requests**: HTTP client for API communications
- **Tabulate**: Data formatting and presentation library