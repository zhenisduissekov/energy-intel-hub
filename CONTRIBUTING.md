# Contributing to Houston Energy Market Analytics Platform

Thank you for your interest in contributing to the Houston Energy Market Analytics Platform! This project was built with Replit AI and we welcome contributions from the community.

## 🤝 Ways to Contribute

- 🐛 **Bug Reports**: Report issues or unexpected behavior
- 💡 **Feature Requests**: Suggest new features or improvements
- 📝 **Documentation**: Improve docs, tutorials, or code comments
- 🔧 **Code Contributions**: Fix bugs or implement new features
- 🧪 **Testing**: Add or improve test coverage
- 🎨 **Design**: Improve UI/UX or create visual assets

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/yourusername/houston-energy-analytics.git
cd houston-energy-analytics
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
make install-dev

# Copy environment template
cp .env.example .env
```

### 3. Start Development Services

```bash
# Start database
make db-up

# Run the application
make dev
```

## 📋 Development Guidelines

### Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting
- **Flake8** for linting
- **MyPy** for type checking
- **pytest** for testing

```bash
# Format code
make format

# Lint code
make lint

# Type check
make type-check

# Run tests
make test
```

### Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new technical indicator
fix: resolve forecasting model accuracy issue
docs: update API documentation
style: format code with black
refactor: optimize data processing pipeline
test: add unit tests for alert system
chore: update dependencies
```

### Branch Naming

Use descriptive branch names:

```
feature/add-options-pricing
fix/dashboard-loading-issue
docs/api-documentation
refactor/alert-system
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test file
pytest tests/test_forecasting.py -v
```

### Writing Tests

- Write tests for all new features
- Maintain at least 80% code coverage
- Use descriptive test names
- Include both positive and negative test cases

Example test structure:

```python
def test_price_forecasting_with_valid_data():
    """Test that forecasting works with valid price data."""
    # Arrange
    price_data = generate_test_price_data()
    
    # Act
    forecast = forecasting_model.predict(price_data)
    
    # Assert
    assert forecast is not None
    assert len(forecast) == expected_length
```

## 🏗️ Architecture Guidelines

### File Organization

```
houston-energy-analytics/
├── app.py                 # Main Streamlit app
├── pages/                 # Page components
├── utils/                 # Business logic
│   ├── api_clients.py     # External data sources
│   ├── data_processor.py  # Data analysis
│   ├── forecasting.py     # ML models
│   └── alerts.py          # Alert system
├── tests/                 # Test suite
├── scripts/               # Utility scripts
└── docs/                  # Documentation
```

### Adding New Features

1. **Data Sources**: Add new APIs in `utils/api_clients.py`
2. **Analysis**: Add processing logic in `utils/data_processor.py`
3. **UI Components**: Create new pages in `pages/`
4. **Models**: Add ML models in `utils/forecasting.py`

### Performance Considerations

- Cache expensive operations using `@st.cache_data`
- Use database connections efficiently
- Optimize API calls to avoid rate limits
- Profile code for bottlenecks

## 📝 Documentation

### Code Documentation

- Use clear, descriptive docstrings
- Document complex algorithms
- Include type hints
- Add inline comments for unclear logic

```python
def calculate_volatility(price_data: pd.Series, window: int = 20) -> float:
    """
    Calculate annualized volatility using rolling standard deviation.
    
    Args:
        price_data: Time series of prices
        window: Rolling window size in days
        
    Returns:
        Annualized volatility as a percentage
    """
```

### README Updates

When adding features, update:
- Feature list in README
- Installation instructions if needed
- Configuration options
- Usage examples

## 🔒 Security

### Security Best Practices

- Never commit API keys or secrets
- Use environment variables for configuration
- Validate all user inputs
- Follow OWASP security guidelines
- Report security vulnerabilities privately

### Reporting Security Issues

Email security issues to: security@houston-energy-analytics.com

## 🚀 Pull Request Process

### Before Submitting

1. ✅ Tests pass (`make test`)
2. ✅ Code is formatted (`make format`)
3. ✅ No linting errors (`make lint`)
4. ✅ Documentation updated
5. ✅ Commit messages follow convention

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] Unit tests added/updated
- [ ] Manual testing completed
- [ ] Edge cases considered

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed code
- [ ] Documentation updated
- [ ] Tests added/updated
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests
2. **Code Review**: Maintainers review code quality
3. **Manual Testing**: Features tested in development
4. **Approval**: Two approvals required for merge

## 🏷️ Issue Guidelines

### Bug Reports

Use the bug report template and include:

- **Environment**: OS, Python version, dependencies
- **Steps to Reproduce**: Clear, numbered steps
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Screenshots**: If applicable
- **Additional Context**: Relevant details

### Feature Requests

Use the feature request template and include:

- **Problem**: What problem does this solve?
- **Solution**: Describe your proposed solution
- **Alternatives**: Other solutions considered
- **Additional Context**: Use cases, examples

## 🎯 Development Priorities

### High Priority
- Performance optimization
- Test coverage improvement
- Security enhancements
- Documentation updates

### Medium Priority
- New technical indicators
- Enhanced visualizations
- Mobile responsiveness
- API integrations

### Future Enhancements
- Multi-user support
- Advanced ML models
- Real-time WebSocket feeds
- Mobile application

## 🆘 Getting Help

### Communication Channels

- **GitHub Discussions**: General questions and ideas
- **GitHub Issues**: Bug reports and feature requests
- **Email**: Direct contact for sensitive issues

### Development Support

- **Documentation**: Check the Wiki for detailed guides
- **Examples**: Look at existing code for patterns
- **Tests**: Review test files for usage examples

## 🏆 Recognition

Contributors will be recognized in:

- **README**: Contributors section
- **Releases**: Release notes acknowledgments
- **GitHub**: Contributor graphs and statistics

## 📜 Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

---

**Thank you for contributing to the Houston Energy Market Analytics Platform!** 🙏

Built with ❤️ using Replit AI