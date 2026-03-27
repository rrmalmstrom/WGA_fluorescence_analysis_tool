# Simplified Fluorescence Tool - Development Setup Plan

## Overview
This is the complete handoff package for implementing the simplified fluorescence data analysis tool using Test-Driven Development (TDD) methodology in a clean, separate environment.

## Phase 1: Environment Setup

### Step 1: Create New Project Directory
```bash
# Navigate to parent directory
cd /Users/RRMalmstrom/Desktop/Programming/

# Create new project directory
mkdir fluorescence_tool_simplified
cd fluorescence_tool_simplified

# Initialize git repository (separate from current repo)
git init
```

### Step 2: Copy Essential Resources
```bash
# Copy test data files for development and testing
mkdir -p test_data
cp ../AI_MDA_curve_tool/example_input_files/* test_data/

# Copy reference algorithm (for reference only, not direct use)
mkdir -p reference
cp ../AI_MDA_curve_tool/analyze_fluorescence_data.py reference/

# Create basic project structure matching architecture
mkdir -p fluorescence_tool/{gui,core,parsers,algorithms,utils}
mkdir -p tests/{unit,integration,performance}
```

### Step 3: Create Environment Configuration
Create `environment.yml`:
```yaml
name: fluorescence-tool
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.9
  - numpy=1.24
  - scipy=1.10
  - pandas=2.0
  - matplotlib=3.7
  - pytest=7.4
  - pytest-cov=4.1
  - black=23.7
  - flake8=6.0
```

### Step 4: Setup Environment
```bash
# Create conda environment
conda env create -f environment.yml

# Activate environment
conda activate fluorescence-tool

# Verify installation
python -c "import numpy, scipy, pandas, matplotlib, tkinter; print('All dependencies ready')"
```

## Phase 2: TDD Implementation Strategy

### Core TDD Principles for This Project
1. **Red-Green-Refactor Cycle**: Write failing test → Make it pass → Improve code
2. **Test First**: Always write tests before implementation
3. **Small Steps**: Implement one small feature at a time
4. **Continuous Validation**: Run tests after every change

### Implementation Order (TDD Phases)

#### Phase 2A: Data Structures and Models
**TDD Approach**: Start with data models since everything depends on them

1. **Write tests for data structures first**:
   ```python
   # tests/test_models.py
   def test_fluorescence_data_creation():
       # Test FluorescenceData class initialization
   
   def test_well_info_validation():
       # Test WellInfo class validation
   
   def test_curve_fit_result_structure():
       # Test CurveFitResult class
   ```

2. **Implement data models to pass tests**:
   ```python
   # fluorescence_tool/models.py
   @dataclass
   class FluorescenceData:
       # Implementation based on technical specs
   ```

3. **Validate with existing data**:
   - Load test data files
   - Ensure data structures handle real data correctly

#### Phase 2B: File Parsers
**TDD Approach**: Test with real data files from the beginning

1. **Write parser tests using actual test data**:
   ```python
   # tests/test_bmg_parser.py
   def test_parse_real_bmg_file():
       parser = BMGParser()
       result = parser.parse_file('test_data/RM5097.96HL.BNCT.1.CSV')
       assert isinstance(result, FluorescenceData)
       assert len(result.wells) > 0
   ```

2. **Implement parsers to handle real data**:
   - Reference existing algorithm for time parsing logic
   - Extract proven patterns from `analyze_fluorescence_data.py`

3. **Validate against known good data**:
   - Compare parsed results with expected values
   - Ensure time conversion accuracy

#### Phase 2C: Core Algorithms
**TDD Approach**: Use synthetic data for predictable testing

1. **Create synthetic data generators for testing**:
   ```python
   # tests/test_data/synthetic_data.py
   def generate_sigmoid_curve(params, noise_level=0.1):
       # Generate known sigmoid curves for testing
   ```

2. **Write algorithm tests with known outcomes**:
   ```python
   # tests/test_curve_fitting.py
   def test_curve_fitting_synthetic_data():
       # Test with synthetic data where we know the answer
   ```

