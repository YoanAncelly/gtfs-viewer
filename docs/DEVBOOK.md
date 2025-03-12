# GTFS-RT Viewer Development Book

This document serves as a development journal and reference for developers and AI agents working on the GTFS-RT Viewer project. It tracks progress, decisions, and provides guidelines for contributing to the project.

## Project Overview

GTFS-RT Viewer is a tool for processing, analyzing, and visualizing General Transit Feed Specification - Real Time (GTFS-RT) data. The application reads protobuf (.pb) files containing trip updates, vehicle positions, and alerts, providing insights through data processing and visualization.

## Project Structure

The GTFS-RT Viewer project follows this directory structure:

```bash
gtfs-viewer/
├── app/                      # Application code
│   ├── __init__.py           # Package initializer
│   ├── api/                  # API endpoints
│   │   ├── __init__.py
│   │   ├── config_routes.py  # Configuration API routes
│   │   └── data_routes.py    # Data API routes
│   ├── core/                 # Core functionality
│   │   ├── __init__.py
│   │   ├── gtfs_rt_reader.py # GTFS-RT processing
│   │   └── visualizations.py # Data visualization functions
│   ├── utils/                # Utility functions
│   │   ├── __init__.py
│   │   └── config_manager.py # Configuration management
│   └── web/                  # Web interface
│       ├── __init__.py
│       └── routes.py         # Web routes
├── config/                   # Configuration files
│   └── config.json           # Main config file
├── data/                     # Data files
│   ├── gtfs/                 # GTFS static data
│   │   ├── agency.csv
│   │   ├── routes.csv
│   │   └── ...
│   └── gtfs_rt/              # GTFS-RT files
│       ├── TripUpdate.pb
│       ├── VehiclePosition.pb
│       └── Alert.pb
├── docs/                     # Documentation
│   ├── DEVBOOK.md            # Development guide
│   └── ROADMAP.md            # Project roadmap
├── output/                   # Generated files
│   ├── csv/                  # CSV exports
│   │   ├── trip_updates.csv
│   │   └── vehicle_positions.csv
│   └── charts/               # Generated charts
│       ├── delay_distribution.png
│       └── vehicle_positions.png
├── static/                   # Static web assets
│   ├── css/                  # CSS styles
│   │   └── styles.css
│   ├── js/                   # JavaScript files
│   │   ├── config.js         # Configuration UI
│   │   └── main.js           # Main UI code
│   └── img/                  # Static images
├── templates/                # HTML templates
│   ├── index.html            # Main UI template
│   └── config.html           # Config UI template
├── tests/                    # Test files
│   ├── __init__.py
│   ├── test_gtfs_rt_reader.py
│   └── test_api.py
├── .gitignore                # Git ignore file
├── README.md                 # Project overview
├── requirements.txt          # Python dependencies
└── main.py                   # Application entry point
```

This structure organizes the codebase by functionality, separating core data processing from web presentation, and keeping configuration and data files in their dedicated directories.

## Organisation des Fichiers

Les fichiers du projet suivent ces conventions d'organisation :

### Fichiers de données

- **Fichiers GTFS statiques (.csv)** : `data/gtfs/`
  - agency.csv, routes.csv, stops.csv, etc.
  
- **Fichiers GTFS-RT (.pb)** : `data/gtfs_rt/`
  - TripUpdate.pb, VehiclePosition.pb, Alert.pb

### Fichiers générés

- **Exports CSV** : `output/csv/`
  - trip_updates.csv, vehicle_positions.csv
  
- **Graphiques et visualisations** : `output/charts/`
  - delay_distribution.png, vehicle_positions.png

### Fichiers temporaires

- **Fichiers de travail temporaires** : `temp/`
  - Tous les fichiers .new (sauvegardes automatiques)
  - Fichiers intermédiaires qui ne sont pas versionnés

### Configuration

- **Fichiers de configuration** : `config/`
  - config.json : paramètres principaux de l'application

## Development Guidelines

### Code Style

- Follow PEP 8 guidelines for Python code
- Use meaningful variable and function names
- Include docstrings for all functions, classes, and modules
- Maintain a consistent indentation style (4 spaces)
- Keep functions focused and under 50 lines when possible

### Git Workflow

- Use feature branches for all new features and bug fixes
- Branch naming convention: `feature/feature-name` or `bugfix/issue-description`
- Create descriptive commit messages that explain the "why" not just the "what"
- Squash commits before merging to maintain a clean history
- Perform code reviews for all pull requests

### Testing

- Write unit tests for all new functionality
- Maintain test coverage above 80%
- Run tests locally before committing
- Ensure tests are fast and deterministic

### Project Documentation

- Update README.md for user-facing changes
- Document API changes in code and in separate documentation
- Keep this DEVBOOK.md updated with design decisions and progress
- Include examples for new features

## Development Log

### 2025-03-12

- Created ROADMAP.md and DEVBOOK.md in the docs directory
- Established initial project structure and documentation
- Defined short, mid, and long-term goals in the roadmap

### Previous Progress

- Implemented basic GTFS-RT file reading functionality
- Added analysis for trip updates, vehicle positions, and alerts
- Created CSV export capability
- Implemented basic data visualization with matplotlib

## Current Sprint (2025-Q1)

### In Progress

- Documentation expansion
- Planning for web-based dashboard implementation
- Researching interactive mapping libraries

### Backlog

- Optimize data loading for large files
- Implement caching for repeated analyses
- Add direct feed URL support

## AI Agent Activities

### Guidelines for AI Agents

- Make incremental, focused changes with clear explanations
- Document design decisions and reasoning
- Follow the established code style and patterns
- Update this development book when making significant changes
- Log your activity in the Development Log section

### AI Agent Log

#### 2025-03-12

- Created initial project documentation structure
- Set up ROADMAP.md with prioritized improvements
- Established DEVBOOK.md for development tracking

## Architecture

### Current Components

- `gtfs_rt_reader.py`: Core functionality for reading and processing GTFS-RT data
- `app.py`: Application logic and orchestration
- Data processing and visualization functions

### Planned Components

- Web server for dashboard interface
- Database integration for historical data
- API layer for external integrations
- Interactive mapping module

## Known Issues & Challenges

- Performance with very large GTFS-RT files
- Handling of complex schedule relationships
- Visualization limitations with basic matplotlib

## Resources

### Reference Documentation

- [GTFS-RT Reference](https://developers.google.com/transit/gtfs-realtime/reference)
- [GTFS Static Specification](https://developers.google.com/transit/gtfs/reference)
- [Protocol Buffer Documentation](https://developers.google.com/protocol-buffers/docs/overview)

### Learning Resources

- [Transit Data Analysis Best Practices](https://transitcenter.org/)
- [Python for Data Analysis](https://wesmckinney.com/book/)
- [Web Dashboard Design Principles](https://www.nngroup.com/articles/dashboard-design-principles/)

## Continuous Integration

- Status: Planned
- Test coverage: TBD
- Build status: TBD

---

*This development book is a living document. All contributors should update it as the project evolves.*
