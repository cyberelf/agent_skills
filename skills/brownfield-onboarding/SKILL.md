---
name: brownfield-onboarding
description: This skill helps users get started with existing (brownfield) projects by scanning the codebase, documenting structure and purpose, analyzing architecture and technical stack, identifying design flaws, and suggesting improvements for testing and CI/CD pipelines.
tags:
  - onboarding
  - brownfield
  - documentation
  - architecture analysis
  - technical debt
  - testing strategy
---

# Brownfield Project Onboarding

## Overview

This skill provides a systematic approach to understand and document existing projects. It helps developers quickly get up to speed with unfamiliar codebases by generating comprehensive documentation about the project's structure, architecture, design decisions, and identifying areas for improvement.

## When to Use This Skill

Invoke this skill when:
- Starting work on an unfamiliar or inherited codebase
- Joining a new team or project
- Conducting a technical audit of an existing system
- User requests "help me understand this project"
- Need to document an undocumented or poorly documented project
- Preparing for a major refactoring or modernization effort

## Core Workflow

The brownfield onboarding process follows four sequential phases:

1. **Project Discovery** - Scan codebase and generate overview documentation
2. **Architecture Analysis** - Document technical stack and architectural patterns
3. **Design Assessment** - Evaluate design quality and suggest improvements
4. **Quality & Automation Review** - Assess testing coverage and CI/CD maturity

## Detailed Phase Instructions

### Phase 1: Project Discovery

**Objective**: Understand the project's purpose, structure, and main features.

#### 1.1 Initial Reconnaissance

First, gather high-level context:

```bash
# Identify the root structure
- List directories at root level
- Check for README, documentation folders
- Identify configuration files (package.json, pom.xml, requirements.txt, etc.)
- Look for LICENSE, CONTRIBUTING, or other meta files
```

