# Travel Planning Application

## Overview

This is a travel planning application built with Streamlit that leverages AI agents to help users plan and book travel. The application integrates multiple external services including flight booking through Amadeus, location data via Google Places API, and AI-powered travel recommendations using CrewAI agents with Groq's LLM models. The system uses a multi-agent architecture where specialized AI agents handle different aspects of travel planning such as flight search, destination research, and itinerary creation.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Streamlit Framework**: Web-based user interface that provides an interactive dashboard for travel planning
- **Real-time Processing**: Direct user interaction with AI agents through the web interface
- **Error Handling**: Graceful degradation with user-friendly error messages and retry mechanisms

### Backend Architecture
- **Multi-Agent System**: Uses CrewAI framework to orchestrate specialized AI agents for different travel planning tasks
- **LLM Integration**: Groq's Llama 3.3 70B model for natural language processing and reasoning
- **Rate Limiting**: Built-in retry mechanisms with exponential backoff for API calls
- **JSON Processing**: Robust parsing system to extract structured data from LLM responses

### Data Processing
- **Environment Configuration**: Secure API key management through environment variables
- **Response Parsing**: Custom utilities to extract and validate JSON data from AI agent responses
- **Error Recovery**: Automatic retry logic for rate-limited API calls

### Service Integration Pattern
- **Travel APIs**: Direct integration with travel booking services for real-time data
- **Location Services**: Geographic data retrieval for destination information
- **AI Orchestration**: Coordinated multi-agent workflows for complex travel planning tasks

## External Dependencies

### AI and Language Models
- **Groq API**: Llama 3.3 70B model for natural language processing and travel recommendations
- **CrewAI**: Multi-agent AI framework for orchestrating specialized travel planning agents

### Travel Services
- **Amadeus API**: Flight search, booking, and travel data services
- **Google Places API**: Location data, points of interest, and geographic information

### Core Libraries
- **Streamlit**: Web application framework for the user interface
- **Python-dotenv**: Environment variable management for secure API key handling
- **Requests**: HTTP client for external API communication
- **Tabulate**: Data formatting and presentation utilities

### Development Tools
- **AST and JSON**: Python standard libraries for data parsing and manipulation
- **DateTime**: Standard library for date and time handling in travel planning
- **Regular Expressions**: Text processing and data extraction utilities