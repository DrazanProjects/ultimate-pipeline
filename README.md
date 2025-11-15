# 🚀 Ultimate Pipeline

<div align="center">

### The Ultimate Xcode Build, Test & Diagnostics Platform

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://www.apple.com/macos/)
[![Xcode](https://img.shields.io/badge/Xcode-14.0+-blue.svg)](https://developer.apple.com/xcode/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

*A visually stunning, cutting-edge GUI application that revolutionizes Xcode project management*

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Screenshots](#-screenshots) • [Contributing](#-contributing)

</div>

---

## 🎯 Overview

**Ultimate Pipeline** is a comprehensive, next-generation tool that combines build automation, comprehensive testing, deep diagnostics, and beautiful reporting into one stunning application. Built with modern UI/UX principles, it transforms the Xcode development workflow into an intuitive, visual experience.

### Why Ultimate Pipeline?

- 🎨 **Stunning Modern GUI** - Beautiful dark-themed interface with smooth animations
- 🚀 **All-in-One Solution** - Build, test, diagnose, and deploy from one place
- 🔍 **Deep Diagnostics** - Comprehensive code quality analysis and issue detection
- 📊 **Beautiful Reports** - Interactive HTML reports with animated visualizations
- 🎯 **Zero Configuration** - Auto-detects projects, schemes, and targets
- 📱 **Multi-Target Support** - Works with simulators and physical devices
- ⚡ **Lightning Fast** - Optimized performance with real-time feedback
- 🌍 **Universal Compatibility** - Works with any Xcode project or workspace

---

## ✨ Features

### 🔨 Build Automation
- **Smart Project Detection** - Automatically finds and configures Xcode projects
- **Real-Time Progress** - Live build output with syntax highlighting
- **Error Analysis** - Intelligent error detection and categorization
- **Multi-Configuration Support** - Debug, Release, and custom configurations

### 🧪 Comprehensive Testing
- **Parallel Test Execution** - Run tests across multiple devices simultaneously
- **Visual Test Results** - Beautiful tree view with status indicators
- **Performance Metrics** - Detailed timing and performance analysis
- **Test Filtering** - Run specific test suites or individual tests
- **Failure Analysis** - Detailed failure reports with stack traces

### 🔍 Advanced Diagnostics
- **Static Code Analysis** - Detect anti-patterns and code smells
- **Quality Metrics** - Measure code complexity and maintainability
- **Force Unwrap Detection** - Find potentially unsafe code patterns
- **Debug Statement Scanner** - Locate leftover print statements
- **File Size Analysis** - Identify overly large files that need refactoring

### 📊 Beautiful Reporting
- **Interactive HTML Reports** - Stunning visualizations with CSS animations
- **Gradient Backgrounds** - Modern aesthetic with animated gradients
- **Responsive Design** - Looks perfect on any screen size
- **Shareable Reports** - Easy to share with team members
- **Historical Tracking** - Compare reports over time

### 📱 Device Management
- **Simulator Support** - Automatically detect and manage simulators
- **Physical Device Support** - Deploy to connected iOS devices
- **Auto-Boot Simulators** - Automatically boot required simulators
- **Device Status Monitoring** - Real-time connection status

### ⚙️ Smart Configuration
- **No Hardcoded Values** - Works with any project structure
- **Auto-Detection** - Finds schemes, bundle IDs, and configurations
- **Custom Paths** - Support for non-standard project layouts
- **Environment Aware** - Respects your Xcode configuration

---

## 📦 Installation

### Prerequisites

- macOS 10.15 (Catalina) or later
- Python 3.8 or higher
- Xcode 14.0 or later
- Command Line Tools installed

### Quick Install

#### Option 1: Direct Download

```bash
curl -O https://raw.githubusercontent.com/DrazanProjects/ultimate-pipeline/main/ultimate_pipeline.py
chmod +x ultimate_pipeline.py
python3 ultimate_pipeline.py
```

The application will automatically install required dependencies on first run.

#### Option 2: Clone Repository

```bash
git clone https://github.com/DrazanProjects/ultimate-pipeline.git
cd ultimate-pipeline
python3 ultimate_pipeline.py
```

#### Option 3: Manual Dependency Installation

If you prefer to install dependencies manually:

```bash
pip3 install customtkinter Pillow
python3 ultimate_pipeline.py
```

### Verify Installation

Run the following to verify everything is set up correctly:

```bash
python3 --version    # Should be 3.8 or higher
xcodebuild -version  # Verify Xcode installation
xcrun simctl list    # Verify simulator access
```

---

## 🎮 Usage

### Quick Start

1. **Navigate to your Xcode project directory:**
   ```bash
   cd /path/to/your/xcode/project
   python3 ultimate_pipeline.py
   ```

2. **Or open from anywhere:**
   - Launch the app
   - Click "📁 Open Project"
   - Select your project directory

### Workflow

#### 1️⃣ **Load Project**
The app automatically detects Xcode projects in the current directory. If you're not in a project directory:
- Click **"📁 Open Project"**
- Navigate to your Xcode project folder
- The app will auto-detect `.xcworkspace` or `.xcodeproj` files

#### 2️⃣ **Select Target**
- Click **"📱 Select Target"**
- Choose between Simulator or Physical Device
- Select your preferred device from the list
- Simulators are automatically booted if needed

#### 3️⃣ **Build Project**
- Click **"🔨 Build Project"**
- Watch real-time build output in the Build Log tab
- View success/failure status in the Dashboard

#### 4️⃣ **Run Tests**
- Click **"🧪 Run Tests"**
- View detailed results in the Test Results tab
- See pass/fail counts and timing information

#### 5️⃣ **Run Diagnostics**
- Click **"🔍 Run Diagnostics"**
- Review code quality issues in the Diagnostics tab
- Address warnings and suggestions

#### 6️⃣ **Generate Report**
- Click **"📊 Generate Report"**
- Beautiful HTML report is generated automatically
- Open in browser to view interactive visualizations
- Reports are saved in `pipeline_reports/` directory

### Interface Overview

#### 📋 Control Panel (Left Sidebar)
- **Open Project** - Load an Xcode project
- **Select Target** - Choose deployment device
- **Build Project** - Compile your code
- **Run Tests** - Execute test suite
- **Run Diagnostics** - Analyze code quality
- **Generate Report** - Create visual report

#### 📑 Tabs
- **Dashboard** - Overview with statistics and welcome screen
- **Build Log** - Real-time build output with syntax highlighting
- **Test Results** - Detailed test outcomes in tree view
- **Diagnostics** - Code quality issues and warnings
- **Reports** - Report generation and management

#### 📊 Status Bar (Bottom)
- Current operation status
- Progress indicator
- Real-time updates

---

## 🖼️ Screenshots

### Main Dashboard
*Modern interface with beautiful statistics cards and gradient backgrounds*

### Build in Progress
*Real-time build output with color-coded logs and progress tracking*

### Test Results
*Visual test tree with pass/fail indicators and timing information*

### Diagnostics View
*Comprehensive code quality analysis with severity indicators*

### HTML Report
*Stunning interactive report with animated visualizations and gradient themes*

---

## 🔧 Configuration

Ultimate Pipeline is designed to work out-of-the-box with zero configuration. However, you can customize various aspects:

### Project Auto-Detection

The tool automatically searches for:
- `.xcworkspace` files (CocoaPods, SPM)
- `.xcodeproj` files
- Schemes and configurations
- Bundle identifiers

### Custom Project Paths

If your project structure is non-standard:

```python
python3 ultimate_pipeline.py
```

Then use the "Open Project" button to manually select your project directory.

### Report Customization

Reports are saved to `pipeline_reports/` in your project directory. You can find them organized by timestamp:

```
your-project/
├── pipeline_reports/
│   ├── ultimate_pipeline_report_20250114_143022.html
│   ├── ultimate_pipeline_report_20250114_150145.html
│   └── ...
```

---

## 🏗️ Architecture

### Core Components

**XcodeDetector**
- Auto-discovers projects and workspaces
- Detects schemes and configurations
- Finds simulators and devices
- Extracts bundle identifiers

**CommandRunner**
- Executes xcodebuild commands
- Streams real-time output
- Handles process management
- Error handling and timeouts

**TestParser**
- Parses xcodebuild test output
- Extracts individual test results
- Calculates statistics
- Formats test data

**DiagnosticsEngine**
- Analyzes build output for errors
- Scans source code for issues
- Detects code quality problems
- Categorizes issues by severity

**ReportGenerator**
- Creates beautiful HTML reports
- Implements animated visualizations
- Responsive design
- Interactive elements

**UltimatePipelineApp**
- Modern GUI with CustomTkinter
- Tab-based navigation
- Real-time updates
- Smooth animations

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Reporting Bugs

1. Check existing issues to avoid duplicates
2. Include detailed reproduction steps
3. Provide system information (macOS version, Python version, Xcode version)
4. Include relevant logs and screenshots

### Suggesting Features

1. Open an issue with the `enhancement` label
2. Describe the feature and its benefits
3. Explain your use case
4. Provide mockups if applicable

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/DrazanProjects/ultimate-pipeline.git
cd ultimate-pipeline
pip3 install -r requirements.txt
python3 ultimate_pipeline.py
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints where applicable
- Keep functions focused and modular
- Add docstrings to new functions
- Test on multiple macOS versions

---

## 📋 Requirements

### System Requirements
- **Operating System:** macOS 10.15 or later
- **Python:** 3.8 or higher
- **Xcode:** 14.0 or later
- **Disk Space:** 50 MB for the tool + report storage

### Python Dependencies
- `customtkinter` - Modern GUI framework
- `Pillow` - Image processing (auto-installed by customtkinter)

All dependencies are automatically installed on first run.

### Xcode Requirements
- Xcode Command Line Tools must be installed
- Valid Xcode project or workspace
- At least one configured scheme

---

## ❓ FAQ

**Q: Does this work with SwiftUI projects?**
A: Yes! Ultimate Pipeline works with any Xcode project, including SwiftUI, UIKit, AppKit, and multi-platform projects.

**Q: Can I use this in CI/CD pipelines?**
A: While the GUI is designed for interactive use, the underlying functions can be adapted for headless CI/CD environments.

**Q: Does it support Objective-C projects?**
A: Absolutely! The tool works with Swift, Objective-C, and mixed projects.

**Q: What about CocoaPods or SPM projects?**
A: Full support for both CocoaPods (workspaces) and Swift Package Manager.

**Q: Can I customize the HTML reports?**
A: The reports are generated as standalone HTML files. You can edit them or use the source code to customize the template.

**Q: Does it work with macOS projects?**
A: Yes, but device selection is optimized for iOS. macOS builds work through simulator selection.

---

## 🐛 Troubleshooting

### App won't launch
- Verify Python version: `python3 --version`
- Ensure Xcode is installed: `xcode-select --install`
- Check dependencies: `pip3 install customtkinter`

### Project not detected
- Ensure you're in the project directory
- Check for `.xcodeproj` or `.xcworkspace` files
- Use "Open Project" to manually select the directory

### Build failures
- Verify project builds in Xcode first
- Check selected scheme is valid
- Ensure target device is available
- Review build logs for specific errors

### Tests not running
- Confirm test targets exist in your project
- Check scheme has tests enabled
- Verify simulator/device is booted and ready

### Report generation fails
- Ensure write permissions in project directory
- Check available disk space
- Review console output for specific errors

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Ultimate Pipeline Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🌟 Acknowledgments

- Built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for modern UI
- Inspired by the need for better Xcode developer tools
- Thanks to the open-source community for continuous inspiration

---

## 🔗 Links

- **Repository:** https://github.com/DrazanProjects/ultimate-pipeline
- **Issues:** https://github.com/DrazanProjects/ultimate-pipeline/issues
- **Discussions:** https://github.com/DrazanProjects/ultimate-pipeline/discussions
- **Wiki:** https://github.com/DrazanProjects/ultimate-pipeline/wiki

---

## 📧 Contact

For questions, suggestions, or collaboration:

- **GitHub Issues:** [Create an issue](https://github.com/DrazanProjects/ultimate-pipeline/issues)
- **Discussions:** [Join the conversation](https://github.com/DrazanProjects/ultimate-pipeline/discussions)

---

<div align="center">

### Made with ❤️ by developers, for developers

**Star ⭐ this repo if you find it useful!**

[⬆ Back to Top](#-ultimate-pipeline)

</div>
