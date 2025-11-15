#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import subprocess
import threading
import json
import re
import os
import sys
import time
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict

try:
    import customtkinter as ctk
except ImportError:
    print("Installing required dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "customtkinter", "Pillow"])
    import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


@dataclass
class ProjectConfig:
    path: str
    name: str
    project_file: str
    scheme: str
    is_workspace: bool
    bundle_id: Optional[str] = None


@dataclass
class TestResult:
    name: str
    status: str
    duration: float


@dataclass
class DiagnosticIssue:
    category: str
    severity: str
    message: str
    file: Optional[str] = None
    line: Optional[int] = None


class XcodeDetector:
    @staticmethod
    def find_project(directory: str) -> Optional[ProjectConfig]:
        path = Path(directory)

        workspaces = list(path.glob("*.xcworkspace"))
        if workspaces:
            workspace = workspaces[0]
            name = workspace.stem
            return ProjectConfig(
                path=directory,
                name=name,
                project_file=workspace.name,
                scheme=XcodeDetector._detect_scheme(directory, workspace.name, True),
                is_workspace=True,
                bundle_id=None
            )

        projects = list(path.glob("*.xcodeproj"))
        if projects:
            project = projects[0]
            name = project.stem
            bundle_id = XcodeDetector._detect_bundle_id(project)
            return ProjectConfig(
                path=directory,
                name=name,
                project_file=project.name,
                scheme=XcodeDetector._detect_scheme(directory, project.name, False),
                is_workspace=False,
                bundle_id=bundle_id
            )

        return None

    @staticmethod
    def _detect_scheme(directory: str, project_file: str, is_workspace: bool) -> str:
        try:
            cmd = ["xcodebuild", "-list"]
            if is_workspace:
                cmd.extend(["-workspace", project_file])
            else:
                cmd.extend(["-project", project_file])

            result = subprocess.run(cmd, cwd=directory, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                lines = result.stdout.split('\n')
                in_schemes = False

                for line in lines:
                    line = line.strip()
                    if "Schemes:" in line:
                        in_schemes = True
                        continue
                    if in_schemes and line and not line.startswith("Build Configurations"):
                        return line

            return Path(project_file).stem
        except Exception:
            return Path(project_file).stem

    @staticmethod
    def _detect_bundle_id(project_path: Path) -> Optional[str]:
        try:
            pbxproj = project_path / "project.pbxproj"
            if pbxproj.exists():
                content = pbxproj.read_text()
                match = re.search(r'PRODUCT_BUNDLE_IDENTIFIER = ([^;]+);', content)
                if match:
                    return match.group(1).strip().strip('"')
        except Exception:
            pass
        return None

    @staticmethod
    def get_simulators() -> List[Dict]:
        try:
            result = subprocess.run(
                ["xcrun", "simctl", "list", "devices", "available", "iOS", "-j"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return []

            data = json.loads(result.stdout)
            simulators = []

            for runtime, devices in data.get("devices", {}).items():
                if "iOS" in runtime:
                    for device in devices:
                        if device.get("isAvailable", False) and "iPhone" in device["name"]:
                            simulators.append({
                                "name": device["name"],
                                "uuid": device["udid"],
                                "state": device.get("state", "Shutdown"),
                                "runtime": runtime.split(".")[-1]
                            })

            return simulators
        except Exception:
            return []

    @staticmethod
    def get_devices() -> List[Dict]:
        try:
            result = subprocess.run(
                ["xcrun", "xctrace", "list", "devices"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return []

            devices = []
            lines = result.stdout.splitlines()
            in_devices = False

            for line in lines:
                line = line.strip()
                if line.startswith("==") and "Devices" in line and "Offline" not in line:
                    in_devices = True
                    continue
                elif line.startswith("=="):
                    in_devices = False
                    continue

                if in_devices and "(" in line and "Simulator" not in line:
                    parts = line.split("(")
                    if len(parts) >= 3:
                        name = parts[0].strip()
                        uuid = parts[-1].replace(")", "").strip()
                        if "-" in uuid and len(uuid) > 20:
                            devices.append({
                                "name": name,
                                "uuid": uuid,
                                "state": "Connected"
                            })

            return devices
        except Exception:
            return []


class CommandRunner:
    @staticmethod
    def run(cmd: List[str], cwd: str, callback=None) -> Tuple[bool, str, str]:
        try:
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            output_lines = []
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                output_lines.append(line)
                if callback:
                    callback(line)

            process.wait()
            output = "".join(output_lines)
            return process.returncode == 0, output, ""
        except Exception as e:
            return False, "", str(e)


class TestParser:
    @staticmethod
    def parse_results(output: str) -> Tuple[List[TestResult], int, int, int]:
        tests = []
        pattern = r"Test Case '(.*?)' (passed|failed) \(([\d.]+) seconds\)"

        for match in re.finditer(pattern, output):
            test_name = match.group(1)
            status = match.group(2)
            duration = float(match.group(3))

            if '.' in test_name:
                parts = test_name.split('.')
                if len(parts) >= 2:
                    test_name = f"{parts[-2]}.{parts[-1]}"

            tests.append(TestResult(
                name=test_name,
                status=status,
                duration=duration
            ))

        summary_pattern = r"Executed (\d+) tests?, with (\d+) failures?"
        summary_match = re.search(summary_pattern, output)

        if summary_match:
            total = int(summary_match.group(1))
            failed = int(summary_match.group(2))
            passed = total - failed
        elif tests:
            total = len(tests)
            passed = sum(1 for t in tests if t.status == "passed")
            failed = sum(1 for t in tests if t.status == "failed")
        else:
            total = passed = failed = 0

        return tests, total, passed, failed


class DiagnosticsEngine:
    @staticmethod
    def analyze_build_output(output: str) -> List[DiagnosticIssue]:
        issues = []

        for line in output.split('\n'):
            if "error:" in line.lower():
                issues.append(DiagnosticIssue(
                    category="Build Error",
                    severity="critical",
                    message=line.strip()
                ))
            elif "warning:" in line.lower():
                issues.append(DiagnosticIssue(
                    category="Build Warning",
                    severity="warning",
                    message=line.strip()
                ))

        return issues

    @staticmethod
    def analyze_source_code(project_path: str) -> List[DiagnosticIssue]:
        issues = []
        path = Path(project_path)
        swift_files = list(path.rglob("*.swift"))

        for swift_file in swift_files:
            try:
                content = swift_file.read_text()

                if "try!" in content or "force try!" in content:
                    issues.append(DiagnosticIssue(
                        category="Code Quality",
                        severity="warning",
                        message=f"Force try detected in {swift_file.name}",
                        file=str(swift_file)
                    ))

                exclamation_count = content.count("!")
                if exclamation_count > 15:
                    issues.append(DiagnosticIssue(
                        category="Code Quality",
                        severity="info",
                        message=f"Excessive force unwrapping in {swift_file.name} ({exclamation_count} instances)",
                        file=str(swift_file)
                    ))

                if "print(" in content and content.count("print(") > 5:
                    issues.append(DiagnosticIssue(
                        category="Code Quality",
                        severity="info",
                        message=f"Multiple debug print statements in {swift_file.name}",
                        file=str(swift_file)
                    ))

                line_count = len(content.split('\n'))
                if line_count > 500:
                    issues.append(DiagnosticIssue(
                        category="Code Quality",
                        severity="info",
                        message=f"Very long file: {swift_file.name} ({line_count} lines)",
                        file=str(swift_file)
                    ))
            except Exception:
                pass

        return issues


class ReportGenerator:
    @staticmethod
    def generate_html(project_config: ProjectConfig, tests: List[TestResult],
                     issues: List[DiagnosticIssue], build_success: bool) -> str:
        passed = sum(1 for t in tests if t.status == "passed")
        failed = sum(1 for t in tests if t.status == "failed")
        total = len(tests)

        critical_issues = sum(1 for i in issues if i.severity == "critical")
        warning_issues = sum(1 for i in issues if i.severity == "warning")
        info_issues = sum(1 for i in issues if i.severity == "info")

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ultimate Pipeline Report - {project_config.name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            min-height: 100vh;
            padding: 40px 20px;
            animation: gradientShift 15s ease infinite;
            background-size: 200% 200%;
        }}

        @keyframes gradientShift {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 30px;
            box-shadow: 0 30px 90px rgba(0, 0, 0, 0.3);
            overflow: hidden;
            animation: slideIn 0.8s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        }}

        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateY(50px) scale(0.9); }}
            to {{ opacity: 1; transform: translateY(0) scale(1); }}
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 60px 40px;
            position: relative;
            overflow: hidden;
        }}

        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 320"><path fill="%23ffffff" fill-opacity="0.1" d="M0,96L48,112C96,128,192,160,288,160C384,160,480,128,576,122.7C672,117,768,139,864,138.7C960,139,1056,117,1152,101.3C1248,85,1344,75,1392,69.3L1440,64L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"></path></svg>');
            background-size: cover;
            animation: wave 20s linear infinite;
        }}

        @keyframes wave {{
            from {{ transform: translateX(0); }}
            to {{ transform: translateX(-50%); }}
        }}

        .header h1 {{
            font-size: 3.5em;
            font-weight: 800;
            margin-bottom: 15px;
            text-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            position: relative;
            z-index: 1;
        }}

        .header .subtitle {{
            font-size: 1.3em;
            opacity: 0.95;
            position: relative;
            z-index: 1;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
            padding: 50px 40px;
            background: linear-gradient(to bottom, #f8f9fa, #ffffff);
        }}

        .stat-card {{
            background: white;
            padding: 35px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
            transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
            position: relative;
            overflow: hidden;
        }}

        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 5px;
            background: linear-gradient(90deg, var(--card-color-1), var(--card-color-2));
        }}

        .stat-card:hover {{
            transform: translateY(-10px) scale(1.02);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
        }}

        .stat-card.success {{
            --card-color-1: #667eea;
            --card-color-2: #764ba2;
        }}

        .stat-card.warning {{
            --card-color-1: #f093fb;
            --card-color-2: #f5576c;
        }}

        .stat-card.info {{
            --card-color-1: #4facfe;
            --card-color-2: #00f2fe;
        }}

        .stat-card h3 {{
            color: #666;
            font-size: 0.95em;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }}

        .stat-card .number {{
            font-size: 3.5em;
            font-weight: 800;
            background: linear-gradient(135deg, var(--card-color-1), var(--card-color-2));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }}

        .stat-card .label {{
            color: #999;
            font-size: 0.9em;
        }}

        .content {{
            padding: 50px 40px;
        }}

        .section {{
            margin-bottom: 50px;
            animation: fadeIn 1s ease;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .section h2 {{
            font-size: 2em;
            margin-bottom: 30px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            display: flex;
            align-items: center;
            gap: 15px;
        }}

        .section h2::before {{
            content: '';
            width: 6px;
            height: 40px;
            background: linear-gradient(180deg, #667eea, #764ba2);
            border-radius: 10px;
        }}

        .test-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
        }}

        .test-item {{
            background: #f8f9fa;
            padding: 20px 25px;
            border-radius: 15px;
            border-left: 5px solid;
            transition: all 0.3s ease;
            cursor: pointer;
        }}

        .test-item:hover {{
            transform: translateX(5px);
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
        }}

        .test-item.passed {{
            border-left-color: #667eea;
            background: linear-gradient(to right, rgba(102, 126, 234, 0.05), transparent);
        }}

        .test-item.failed {{
            border-left-color: #f5576c;
            background: linear-gradient(to right, rgba(245, 87, 108, 0.05), transparent);
        }}

        .test-item .test-name {{
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
            font-size: 0.95em;
        }}

        .test-item .test-meta {{
            display: flex;
            justify-content: space-between;
            color: #666;
            font-size: 0.85em;
        }}

        .badge {{
            display: inline-block;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .badge.success {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }}

        .badge.error {{
            background: linear-gradient(135deg, #f5576c, #f093fb);
            color: white;
        }}

        .badge.warning {{
            background: linear-gradient(135deg, #fbc2eb, #a6c1ee);
            color: #333;
        }}

        .issue-list {{
            list-style: none;
        }}

        .issue-item {{
            background: white;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 12px;
            border-left: 4px solid;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
        }}

        .issue-item:hover {{
            box-shadow: 0 5px 25px rgba(0, 0, 0, 0.1);
            transform: translateX(5px);
        }}

        .issue-item.critical {{
            border-left-color: #f5576c;
        }}

        .issue-item.warning {{
            border-left-color: #fbc2eb;
        }}

        .issue-item.info {{
            border-left-color: #4facfe;
        }}

        .footer {{
            background: linear-gradient(135deg, #2c3e50, #3498db);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .footer p {{
            margin: 10px 0;
            opacity: 0.9;
        }}

        .project-info {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.05);
        }}

        .project-info table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .project-info td {{
            padding: 12px;
            border-bottom: 1px solid #f0f0f0;
        }}

        .project-info td:first-child {{
            font-weight: 600;
            color: #667eea;
            width: 200px;
        }}

        .progress-bar {{
            height: 10px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 20px 0;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
            background-size: 200% 100%;
            animation: progressShine 2s linear infinite;
            transition: width 0.5s ease;
        }}

        @keyframes progressShine {{
            0% {{ background-position: 200% 0; }}
            100% {{ background-position: -200% 0; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Ultimate Pipeline Report</h1>
            <p class="subtitle">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>

        <div class="project-info" style="margin: 30px 40px 0;">
            <h2 style="margin-bottom: 20px; color: #333;">📦 Project Information</h2>
            <table>
                <tr>
                    <td>Project Name</td>
                    <td><strong>{project_config.name}</strong></td>
                </tr>
                <tr>
                    <td>Project Type</td>
                    <td>{'Workspace' if project_config.is_workspace else 'Project'}</td>
                </tr>
                <tr>
                    <td>Scheme</td>
                    <td>{project_config.scheme}</td>
                </tr>
                <tr>
                    <td>Bundle ID</td>
                    <td>{project_config.bundle_id or 'N/A'}</td>
                </tr>
                <tr>
                    <td>Build Status</td>
                    <td><span class="badge {'success' if build_success else 'error'}">{'SUCCESS' if build_success else 'FAILED'}</span></td>
                </tr>
            </table>
        </div>

        <div class="stats-grid">
            <div class="stat-card success">
                <h3>Tests Passed</h3>
                <div class="number">{passed}</div>
                <div class="label">of {total} tests</div>
            </div>
            <div class="stat-card warning">
                <h3>Tests Failed</h3>
                <div class="number">{failed}</div>
                <div class="label">require attention</div>
            </div>
            <div class="stat-card info">
                <h3>Success Rate</h3>
                <div class="number">{(passed/total*100) if total > 0 else 0:.1f}%</div>
                <div class="label">overall performance</div>
            </div>
            <div class="stat-card warning">
                <h3>Issues Found</h3>
                <div class="number">{len(issues)}</div>
                <div class="label">diagnostics</div>
            </div>
        </div>

        <div class="content">
            <div class="section">
                <h2>🧪 Test Results</h2>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {(passed/total*100) if total > 0 else 0}%"></div>
                </div>
                <div class="test-grid">
"""

        for test in tests[:50]:
            status_class = "passed" if test.status == "passed" else "failed"
            status_emoji = "✅" if test.status == "passed" else "❌"
            html += f"""
                    <div class="test-item {status_class}">
                        <div class="test-name">{status_emoji} {test.name}</div>
                        <div class="test-meta">
                            <span class="badge {'success' if test.status == 'passed' else 'error'}">{test.status.upper()}</span>
                            <span>⏱️ {test.duration:.3f}s</span>
                        </div>
                    </div>
"""

        if len(tests) > 50:
            html += f"""
                    <div class="test-item">
                        <div class="test-name">... and {len(tests) - 50} more tests</div>
                    </div>
"""

        html += """
                </div>
            </div>
"""

        if issues:
            html += """
            <div class="section">
                <h2>⚠️ Diagnostic Issues</h2>
                <ul class="issue-list">
"""

            for issue in issues[:100]:
                html += f"""
                    <li class="issue-item {issue.severity}">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>{issue.category}</strong>
                                <p style="margin-top: 8px; color: #666;">{issue.message}</p>
                                {f'<p style="margin-top: 5px; font-size: 0.85em; color: #999;">📄 {issue.file}</p>' if issue.file else ''}
                            </div>
                            <span class="badge {issue.severity}">{issue.severity.upper()}</span>
                        </div>
                    </li>
"""

            if len(issues) > 100:
                html += f"""
                    <li class="issue-item info">
                        <strong>... and {len(issues) - 100} more issues</strong>
                    </li>
"""

            html += """
                </ul>
            </div>
"""

        html += f"""
        </div>

        <div class="footer">
            <p><strong>Ultimate Pipeline Tool</strong></p>
            <p>Comprehensive Xcode Build, Test & Diagnostics Platform</p>
            <p style="margin-top: 15px; opacity: 0.7;">Report generated in {datetime.now().strftime('%Y')}</p>
        </div>
    </div>
</body>
</html>
"""

        return html

    @staticmethod
    def save_report(html: str, project_path: str) -> str:
        reports_dir = Path(project_path) / "pipeline_reports"
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = reports_dir / f"ultimate_pipeline_report_{timestamp}.html"
        report_path.write_text(html)

        return str(report_path)


class AnimatedButton(ctk.CTkButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_color = self.cget("fg_color")
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event=None):
        self.configure(cursor="hand2")

    def _on_leave(self, event=None):
        self.configure(cursor="")


class UltimatePipelineApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Ultimate Pipeline - Xcode Build & Diagnostics")
        self.root.geometry("1400x900")

        self.project_config: Optional[ProjectConfig] = None
        self.selected_target: Optional[Dict] = None
        self.test_results: List[TestResult] = []
        self.diagnostic_issues: List[DiagnosticIssue] = []
        self.build_success = False

        self._setup_ui()
        self._auto_detect_project()

    def _setup_ui(self):
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self.root, height=120, fg_color=("#667eea", "#1a1a2e"))
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_propagate(False)

        title_label = ctk.CTkLabel(
            header,
            text="🚀 Ultimate Pipeline",
            font=ctk.CTkFont(size=42, weight="bold"),
            text_color="white"
        )
        title_label.pack(pady=(20, 5))

        subtitle_label = ctk.CTkLabel(
            header,
            text="Xcode Build • Test • Diagnostics • Deploy",
            font=ctk.CTkFont(size=16),
            text_color=("#e0e0e0", "#b0b0b0")
        )
        subtitle_label.pack()

        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(1, weight=1)

        sidebar = ctk.CTkFrame(main_container, width=280, fg_color=("#f0f0f0", "#2a2a2a"))
        sidebar.grid(row=0, column=0, sticky="ns", padx=(0, 20), pady=0)
        sidebar.grid_propagate(False)

        ctk.CTkLabel(
            sidebar,
            text="📋 Control Panel",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(30, 20), padx=20)

        self.project_label = ctk.CTkLabel(
            sidebar,
            text="No project loaded",
            font=ctk.CTkFont(size=12),
            wraplength=240,
            justify="left"
        )
        self.project_label.pack(pady=(0, 20), padx=20)

        AnimatedButton(
            sidebar,
            text="📁 Open Project",
            command=self._select_project,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#667eea", "#667eea"),
            hover_color=("#764ba2", "#764ba2")
        ).pack(pady=10, padx=20, fill="x")

        AnimatedButton(
            sidebar,
            text="📱 Select Target",
            command=self._select_target,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#f093fb", "#f093fb"),
            hover_color=("#f5576c", "#f5576c")
        ).pack(pady=10, padx=20, fill="x")

        AnimatedButton(
            sidebar,
            text="🔨 Build Project",
            command=self._build_project,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#4facfe", "#4facfe"),
            hover_color=("#00f2fe", "#00f2fe")
        ).pack(pady=10, padx=20, fill="x")

        AnimatedButton(
            sidebar,
            text="🧪 Run Tests",
            command=self._run_tests,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#43e97b", "#43e97b"),
            hover_color=("#38f9d7", "#38f9d7")
        ).pack(pady=10, padx=20, fill="x")

        AnimatedButton(
            sidebar,
            text="🔍 Run Diagnostics",
            command=self._run_diagnostics,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#fa709a", "#fa709a"),
            hover_color=("#fee140", "#fee140")
        ).pack(pady=10, padx=20, fill="x")

        AnimatedButton(
            sidebar,
            text="📊 Generate Report",
            command=self._generate_report,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#30cfd0", "#30cfd0"),
            hover_color=("#330867", "#330867")
        ).pack(pady=10, padx=20, fill="x")

        self.tabview = ctk.CTkTabview(main_container)
        self.tabview.grid(row=0, column=1, sticky="nsew")

        self.tabview.add("Dashboard")
        self.tabview.add("Build Log")
        self.tabview.add("Test Results")
        self.tabview.add("Diagnostics")
        self.tabview.add("Reports")

        self._setup_dashboard_tab()
        self._setup_build_log_tab()
        self._setup_test_results_tab()
        self._setup_diagnostics_tab()
        self._setup_reports_tab()

        status_bar = ctk.CTkFrame(self.root, height=40, fg_color=("#e0e0e0", "#1a1a1a"))
        status_bar.grid(row=2, column=0, sticky="ew", padx=0, pady=0)

        self.status_label = ctk.CTkLabel(
            status_bar,
            text="🎯 Ready",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=20, pady=10)

        self.progress_bar = ctk.CTkProgressBar(status_bar, width=300)
        self.progress_bar.pack(side="right", padx=20, pady=10)
        self.progress_bar.set(0)

    def _setup_dashboard_tab(self):
        tab = self.tabview.tab("Dashboard")

        stats_frame = ctk.CTkFrame(tab, fg_color="transparent")
        stats_frame.pack(fill="both", expand=True, padx=20, pady=20)

        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.build_stat = self._create_stat_card(stats_frame, "🔨 Build", "Not Run", 0, 0)
        self.test_stat = self._create_stat_card(stats_frame, "🧪 Tests", "0 / 0", 0, 1)
        self.pass_stat = self._create_stat_card(stats_frame, "✅ Passed", "0", 0, 2)
        self.issue_stat = self._create_stat_card(stats_frame, "⚠️ Issues", "0", 0, 3)

        welcome_frame = ctk.CTkFrame(tab)
        welcome_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        ctk.CTkLabel(
            welcome_frame,
            text="Welcome to Ultimate Pipeline! 🚀",
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(pady=(40, 20))

        ctk.CTkLabel(
            welcome_frame,
            text="The most advanced Xcode build, test, and diagnostics tool",
            font=ctk.CTkFont(size=16),
            text_color="gray"
        ).pack(pady=(0, 40))

        features_text = """
        ✨ Features:

        • Automatic project detection and configuration
        • Build automation with real-time progress tracking
        • Comprehensive test execution and reporting
        • Deep diagnostics and code quality analysis
        • Beautiful HTML reports with interactive visualizations
        • Support for simulators and physical devices
        • No hardcoded values - works with any project

        Get started by opening a project or let the app auto-detect your current one!
        """

        ctk.CTkLabel(
            welcome_frame,
            text=features_text,
            font=ctk.CTkFont(size=14),
            justify="left"
        ).pack(pady=20, padx=40)

    def _create_stat_card(self, parent, title, value, row, col):
        card = ctk.CTkFrame(parent, fg_color=("#f8f8f8", "#2a2a2a"), corner_radius=15)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 10))

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=("#667eea", "#667eea")
        )
        value_label.pack(pady=(0, 20))

        return value_label

    def _setup_build_log_tab(self):
        tab = self.tabview.tab("Build Log")

        self.build_log = scrolledtext.ScrolledText(
            tab,
            wrap=tk.WORD,
            font=("Monaco", 11),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            relief="flat",
            padx=15,
            pady=15
        )
        self.build_log.pack(fill="both", expand=True, padx=10, pady=10)

    def _setup_test_results_tab(self):
        tab = self.tabview.tab("Test Results")

        self.test_tree = ttk.Treeview(
            tab,
            columns=("Status", "Duration"),
            show="tree headings",
            height=20
        )
        self.test_tree.heading("#0", text="Test Name")
        self.test_tree.heading("Status", text="Status")
        self.test_tree.heading("Duration", text="Duration")

        self.test_tree.column("#0", width=500)
        self.test_tree.column("Status", width=100, anchor="center")
        self.test_tree.column("Duration", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=self.test_tree.yview)
        self.test_tree.configure(yscrollcommand=scrollbar.set)

        self.test_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)

        style = ttk.Style()
        style.configure("Treeview", rowheight=30, font=("Helvetica", 11))
        style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"))

    def _setup_diagnostics_tab(self):
        tab = self.tabview.tab("Diagnostics")

        self.diagnostics_tree = ttk.Treeview(
            tab,
            columns=("Category", "Severity", "File"),
            show="tree headings",
            height=20
        )
        self.diagnostics_tree.heading("#0", text="Message")
        self.diagnostics_tree.heading("Category", text="Category")
        self.diagnostics_tree.heading("Severity", text="Severity")
        self.diagnostics_tree.heading("File", text="File")

        self.diagnostics_tree.column("#0", width=400)
        self.diagnostics_tree.column("Category", width=150)
        self.diagnostics_tree.column("Severity", width=100, anchor="center")
        self.diagnostics_tree.column("File", width=200)

        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=self.diagnostics_tree.yview)
        self.diagnostics_tree.configure(yscrollcommand=scrollbar.set)

        self.diagnostics_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)

    def _setup_reports_tab(self):
        tab = self.tabview.tab("Reports")

        ctk.CTkLabel(
            tab,
            text="📊 Reports Center",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=(30, 20))

        self.report_status = ctk.CTkLabel(
            tab,
            text="No reports generated yet",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        self.report_status.pack(pady=20)

        button_frame = ctk.CTkFrame(tab, fg_color="transparent")
        button_frame.pack(pady=20)

        AnimatedButton(
            button_frame,
            text="📊 Generate HTML Report",
            command=self._generate_report,
            width=250,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=("#667eea", "#667eea"),
            hover_color=("#764ba2", "#764ba2")
        ).pack(pady=10)

        self.open_report_btn = AnimatedButton(
            button_frame,
            text="🌐 Open Latest Report",
            command=self._open_latest_report,
            width=250,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=("#4facfe", "#4facfe"),
            hover_color=("#00f2fe", "#00f2fe"),
            state="disabled"
        )
        self.open_report_btn.pack(pady=10)

        self.last_report_path = None

    def _auto_detect_project(self):
        cwd = os.getcwd()
        self.project_config = XcodeDetector.find_project(cwd)

        if self.project_config:
            self._update_project_display()
            self._log(f"✅ Auto-detected project: {self.project_config.name}")
            self._set_status(f"📦 Project: {self.project_config.name}")
        else:
            self._log("ℹ️ No project found in current directory")
            self._set_status("⚠️ No project detected - please open one")

    def _select_project(self):
        directory = filedialog.askdirectory(title="Select Xcode Project Directory")
        if directory:
            self.project_config = XcodeDetector.find_project(directory)
            if self.project_config:
                os.chdir(directory)
                self._update_project_display()
                self._log(f"✅ Loaded project: {self.project_config.name}")
                self._set_status(f"📦 Project: {self.project_config.name}")
            else:
                messagebox.showerror("Error", "No Xcode project found in selected directory")

    def _update_project_display(self):
        if self.project_config:
            text = f"📦 {self.project_config.name}\n"
            text += f"🎯 {self.project_config.scheme}\n"
            text += f"{'📂 Workspace' if self.project_config.is_workspace else '📄 Project'}"
            self.project_label.configure(text=text)

    def _select_target(self):
        if not self.project_config:
            messagebox.showwarning("Warning", "Please open a project first")
            return

        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Select Target")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="📱 Select Deployment Target",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=20)

        target_type = tk.StringVar(value="simulator")

        type_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        type_frame.pack(pady=10)

        ctk.CTkRadioButton(
            type_frame,
            text="📱 Simulator",
            variable=target_type,
            value="simulator",
            font=ctk.CTkFont(size=14),
            command=lambda: self._update_target_list(listbox, target_type.get())
        ).pack(side="left", padx=20)

        ctk.CTkRadioButton(
            type_frame,
            text="📲 Physical Device",
            variable=target_type,
            value="device",
            font=ctk.CTkFont(size=14),
            command=lambda: self._update_target_list(listbox, target_type.get())
        ).pack(side="left", padx=20)

        listbox_frame = ctk.CTkFrame(dialog)
        listbox_frame.pack(fill="both", expand=True, padx=20, pady=10)

        listbox = tk.Listbox(
            listbox_frame,
            font=("Helvetica", 12),
            height=15,
            relief="flat",
            selectmode=tk.SINGLE,
            bg="#2a2a2a",
            fg="white",
            selectbackground="#667eea",
            selectforeground="white"
        )
        listbox.pack(fill="both", expand=True, padx=5, pady=5)

        self._update_target_list(listbox, "simulator")

        def on_select():
            selection = listbox.curselection()
            if selection:
                idx = selection[0]
                targets = XcodeDetector.get_simulators() if target_type.get() == "simulator" else XcodeDetector.get_devices()
                if idx < len(targets):
                    self.selected_target = targets[idx]
                    self.selected_target["type"] = target_type.get()
                    self._log(f"✅ Selected target: {self.selected_target['name']}")
                    self._set_status(f"📱 Target: {self.selected_target['name']}")
                    dialog.destroy()

        AnimatedButton(
            dialog,
            text="Select",
            command=on_select,
            width=200,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#667eea", "#667eea"),
            hover_color=("#764ba2", "#764ba2")
        ).pack(pady=20)

    def _update_target_list(self, listbox, target_type):
        listbox.delete(0, tk.END)

        if target_type == "simulator":
            targets = XcodeDetector.get_simulators()
            for target in targets:
                status_icon = "🟢" if target["state"] == "Booted" else "⚪"
                listbox.insert(tk.END, f"{status_icon} {target['name']} ({target['runtime']})")
        else:
            targets = XcodeDetector.get_devices()
            for target in targets:
                status_icon = "🟢" if target["state"] == "Connected" else "🔴"
                listbox.insert(tk.END, f"{status_icon} {target['name']}")

    def _build_project(self):
        if not self.project_config:
            messagebox.showwarning("Warning", "Please open a project first")
            return

        if not self.selected_target:
            messagebox.showwarning("Warning", "Please select a target first")
            return

        self._clear_build_log()
        self._set_status("🔨 Building...")
        self.progress_bar.set(0)

        def build_thread():
            cmd = ["xcodebuild", "clean", "build"]

            if self.project_config.is_workspace:
                cmd.extend(["-workspace", self.project_config.project_file])
            else:
                cmd.extend(["-project", self.project_config.project_file])

            cmd.extend([
                "-scheme", self.project_config.scheme,
                "-destination", f"id={self.selected_target['uuid']}"
            ])

            self._log("🔨 Starting build...")
            self._log(f"$ {' '.join(cmd[:5])}...\n")

            success, output, _ = CommandRunner.run(
                cmd,
                self.project_config.path,
                lambda line: self._append_build_log(line)
            )

            self.build_success = success

            if success:
                self._log("\n✅ Build succeeded!")
                self._set_status("✅ Build successful")
                self.build_stat.configure(text="Success", text_color="#43e97b")
            else:
                self._log("\n❌ Build failed!")
                self._set_status("❌ Build failed")
                self.build_stat.configure(text="Failed", text_color="#f5576c")

            self.progress_bar.set(1.0)

            build_issues = DiagnosticsEngine.analyze_build_output(output)
            self.diagnostic_issues.extend(build_issues)
            self._update_diagnostics_display()

        threading.Thread(target=build_thread, daemon=True).start()

    def _run_tests(self):
        if not self.project_config:
            messagebox.showwarning("Warning", "Please open a project first")
            return

        if not self.selected_target:
            messagebox.showwarning("Warning", "Please select a target first")
            return

        self._clear_build_log()
        self._set_status("🧪 Running tests...")
        self.progress_bar.set(0)

        def test_thread():
            cmd = ["xcodebuild", "test"]

            if self.project_config.is_workspace:
                cmd.extend(["-workspace", self.project_config.project_file])
            else:
                cmd.extend(["-project", self.project_config.project_file])

            cmd.extend([
                "-scheme", self.project_config.scheme,
                "-destination", f"id={self.selected_target['uuid']}"
            ])

            self._log("🧪 Starting tests...")
            self._log(f"$ {' '.join(cmd[:5])}...\n")

            success, output, _ = CommandRunner.run(
                cmd,
                self.project_config.path,
                lambda line: self._append_build_log(line)
            )

            tests, total, passed, failed = TestParser.parse_results(output)
            self.test_results = tests

            self._log(f"\n📊 Test Results: {passed} passed, {failed} failed out of {total} total")
            self._set_status(f"🧪 Tests: {passed}/{total} passed")

            self.test_stat.configure(text=f"{passed} / {total}")
            self.pass_stat.configure(text=str(passed))

            self._update_test_display()
            self.progress_bar.set(1.0)

        threading.Thread(target=test_thread, daemon=True).start()

    def _run_diagnostics(self):
        if not self.project_config:
            messagebox.showwarning("Warning", "Please open a project first")
            return

        self._set_status("🔍 Running diagnostics...")
        self.progress_bar.set(0)

        def diagnostics_thread():
            self._log("🔍 Running code quality analysis...")

            code_issues = DiagnosticsEngine.analyze_source_code(self.project_config.path)
            self.diagnostic_issues.extend(code_issues)

            self._log(f"✅ Found {len(code_issues)} code quality issues")
            self._set_status(f"🔍 Diagnostics complete: {len(self.diagnostic_issues)} issues")

            self.issue_stat.configure(text=str(len(self.diagnostic_issues)))
            self._update_diagnostics_display()
            self.progress_bar.set(1.0)

        threading.Thread(target=diagnostics_thread, daemon=True).start()

    def _generate_report(self):
        if not self.project_config:
            messagebox.showwarning("Warning", "Please open a project first")
            return

        self._set_status("📊 Generating report...")

        def report_thread():
            html = ReportGenerator.generate_html(
                self.project_config,
                self.test_results,
                self.diagnostic_issues,
                self.build_success
            )

            report_path = ReportGenerator.save_report(html, self.project_config.path)
            self.last_report_path = report_path

            self._log(f"📊 Report saved: {report_path}")
            self._set_status("✅ Report generated")

            self.root.after(0, lambda: self.report_status.configure(
                text=f"✅ Report saved to:\n{os.path.basename(report_path)}"
            ))
            self.root.after(0, lambda: self.open_report_btn.configure(state="normal"))

            if messagebox.askyesno("Report Generated", "Report generated successfully!\n\nOpen in browser?"):
                webbrowser.open(f"file://{report_path}")

        threading.Thread(target=report_thread, daemon=True).start()

    def _open_latest_report(self):
        if self.last_report_path and os.path.exists(self.last_report_path):
            webbrowser.open(f"file://{self.last_report_path}")
        else:
            messagebox.showwarning("Warning", "No report available")

    def _update_test_display(self):
        for item in self.test_tree.get_children():
            self.test_tree.delete(item)

        for test in self.test_results:
            status_emoji = "✅" if test.status == "passed" else "❌"
            status_text = f"{status_emoji} {test.status.upper()}"
            duration_text = f"{test.duration:.3f}s"

            self.test_tree.insert(
                "",
                "end",
                text=test.name,
                values=(status_text, duration_text)
            )

    def _update_diagnostics_display(self):
        for item in self.diagnostics_tree.get_children():
            self.diagnostics_tree.delete(item)

        for issue in self.diagnostic_issues:
            severity_emoji = {
                "critical": "🔴",
                "warning": "🟡",
                "info": "🔵"
            }.get(issue.severity, "⚪")

            severity_text = f"{severity_emoji} {issue.severity.upper()}"
            file_name = os.path.basename(issue.file) if issue.file else "N/A"

            self.diagnostics_tree.insert(
                "",
                "end",
                text=issue.message[:100],
                values=(issue.category, severity_text, file_name)
            )

    def _log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.root.after(0, lambda: self._append_build_log(log_message))

    def _append_build_log(self, text):
        self.build_log.insert(tk.END, text)
        self.build_log.see(tk.END)
        self.root.update_idletasks()

    def _clear_build_log(self):
        self.build_log.delete(1.0, tk.END)

    def _set_status(self, text):
        self.root.after(0, lambda: self.status_label.configure(text=text))

    def run(self):
        self.root.mainloop()


def main():
    app = UltimatePipelineApp()
    app.run()


if __name__ == "__main__":
    main()
