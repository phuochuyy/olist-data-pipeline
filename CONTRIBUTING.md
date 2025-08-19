# Contributing to Olist Data Pipeline

Thank you for your interest in contributing to the Olist Data Pipeline project! This document provides guidelines and instructions for contributing.

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.10+
- Git
- Basic knowledge of data engineering concepts

### Development Setup

1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/your-username/olist-data-pipeline.git
   cd olist-data-pipeline
   ```

3. **Set up development environment**:
   ```bash
   cp .env.example .env
   cp dbt_project/profiles.yml.example dbt_project/profiles.yml
   make setup
   ```

4. **Start development stack**:
   ```bash
   make up
   ```

## 📝 Development Guidelines

### Code Style

- **Python**: Follow PEP 8 standards
- **SQL**: Use lowercase with underscores
- **dbt**: Follow dbt style guide
- **Docker**: Use multi-stage builds when appropriate

### Commit Messages

Use conventional commits format:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
```
feat(dbt): add customer segmentation model
fix(airflow): resolve task dependency issue
docs(readme): update installation instructions
```

### Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
3. **Test your changes**:
   ```bash
   make test
   make lint
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat(scope): your description"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**

### Pull Request Guidelines

- **Title**: Use descriptive title
- **Description**: Explain what and why
- **Testing**: Include test results
- **Documentation**: Update docs if needed
- **Screenshots**: Add if UI changes

## 🧪 Testing

### Running Tests

```bash
# dbt tests
make dbt-test

# Data quality tests
make data-quality-test

# Integration tests
make integration-test
```

### Adding Tests

- **dbt models**: Add tests in `schema.yml`
- **Python code**: Use pytest
- **Data quality**: Use Great Expectations

## 📚 Project Structure

```
├── airflow/              # Airflow DAGs and plugins
├── dbt_project/          # dbt models and tests
├── spark/               # Spark jobs
├── great_expectations/   # Data quality tests
├── sql/                 # SQL scripts
├── notebooks/           # Jupyter notebooks
├── init/                # Database initialization
└── config/              # Configuration files
```

## 🐛 Reporting Issues

### Bug Reports

When reporting bugs, include:
- **Environment details**
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Error messages/logs**
- **Screenshots if applicable**

### Feature Requests

When requesting features:
- **Use case description**
- **Proposed solution**
- **Alternative solutions**
- **Additional context**

## 💡 Contribution Ideas

### Beginner Friendly

- [ ] Add more data quality tests
- [ ] Improve documentation
- [ ] Add example queries
- [ ] Create tutorial notebooks

### Intermediate

- [ ] Add new dbt models
- [ ] Implement data lineage tracking
- [ ] Add monitoring dashboards
- [ ] Optimize Spark jobs

### Advanced

- [ ] Implement streaming pipeline
- [ ] Add ML model training
- [ ] Setup CI/CD pipeline
- [ ] Add security features

## 🏆 Recognition

Contributors will be:
- Listed in README.md
- Mentioned in release notes
- Given contributor badge

## 📞 Getting Help

- **Discord**: [Join our community](#)
- **GitHub Issues**: For bugs and features
- **GitHub Discussions**: For questions
- **Email**: your.email@example.com

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.