**Tools to use**:
- `list_dir` for folder structure
- `file_search` for finding key files (README*, CONTRIBUTING*, docs/*)
- `read_file` for reading key documentation files

#### 1.2 Codebase Scanning

Perform comprehensive codebase analysis:

1. **Folder Structure Analysis**
   - Map out the directory hierarchy (max 3-4 levels deep)
   - Identify purpose of each major directory
   - Note any unusual or non-standard organization

2. **Technology Detection**
   - Identify programming languages used
   - Find framework indicators (imports, configs)
   - List build tools and dependency managers

3. **Entry Points Discovery**
   - Find main entry files (main.py, index.js, App.java, etc.)
   - Locate startup scripts or configuration
   - Identify API endpoints or CLI commands

4. **Feature Mapping**
   - Use `semantic_search` to find major features
   - Search for route definitions, controllers, or handlers
   - Look for domain models or business logic
   - Check for admin interfaces, APIs, or user interfaces

**Tools to use**:
- `semantic_search` for finding features: "main features", "core functionality", "API endpoints"
- `grep_search` with patterns like "route|endpoint|handler|controller"
- `file_search` for finding entry points: "**/main.*", "**/index.*", "**/app.*"

#### 1.3 Generate Project Overview

Create `.onboard/overview.md` with:

```markdown
# Project Overview: [Project Name]

## Project Purpose
[What problem does this project solve? What is its primary goal?]

## Project Type
[Web application, CLI tool, library, microservice, etc.]

## Folder Structure
```
root/
├── src/           - [purpose]
├── tests/         - [purpose]
├── docs/          - [purpose]
└── ...
```

## Main Features
1. **[Feature Name]** - [Description]
   - Location: [file paths]
   - Key components: [list]

2. **[Feature Name]** - [Description]
   - Location: [file paths]
   - Key components: [list]

[Continue for all major features]

## Entry Points
- **Main Application**: [path and description]
- **CLI Tools**: [if applicable]
- **API Server**: [if applicable]

## Key Dependencies
[List major external dependencies and their purpose]

## Documentation Status
- README: [exists/missing, quality assessment]
- API Docs: [exists/missing, format]
- Architecture Docs: [exists/missing]
- Code Comments: [sparse/adequate/excellent]
```

**Store output**: Create file at `./.onboard/overview.md`

---

### Phase 2: Architecture Analysis

**Objective**: Document the technical architecture and technology stack.

#### 2.1 Technology Stack Identification

Identify all layers of the stack:

1. **Programming Languages & Versions**
   - Primary language(s)
   - Version requirements
   - Check config files: package.json, pom.xml, go.mod, requirements.txt, etc.

2. **Frameworks & Libraries**
   - Web frameworks (Express, Django, Spring Boot, etc.)
   - UI frameworks (React, Vue, Angular, etc.)
   - Testing frameworks
   - Build tools and task runners

3. **Infrastructure & Platform**
   - Database(s) and version
   - Cache layers (Redis, Memcached)
   - Message queues (RabbitMQ, Kafka)
   - Search engines (Elasticsearch, Solr)
   - Container orchestration (Docker, Kubernetes)

4. **External Services & APIs**
   - Third-party integrations
   - Cloud services (AWS, GCP, Azure)
   - Authentication providers

**Tools to use**:
- `read_file` on dependency files
- `grep_search` for "import", "from", "require" statements
- `semantic_search` for "database connection", "API client", "service integration"

#### 2.2 Architectural Pattern Recognition

Identify the architectural style:

1. **Overall Architecture**
   - Monolith vs. Microservices
   - Layered architecture (presentation, business, data)
   - Domain-Driven Design (DDD)
   - Event-driven architecture
   - Serverless

2. **Design Patterns**
   - MVC, MVP, MVVM
   - Repository pattern
   - Service layer pattern
   - Factory, Strategy, Observer patterns
   - Dependency injection

3. **Code Organization**
   - Feature-based vs. layer-based
   - Module boundaries
   - Separation of concerns

**Tools to use**:
- `semantic_search` for "architecture", "design pattern", "layer", "service"
- `grep_search` for class/interface patterns
- `list_code_usages` for understanding key abstractions

#### 2.3 Data Flow Analysis

Map how data moves through the system:

1. **Request Flow**
   - Entry points → routing → controllers/handlers → services → data access
   - Middleware/interceptors
   - Error handling

2. **Data Storage**
   - Database schema location
   - ORM/ODM usage
   - Migration strategy

3. **State Management**
   - Session handling
   - Cache strategy
   - Frontend state (if applicable)

#### 2.4 Generate Architecture Document

Create `.onboard/architecture.md` with:

```markdown
# Architecture Overview: [Project Name]

## Technical Stack

### Languages & Runtime
- **Primary Language**: [e.g., Python 3.11]
- **Additional Languages**: [if any]

### Backend Stack
- **Framework**: [e.g., Django 4.2]
- **Web Server**: [e.g., Gunicorn, Nginx]
- **Database**: [e.g., PostgreSQL 15]
- **Cache**: [e.g., Redis 7]
- **Message Queue**: [if applicable]

### Frontend Stack (if applicable)
- **Framework**: [e.g., React 18]
- **Build Tool**: [e.g., Vite]
- **State Management**: [e.g., Redux]
- **UI Library**: [e.g., Material-UI]

### DevOps & Infrastructure
- **Containerization**: [Docker, Docker Compose]
- **Orchestration**: [Kubernetes, etc.]
- **Cloud Platform**: [AWS, GCP, Azure, self-hosted]
- **CI/CD**: [GitHub Actions, Jenkins, etc.]

## Architectural Style

**Primary Pattern**: [Monolith/Microservices/Serverless/Hybrid]

### Architecture Diagram (Text-based)
```
[Create a simple ASCII or markdown diagram showing major components]
```

### Layers
1. **Presentation Layer**
   - Location: [paths]
   - Responsibilities: [description]

2. **Business Logic Layer**
   - Location: [paths]
   - Responsibilities: [description]

3. **Data Access Layer**
   - Location: [paths]
   - Responsibilities: [description]

4. **Integration Layer**
   - Location: [paths]
   - Responsibilities: [description]

## Key Design Patterns

### [Pattern Name]
- **Usage**: [where it's used]
- **Implementation**: [brief description]

[Repeat for each major pattern]

## Data Flow

### Request Flow
1. [Entry point] → 2. [Routing] → 3. [Controller] → 4. [Service] → 5. [Repository] → 6. [Database]

### Authentication/Authorization
[How auth is handled]

### Error Handling
[Error handling strategy]

## External Dependencies

### Critical Dependencies
| Dependency | Purpose | Version | License |
|------------|---------|---------|---------|
| [name]     | [purpose] | [ver] | [license] |

### Third-Party Integrations
- **[Service Name]**: [purpose and usage]

## Configuration Management
- **Config Location**: [where configs are stored]
- **Environment Variables**: [how they're managed]
- **Secrets Management**: [how secrets are handled]

## Scalability Considerations
[Current approach to scalability, if evident]

## Security Measures
[Observed security patterns: auth, encryption, input validation, etc.]
```

**Store output**: Create file at `./.onboard/architecture.md`

---

### Phase 3: Design Assessment

**Objective**: Evaluate design quality and identify improvement opportunities.

#### 3.1 Design Quality Analysis

Assess the current design against best practices:

1. **Architectural Alignment**
   - Does the implementation match the project's stated purpose?
   - Are there unnecessary complexities for the problem domain?
   - Is the chosen architecture appropriate for the scale?

2. **Code Quality Indicators**
   - **Coupling**: Are modules tightly coupled or loosely coupled?
   - **Cohesion**: Do modules have clear, focused responsibilities?
   - **Duplication**: Is there significant code duplication?
   - **Complexity**: Are there overly complex functions or classes?

3. **SOLID Principles Adherence**
   - Single Responsibility Principle
   - Open/Closed Principle
   - Liskov Substitution Principle
   - Interface Segregation Principle
   - Dependency Inversion Principle

4. **Common Anti-Patterns**
   - God objects/classes
   - Circular dependencies
   - Tight coupling to external services
   - Hardcoded values
   - Missing abstractions
   - Over-engineering or under-engineering

**Tools to use**:
- `semantic_search` for "TODO", "FIXME", "HACK", "XXX"
- `grep_search` for code smells
- `list_code_usages` to check for tight coupling
- `get_errors` to identify existing issues

#### 3.2 Technical Debt Identification

Look for signs of technical debt:

1. **Code Smells**
   - Long methods/functions (>50 lines)
   - Large classes (>500 lines)
   - Long parameter lists
   - Nested conditionals (>3 levels)

2. **Deprecated Patterns**
   - Use of outdated APIs
   - Deprecated dependencies
   - Legacy code patterns

3. **Missing Abstractions**
   - Repeated logic that should be extracted
   - Business rules embedded in UI/controllers
   - Hard-to-test code

#### 3.3 Generate Design Suggestions

Create `.onboard/design_suggestions.md` with:

```markdown
# Design Assessment & Improvement Suggestions: [Project Name]

## Executive Summary
[2-3 paragraph overview of design quality and key findings]

## Overall Design Quality: [Grade: Excellent/Good/Fair/Needs Improvement]

### Strengths
- ✅ [Positive aspect 1]
- ✅ [Positive aspect 2]
- ✅ [Positive aspect 3]

### Areas for Improvement
- ⚠️ [Issue 1]
- ⚠️ [Issue 2]
- ⚠️ [Issue 3]

---

## Detailed Findings

### Finding 1: [Title - e.g., "Tight Coupling Between Modules"]

**Severity**: [Critical/High/Medium/Low]

**Current State**:
[Describe the current implementation]
- Location: [file paths]
- Impact: [what problems this causes]

**Problem**:
[Explain why this is an issue]

**Proposed Solution**:
[Describe the recommended approach]

**Benefits**:
- [Benefit 1]
- [Benefit 2]

**Implementation Complexity**: [Low/Medium/High]
**Estimated Effort**: [Hours/Days/Weeks]

---

### Finding 2: [Title]
[Repeat structure above]

---

## Architectural Recommendations

### Recommendation 1: [Title]

**Current Architecture**:
```
[Simple diagram or description]
```

**Proposed Architecture**:
```
[Improved diagram or description]
```

**Rationale**:
[Why this change would be beneficial]

**Migration Path**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Risks**:
- [Risk 1 and mitigation]
- [Risk 2 and mitigation]

---

## Code Quality Improvements

### Priority 1: High Impact, Low Effort
- [ ] [Specific action item with file references]
- [ ] [Specific action item with file references]

### Priority 2: High Impact, Medium Effort
- [ ] [Specific action item with file references]
- [ ] [Specific action item with file references]

### Priority 3: Medium Impact, Low Effort
- [ ] [Specific action item with file references]

### Priority 4: Long-term Improvements
- [ ] [Specific action item with file references]

---

## Refactoring Opportunities

### Opportunity 1: [Extract Service/Refactor Module/etc.]
- **Files**: [list]
- **Description**: [what to refactor]
- **Reason**: [why this would improve the code]
- **Approach**: [how to do it]

---

## Dependency Recommendations

### Updates Needed
| Dependency | Current | Latest | Breaking Changes | Priority |
|------------|---------|--------|------------------|----------|
| [name]     | [ver]   | [ver]  | Yes/No          | High/Med/Low |

### Security Vulnerabilities
[Any known vulnerabilities in dependencies]

### Bloat Reduction
[Dependencies that could be removed or replaced]

---

## Performance Considerations

[Any observed performance anti-patterns or optimization opportunities]

---

## Next Steps

### Immediate Actions (Do First)
1. [Action item]
2. [Action item]

### Short-term Improvements (Next Sprint/Month)
1. [Action item]
2. [Action item]

### Long-term Roadmap (Next Quarter)
1. [Action item]
2. [Action item]
```

**Store output**: Create file at `./.onboard/design_suggestions.md`

---

### Phase 4: Quality & Automation Review

**Objective**: Assess testing coverage and CI/CD maturity, propose improvements.

#### 4.1 Testing Assessment

Analyze the current testing situation:

1. **Test Coverage Analysis**
   - Identify test directories and files
   - Check for unit tests, integration tests, E2E tests
   - Look for test configuration files
   - Assess test coverage if metrics available

2. **Testing Frameworks**
   - What testing tools are used? (pytest, Jest, JUnit, etc.)
   - Mocking libraries
   - Test runners
   - Coverage tools

3. **Test Quality**
   - Are tests comprehensive?
   - Do tests follow AAA pattern (Arrange, Act, Assert)?
   - Are tests independent and isolated?
   - Are there flaky tests?

4. **Missing Test Types**
   - Unit tests for core business logic
   - Integration tests for module interactions
   - End-to-end tests for critical user flows
   - Performance/load tests
   - Security tests

**Tools to use**:
- `file_search` for test files: "**/test_*.py", "**/*.test.js", "**/*_spec.rb"
- `grep_search` for test patterns: "describe|it|test|should"
- `semantic_search` for "test", "coverage", "testing strategy"
- `read_file` on test configuration files

#### 4.2 CI/CD Pipeline Analysis

Evaluate automation maturity:

1. **CI/CD Platform Detection**
   - GitHub Actions (.github/workflows/)
   - GitLab CI (.gitlab-ci.yml)
   - Jenkins (Jenkinsfile)
   - CircleCI (.circleci/config.yml)
   - Travis CI (.travis.yml)
   - Other platforms

2. **Pipeline Stages**
   - Build automation
   - Test execution
   - Code quality checks (linting, static analysis)
   - Security scanning
   - Deployment automation
   - Rollback strategies

3. **Quality Gates**
   - Required checks before merge
   - Code coverage thresholds
   - Performance benchmarks
   - Security scan requirements

4. **Missing Automation**
   - Automated builds
   - Automated testing
   - Automated deployments
   - Dependency updates (Dependabot, Renovate)
   - Security scanning
   - Code quality checks

**Tools to use**:
- `file_search` for CI files: ".github/workflows/*", ".gitlab-ci.yml", "Jenkinsfile"
- `read_file` on CI configuration files
- `grep_search` for deployment scripts

#### 4.3 Development Workflow Analysis

Assess the development process:

1. **Pre-commit Hooks**
   - Husky, pre-commit, or similar
   - What checks run locally?

2. **Code Review Process**
   - PR/MR templates
   - Review requirements
   - Automated reviews (CodeQL, SonarQube)

3. **Documentation Generation**
   - Automated API docs
   - Changelog generation
   - Version management

#### 4.4 Generate Quality & Automation Suggestions

Create `.onboard/guardrail_suggestions.md` with:

```markdown
# Quality & Automation Improvement Suggestions: [Project Name]

## Executive Summary
[Overview of current testing and CI/CD maturity]

**Testing Maturity**: [Grade: Excellent/Good/Fair/Poor/None]  
**CI/CD Maturity**: [Grade: Excellent/Good/Fair/Poor/None]  
**Overall Risk Level**: [Low/Medium/High/Critical]

---

## Current State Assessment

### Testing Coverage

#### Existing Tests
- **Unit Tests**: [Present/Absent] - [Location if present]
- **Integration Tests**: [Present/Absent] - [Location if present]
- **E2E Tests**: [Present/Absent] - [Location if present]
- **Performance Tests**: [Present/Absent]
- **Security Tests**: [Present/Absent]

#### Testing Frameworks in Use
- [Framework 1]: [Purpose]
- [Framework 2]: [Purpose]

#### Coverage Metrics
[If available, include coverage percentages or note "No coverage reporting configured"]

### CI/CD Status

#### Current Pipeline
[Describe what exists, or state "No CI/CD pipeline configured"]

**Pipeline Platform**: [GitHub Actions/GitLab CI/Jenkins/etc. or None]

**Automated Stages**:
- ✅ [Stage that exists]
- ❌ [Stage that doesn't exist]

#### Deployment Strategy
[Describe current deployment process, manual or automated]

---

## Testing Improvements

### Priority 1: Critical Gaps

#### 1.1 Missing Unit Tests

**Impact**: [HIGH] - No automated validation of core business logic

**Proposed Action**:
Create unit tests for critical components:

1. **[Component/Module 1]** (Priority: Critical)
   - Files: [list file paths]
   - Functions to test: [key functions]
   - Coverage target: 80%+
   
2. **[Component/Module 2]** (Priority: High)
   - Files: [list file paths]
   - Functions to test: [key functions]
   - Coverage target: 70%+

**Recommended Framework**: [specific framework and reason]

**Example Test Structure**:
```python
# tests/test_[module].py
import pytest
from [module] import [function]

def test_[function_name]_[scenario]():
    # Arrange
    [setup test data]
    
    # Act
    result = [function](test_data)
    
    # Assert
    assert result == expected
```

**Implementation Steps**:
1. Install test framework: `[command]`
2. Create test directory structure
3. Configure test runner
4. Write tests for critical paths first
5. Set up coverage reporting

**Effort Estimate**: [X days/weeks]

---

#### 1.2 Missing Integration Tests

**Impact**: [HIGH/MEDIUM] - No validation of module interactions

**Proposed Action**:
Create integration tests for:

1. **[Integration Point 1]** (e.g., API endpoints)
   - Test scenarios: [list key scenarios]
   - Endpoints to cover: [list endpoints]

2. **[Integration Point 2]** (e.g., Database interactions)
   - Test scenarios: [list key scenarios]

**Recommended Framework**: [specific framework]

**Implementation Steps**:
1. [Step 1]
2. [Step 2]

**Effort Estimate**: [X days/weeks]

---

#### 1.3 Missing E2E Tests

**Impact**: [MEDIUM] - No validation of complete user flows

**Proposed Action**:
Implement E2E tests for critical user journeys:

1. **[User Journey 1]** (e.g., User Registration Flow)
   - Steps: [list steps]
   - Expected outcomes: [list outcomes]

2. **[User Journey 2]** (e.g., Purchase Flow)
   - Steps: [list steps]
   - Expected outcomes: [list outcomes]

**Recommended Framework**: [Playwright/Cypress/Selenium/etc.]

**Implementation Steps**:
1. [Step 1]
2. [Step 2]

**Effort Estimate**: [X days/weeks]

---

### Priority 2: Quality Enhancements

#### 2.1 Test Coverage Reporting

**Action**: Set up automated coverage reporting

**Tools**: [coverage.py/Istanbul/JaCoCo/etc.]

**Configuration**:
```[language]
[Example configuration]
```

**Integration**:
- Add coverage reporting to CI pipeline
- Set coverage thresholds (recommend: 70% minimum)
- Block PRs that reduce coverage

---

#### 2.2 Test Data Management

**Current Issue**: [Describe any issues with test data]

**Proposed Solution**:
- Implement test fixtures/factories
- Use in-memory databases for fast tests
- Seed data scripts for consistent test environments

---

## CI/CD Pipeline Improvements

### Priority 1: Essential Automation

#### 1.1 Continuous Integration Setup

**Current State**: [Describe current state or "No CI configured"]

**Proposed Pipeline**:

Create `.github/workflows/ci.yml` (or equivalent):

```yaml
name: Continuous Integration

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up [Language/Runtime]
        uses: [appropriate action]
        with:
          [language]-version: [version]
      
      - name: Install dependencies
        run: [install command]
      
      - name: Run linter
        run: [lint command]
      
      - name: Run tests
        run: [test command]
      
      - name: Check coverage
        run: [coverage command]
      
      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
```

**Benefits**:
- Automated testing on every commit
- Early detection of breaking changes
- Consistent test environment

**Implementation Steps**:
1. Create workflow file
2. Configure secrets/environment variables
3. Test the pipeline
4. Add branch protection rules

**Effort Estimate**: [X hours/days]

---

#### 1.2 Code Quality Checks

**Proposed Actions**:

1. **Linting**
   - Tool: [ESLint/Pylint/RuboCop/etc.]
   - Configuration: [reference or example]
   - Integration: Add to CI pipeline

2. **Static Analysis**
   - Tool: [SonarQube/CodeQL/Bandit/etc.]
   - Focus: Security vulnerabilities, code smells
   - Integration: Add to CI pipeline

3. **Dependency Scanning**
   - Tool: [Dependabot/Snyk/npm audit/etc.]
   - Purpose: Identify vulnerable dependencies
   - Configuration: [example]

**Example Configuration**:
```yaml
- name: Run linter
  run: [command]
  
- name: Run security scan
  uses: [action]
```

**Effort Estimate**: [X hours/days]

---

#### 1.3 Automated Deployment

**Current Deployment**: [Describe current process - likely manual]

**Proposed CD Pipeline**:

**Environments**:
1. Development - Auto-deploy on merge to `develop`
2. Staging - Auto-deploy on merge to `main`
3. Production - Manual approval required

**Deployment Strategy**: [Blue-Green/Rolling/Canary/etc.]

**Pipeline Example**:
```yaml
deploy:
  needs: test
  runs-on: ubuntu-latest
  if: github.ref == 'refs/heads/main'
  
  steps:
    - name: Deploy to staging
      run: [deploy command]
    
    - name: Run smoke tests
      run: [smoke test command]
```

**Rollback Strategy**:
[Describe how to rollback failed deployments]

**Effort Estimate**: [X days/weeks]

---

### Priority 2: Advanced Automation

#### 2.1 Automated Dependency Updates

**Tool**: Dependabot/Renovate

**Configuration**:
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "[npm/pip/maven/etc]"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
```

**Benefits**:
- Stay up-to-date with dependencies
- Automatic security patches
- Reduced manual maintenance

---

#### 2.2 Performance Testing

**Proposed Action**: Add performance benchmarks to CI

**Tools**: [k6/JMeter/Locust/etc.]

**Implementation**:
- Define performance baselines
- Run benchmarks on every PR
- Fail CI if performance degrades >X%

---

#### 2.3 Automated Release Management

**Proposed Action**: Automate versioning and changelogs

**Tools**: 
- Semantic versioning
- Conventional commits
- Automated changelog generation

**Benefits**:
- Consistent versioning
- Clear release notes
- Reduced manual effort

---

## Development Workflow Enhancements

### Pre-commit Hooks

**Current State**: [Present/Absent]

**Proposed Setup**:

Install pre-commit framework:
```bash
[installation command]
```

Configuration (`.pre-commit-config.yaml`):
```yaml
repos:
  - repo: [linter repo]
    hooks:
      - id: [linter]
  
  - repo: [formatter repo]
    hooks:
      - id: [formatter]
  
  - repo: [test repo]
    hooks:
      - id: [test hook]
```

**Checks to Include**:
- Code formatting
- Linting
- Type checking (if applicable)
- Unit tests for changed files
- Commit message validation

---

### Pull Request Templates

**Current State**: [Present/Absent]

**Proposed Template** (`.github/pull_request_template.md`):
```markdown
## Description
[What does this PR do?]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Tests pass locally
- [ ] Documentation updated
```

---

## Agent-Friendly Validation

### Automated Validation for AI Agents

To enable AI agents to validate their own work:

1. **Test Suite**
   - Comprehensive test coverage
   - Fast-running test suite (<5 minutes)
   - Clear test names describing what they validate

2. **CI Pipeline**
   - Quick feedback (<10 minutes)
   - Clear error messages
   - Automatic formatting checks

3. **Documentation**
   - Clear coding standards
   - Architecture decision records
   - API documentation

4. **Validation Scripts**
   Create `scripts/validate.sh`:
   ```bash
   #!/bin/bash
   set -e
   
   echo "Running validation..."
   
   # Format check
   [format check command]
   
   # Lint
   [lint command]
   
   # Type check
   [type check command]
   
   # Tests
   [test command]
   
   # Coverage
   [coverage command]
   
   echo "✅ All validations passed!"
   ```

---

## Implementation Roadmap

### Phase 1: Immediate (Week 1-2)
- [ ] Set up basic CI pipeline with automated testing
- [ ] Add linting and formatting checks
- [ ] Create initial unit tests for critical paths
- [ ] Set up test coverage reporting

**Success Criteria**: 
- CI pipeline runs on every PR
- At least 50% test coverage on critical components

### Phase 2: Short-term (Month 1)
- [ ] Increase test coverage to 70%+
- [ ] Add integration tests
- [ ] Set up pre-commit hooks
- [ ] Configure dependency scanning
- [ ] Create PR templates

**Success Criteria**:
- 70% overall test coverage
- All PRs go through automated checks

### Phase 3: Medium-term (Month 2-3)
- [ ] Implement E2E tests for critical flows
- [ ] Set up automated deployment pipeline
- [ ] Add performance testing
- [ ] Implement automated releases

**Success Criteria**:
- Automated deployments to staging
- E2E tests cover top 3 user journeys

### Phase 4: Long-term (Quarter 2)
- [ ] Achieve 80%+ test coverage
- [ ] Production deployment automation
- [ ] Advanced monitoring and alerting
- [ ] Load testing in CI

**Success Criteria**:
- Full CI/CD maturity
- Confident automated releases

---

## Estimated Overall Effort

- **Testing Setup**: [X weeks]
- **CI Pipeline**: [X weeks]
- **CD Pipeline**: [X weeks]
- **Total**: [X weeks] with [Y] person team

---

## ROI Analysis

### Current Costs (Without Improvements)
- Manual testing time: [estimate]
- Bug escape rate: [if known]
- Deployment time: [manual deployment duration]
- Downtime incidents: [if tracked]

### Expected Benefits
- **Time Savings**: [X hours/week] from automated testing
- **Quality Improvement**: [Y%] reduction in production bugs
- **Faster Deployment**: [Z minutes] vs [A hours] manual process
- **Confidence**: Agents can validate their work automatically
- **Developer Experience**: Faster feedback, less context switching

---

## Resources & Tools

### Recommended Tools
- **Testing**: [specific recommendations]
- **CI/CD**: [specific recommendations]
- **Code Quality**: [specific recommendations]
- **Monitoring**: [specific recommendations]

### Learning Resources
- [Link to testing best practices]
- [Link to CI/CD guides]
- [Link to project-specific docs to create]

---

## Conclusion

[Summary of key recommendations and expected impact]

**Next Action**: [Most important first step]
```

**Store output**: Create file at `./.onboard/guardrail_suggestions.md`

---

## Complete Workflow Execution

When a user invokes this skill, execute all four phases in sequence:

1. **Phase 1**: Generate `.onboard/overview.md`
2. **Phase 2**: Generate `.onboard/architecture.md`
3. **Phase 3**: Generate `.onboard/design_suggestions.md`
4. **Phase 4**: Generate `.onboard/guardrail_suggestions.md`

After completion, provide a summary:

```
✅ Brownfield onboarding complete!

Generated documentation:
- .onboard/overview.md (Project structure and features)
- .onboard/architecture.md (Technical stack and architecture)
- .onboard/design_suggestions.md (Design improvements)
- .onboard/guardrail_suggestions.md (Testing and CI/CD recommendations)

These documents provide a comprehensive understanding of the project and actionable improvement suggestions.
```

## Notes & Best Practices

- **Comprehensive Analysis**: Take time to thoroughly explore the codebase before writing documentation
- **Be Specific**: Include file paths, line numbers, and concrete examples in suggestions
- **Prioritize**: Rank suggestions by impact and effort
- **Actionable**: Provide clear, implementable recommendations, not just observations
- **Context-Aware**: Tailor suggestions to the project's size, domain, and maturity
- **Positive Framing**: Start with strengths before discussing improvements
- **Realistic Estimates**: Provide effort estimates to help with planning
- **Agent-Friendly**: Ensure recommendations enable AI agents to validate their work automatically

## Common Pitfalls to Avoid

- ❌ Generating superficial documentation without deep analysis
- ❌ Making technology recommendations without understanding constraints
- ❌ Suggesting major rewrites instead of incremental improvements
- ❌ Ignoring existing documentation or architectural decisions
- ❌ Providing generic advice that doesn't apply to the specific project
- ❌ Overwhelming with too many suggestions without prioritization
- ❌ Missing critical security or performance issues

## Extension Points

This skill can be extended to include:
- **Security Audit**: Dedicated security vulnerability assessment
- **Performance Profiling**: Performance bottleneck identification
- **Accessibility Review**: WCAG compliance checking for web apps
- **API Documentation**: Automated API documentation generation
- **Database Analysis**: Schema design review and optimization suggestions