3. **Implement algorithms using proven approaches**:
   - Adapt 5-parameter sigmoid from existing code
   - Use proven adaptive fitting strategy
   - Implement baseline percentage threshold method

#### Phase 2D: GUI Components
**TDD Approach**: Test GUI components with mock data

1. **Write GUI component tests**:
   ```python
   # tests/test_gui_components.py
   def test_plate_view_creation():
       # Test plate view with mock data
   ```

2. **Implement GUI incrementally**:
   - Start with basic tkinter window
   - Add components one by one
   - Test each component independently

#### Phase 2E: Integration and Polish
**TDD Approach**: End-to-end workflow testing

1. **Write integration tests**:
   ```python
   # tests/test_integration.py
   def test_complete_bmg_workflow():
       # Test entire workflow from file load to export
   ```

2. **Implement export functionality**
3. **Performance testing and optimization**

## Phase 3: Resource Management Strategy

### What to Extract from Existing Code
1. **Proven Algorithm Logic** (reference only):
   - 5-parameter sigmoid function with overflow protection
   - Adaptive fitting strategy with multiple attempts
   - Baseline percentage threshold calculation
   - Time parsing patterns for BMG format

2. **Test Data Files**:
   - `RM5097.96HL.BNCT.1.CSV` (BMG format)
   - `TEST01.BIORAD.FORMAT.1.txt` (BioRad format)
   - `RM5097_layout.csv` (Layout format)

3. **Validation Patterns**:
   - Data cleaning approaches
   - Error handling strategies
   - File format detection logic

### What NOT to Copy
- Complex web framework code
- Database integration
- Microservices architecture
- Over-engineered abstractions

## Phase 4: Quality Assurance Plan

### Continuous Testing Strategy
```bash
# Run tests frequently during development
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=fluorescence_tool --cov-report=html

# Run specific test categories
pytest tests/unit/ -v          # Unit tests only
pytest tests/integration/ -v   # Integration tests only
```

### Validation Checkpoints
1. **After each TDD cycle**: All tests pass
2. **After each component**: Integration tests pass
3. **Weekly**: Full test suite + manual testing
4. **Before completion**: Performance validation

### Success Criteria
- [ ] All test data files parse correctly
- [ ] Curve fitting produces reasonable results on test data
- [ ] GUI loads and displays data without errors
- [ ] Export functionality generates valid files
- [ ] Performance meets requirements (< 30 seconds for 384-well analysis)

## Phase 5: Implementation Instructions for Coding Agent

### Daily TDD Workflow
1. **Start each session**:
   ```bash
   conda activate fluorescence-tool
   cd fluorescence_tool_simplified
   git status  # Check current state
   ```

2. **Before implementing any feature**:
   - Write failing test first
   - Run test to confirm it fails
   - Implement minimal code to pass test
   - Refactor if needed
   - Commit changes

3. **Communication Protocol**:
   - **Before each component**: Explain what you're building and why
   - **During implementation**: Show test-first approach
   - **After each milestone**: Demonstrate working functionality
   - **Ask questions**: If requirements are unclear

### Step-by-Step Implementation Guide
1. **Phase 1**: Set up environment, create data models with tests
2. **Phase 2**: Implement BMG parser with TDD
3. **Phase 3**: Implement BioRad parser with TDD
4. **Phase 4**: Implement layout parser with TDD
5. **Phase 5**: Implement curve fitting algorithms with TDD
6. **Phase 6**: Implement basic GUI with TDD
7. **Phase 7**: Implement interactive features with TDD
8. **Phase 8**: Implement export functionality with TDD
9. **Phase 9**: Integration testing and polish

### Key Success Factors
- **Use MCP Context7** for latest documentation and best practices
- **Ask questions** when architecture decisions are unclear
- **Show progress** step-by-step rather than large commits
- **Validate frequently** against real test data
- **Keep it simple** - avoid over-engineering

This plan provides a complete roadmap for implementing the simplified fluorescence tool using proven TDD methodology while leveraging the best parts of the existing codebase.