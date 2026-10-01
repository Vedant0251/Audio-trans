#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Startup Business Idea Evaluation Tool
====================================
This script evaluates business ideas using Google's Gemini AI and generates
a comprehensive report with scores, verdict, and actionable insights.

Features:
- Evaluates business ideas against 12 key criteria
- Provides GO/WAIT/NO-GO verdict
- Exports results to formatted text file
- Colored console output for better readability

Author: Business Evaluation Assistant
Version: 2.0
"""

import os
import sys

# Force UTF-8 on Windows stdout/stderr so emoji in print() never crash the API
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import json
import datetime
import argparse
from pathlib import Path
from dotenv import load_dotenv
from bmc import choose_model
import google.generativeai as genai

# Optional colored console output
try:
    from termcolor import colored
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    def colored(text, color=None, attrs=None):
        return text


class StartupEvaluator:
    """Main class for evaluating startup business ideas."""
    
    def __init__(self):
        """Initialize the evaluator with API configuration."""
        self.setup_api()
        model_name = choose_model()
        self.model = genai.GenerativeModel(model_name)
        self._safe_print(f"Using model: {model_name}", "cyan")
        self.evaluation_criteria = [
            "MarketNeed", "MarketSize", "ProductFit", "BusinessModel",
            "TeamCredibility", "ExecutionComplexity", "OverallViability",
            "CompetitiveAdvantage", "Scalability", "CustomerAcquisitionPotential",
            "FinancialSustainability", "InnovationLevel"
        ]
    
    def setup_api(self):
        """Load environment variables and configure Gemini API."""
        load_dotenv()
        api_key = os.environ.get("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables. "
                "Please add your Gemini API key to the .env file."
            )
        
        genai.configure(api_key=api_key)
        self._safe_print("API configured", "green")
    
    def _colored_print(self, text, color=None, attrs=None):
        """Helper method for colored printing with safe encoding fallback."""
        try:
            result = colored(text, color) if COLORS_AVAILABLE else text
        except Exception:
            result = text
        return result

    def _safe_print(self, text, color=None):
        """Print with encoding-safe fallback for Windows charmap issues."""
        try:
            print(self._colored_print(text, color))
        except (UnicodeEncodeError, UnicodeDecodeError):
            # Strip non-ASCII chars if stdout still can't handle them
            safe = text.encode("ascii", errors="replace").decode("ascii")
            print(safe)
    
    def load_business_idea(self, file_path):
        """
        Load business idea from text file.
        
        Args:
            file_path (str): Path to the text file containing the business idea
            
        Returns:
            str: Content of the business idea file
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                
            if not content:
                raise ValueError("The business idea file is empty.")
                
            self._safe_print(f"✅ Business idea loaded from: {file_path}", "green")
            return content
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find file: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")
    
    def create_evaluation_prompt(self, idea_text):
        """
        Create the evaluation prompt for the AI model.
        
        Args:
            idea_text (str): The business idea to evaluate
            
        Returns:
            str: Formatted prompt for evaluation
        """
        return f"""
You are an expert startup mentor and investor. Evaluate the following business idea using this comprehensive rubric.

EVALUATION CRITERIA (Score 1-10 for each):
- MarketNeed: How pressing is the problem this solves?
- MarketSize: How large is the target market?
- ProductFit: How well does the solution fit the problem?
- BusinessModel: How viable is the revenue model?
- TeamCredibility: How capable does the team appear?
- ExecutionComplexity: How feasible is implementation?
- OverallViability: Overall business potential
- CompetitiveAdvantage: How differentiated is this solution?
- Scalability: How easily can this business scale?
- CustomerAcquisitionPotential: How easy will it be to acquire customers?
- FinancialSustainability: How sustainable are the financials?
- InnovationLevel: How innovative is this approach?

VERDICT OPTIONS:
- GO: Strong potential, recommend proceeding
- WAIT: Needs refinement before proceeding
- NO-GO: Significant concerns, not recommended

OUTPUT FORMAT (JSON only):
{{
    "scores": {{
        "MarketNeed": <score>,
        "MarketSize": <score>,
        ... (all 12 criteria)
    }},
    "verdict": "<GO/WAIT/NO-GO>",
    "strengths": ["strength1", "strength2", ...],
    "risks": ["risk1", "risk2", ...],
    "suggestions": ["suggestion1", "suggestion2", ...]
}}

Business Idea to Evaluate:
{idea_text}
"""
    
    def evaluate_idea(self, idea_text):
        """
        Send the business idea to Gemini for evaluation.
        
        Args:
            idea_text (str): The business idea to evaluate
            
        Returns:
            dict: Parsed evaluation results
        """
        self._safe_print("🤖 Generating evaluation...", "yellow")
        
        prompt = self.create_evaluation_prompt(idea_text)
        response = self.model.generate_content(prompt)
        raw_output = response.text.strip()
        
        # Clean markdown formatting if present
        if raw_output.startswith("```"):
            raw_output = raw_output.lstrip("```").replace("json", "").strip()
        if raw_output.endswith("```"):
            raw_output = raw_output.rstrip("```").strip()
        
        try:
            parsed_result = json.loads(raw_output)
            normalized = self._normalize_results(parsed_result)
            self._safe_print("✅ Evaluation completed successfully", "green")
            return normalized
            
        except json.JSONDecodeError as e:
            # Attempt to sanitize and recover JSON
            self._safe_print("⚠️ JSON parsing failed. Attempting to sanitize output...", "yellow")
            sanitized = self._attempt_sanitize_json(raw_output)
            try:
                parsed_result = json.loads(sanitized)
                normalized = self._normalize_results(parsed_result)
                self._safe_print("✅ Recovery successful after sanitization", "green")
                return normalized
            except Exception:
                self._safe_print("⚠️ JSON recovery failed. Falling back to raw output.", "red")
                # Return a minimal structure to allow downstream display and saving
                return self._normalize_results({
                    "raw": raw_output,
                    "scores": {},
                    "verdict": "N/A",
                    "strengths": [],
                    "risks": [],
                    "suggestions": []
                })

    def _normalize_results(self, data):
        """Normalize AI results to expected schema to avoid runtime errors."""
        # Ensure dict structure
        if not isinstance(data, dict):
            return {
                "raw": data,
                "scores": {},
                "verdict": "N/A",
                "strengths": [],
                "risks": [],
                "suggestions": []
            }

        # Normalize scores
        scores = data.get("scores", {})
        if isinstance(scores, list):
            converted = {}
            for idx, item in enumerate(scores, start=1):
                if isinstance(item, dict):
                    name = item.get("criterion") or item.get("name") or item.get("key") or f"Metric_{idx}"
                    val = item.get("score") if isinstance(item.get("score"), (int, float)) else item.get("value")
                    try:
                        val_num = float(val) if val is not None else None
                    except Exception:
                        val_num = None
                    if val_num is not None:
                        converted[name] = val_num
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    name = str(item[0])
                    try:
                        val_num = float(item[1])
                    except Exception:
                        val_num = None
                    if val_num is not None:
                        converted[name] = val_num
                else:
                    converted[f"Metric_{idx}"] = 0.0
            data["scores"] = converted
        elif isinstance(scores, dict):
            # Coerce all values to numbers if possible
            clean = {}
            for k, v in scores.items():
                try:
                    clean[k] = float(v)
                except Exception:
                    # Default non-numeric to 0
                    clean[k] = 0.0
            data["scores"] = clean
        else:
            data["scores"] = {}

        # Lists: strengths, risks, suggestions
        for key in ("strengths", "risks", "suggestions"):
            val = data.get(key, [])
            if isinstance(val, list):
                # stringify any non-string items
                data[key] = [str(x) for x in val]
            elif isinstance(val, str):
                data[key] = [val]
            else:
                data[key] = []

        # Verdict default
        if not isinstance(data.get("verdict"), str):
            data["verdict"] = "N/A"

        return data

    def _attempt_sanitize_json(self, raw_output: str) -> str:
        """Try to extract the JSON block and escape problematic characters inside strings.

        - Extract substring between the first '{' and the last '}'
        - Replace unescaped newline characters inside quoted strings with '\\n'
        """
        # Extract JSON block
        start = raw_output.find('{')
        end = raw_output.rfind('}')
        if start == -1 or end == -1 or end <= start:
            return raw_output
        json_block = raw_output[start:end+1]

        # State machine to escape newlines within strings
        result = []
        in_string = False
        quote_char = ''
        escape = False
        for ch in json_block:
            if in_string:
                if escape:
                    # Keep escaped char as-is
                    result.append(ch)
                    escape = False
                    continue
                if ch == '\\':
                    result.append(ch)
                    escape = True
                    continue
                if ch == quote_char:
                    in_string = False
                    quote_char = ''
                    result.append(ch)
                elif ch == '\n' or ch == '\r':
                    # Escape raw newline characters inside strings
                    result.append('\\n')
                else:
                    result.append(ch)
            else:
                if ch in ('"', '\''):
                    in_string = True
                    quote_char = ch
                    result.append(ch)
                else:
                    result.append(ch)
        return ''.join(result)
    
    def display_results(self, evaluation_results):
        """
        Display evaluation results in a formatted console output.
        
        Args:
            evaluation_results (dict): The parsed evaluation results
        """
        print(self._colored_print("\n" + "="*70, "green"))
        print(self._colored_print("🚀 STARTUP EVALUATION REPORT", "green", attrs=['bold']))
        print(self._colored_print("="*70 + "\n", "green"))
        
        # Display scores
        try:
            self._display_scores(evaluation_results.get("scores", {}))
        except Exception as e:
            print(self._colored_print(f"Scores display error: {e}", "red"))
        
        # Display verdict
        try:
            self._display_verdict(evaluation_results.get("verdict", "N/A"))
        except Exception as e:
            print(self._colored_print(f"Verdict display error: {e}", "red"))
        
        # Display detailed sections
        sections = [
            ("strengths", "💪 STRENGTHS", "green"),
            ("risks", "⚠️  RISKS", "red"),
            ("suggestions", "💡 SUGGESTIONS", "blue")
        ]
        
        for key, title, color in sections:
            try:
                self._display_section(
                    evaluation_results.get(key, []), 
                    title, 
                    color
                )
            except Exception as e:
                print(self._colored_print(f"Section '{key}' display error: {e}", "red"))
    
    def _display_scores(self, scores):
        """Display evaluation scores in a formatted table."""
        if not scores or not isinstance(scores, dict):
            print("No scores available")
            return
            
        print(self._colored_print("📊 EVALUATION SCORES:", "cyan", attrs=['bold']))
        print("-" * 70)
        
        # Sort scores by value (highest first)
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        for criterion, score in sorted_scores:
            # Color coding based on score
            if score >= 8:
                color = "green"
            elif score >= 6:
                color = "yellow"
            elif score >= 4:
                color = "yellow"
            else:
                color = "red"
            
            # Format criterion name for better readability
            formatted_criterion = criterion.replace("_", " ").title()
            
            print(f"  {formatted_criterion:<30}: {self._colored_print(f'{score}/10', color, attrs=['bold'])}")
        
        # Calculate and display average
        avg_score = round(sum(scores.values()) / len(scores), 1)
        print("-" * 70)
        print(f"  {'Average Score':<30}: {self._colored_print(f'{avg_score}/10', 'cyan', attrs=['bold'])}")
        print()
    
    def _display_verdict(self, verdict):
        """Display the final verdict with appropriate styling."""
        verdict_colors = {
            "GO": "green",
            "WAIT": "yellow", 
            "NO-GO": "red"
        }
        
        color = verdict_colors.get(verdict, "white")
        print(self._colored_print(f"🎯 FINAL VERDICT: {verdict}", color, attrs=['bold']))
        print("-" * 70)
        print()
    
    def _display_section(self, items, title, color):
        """Display a section (strengths, risks, or suggestions)."""
        print(self._colored_print(title, color, attrs=['bold']))
        print("-" * 70)
        
        if items:
            for i, item in enumerate(items, 1):
                print(f"  {i}. {item}")
        else:
            print("  None identified")
        
        print()
    
    def save_to_file(self, evaluation_results, idea_text, output_dir="evaluations"):
        """
        Save evaluation results to a formatted text file.
        
        Args:
            evaluation_results (dict): The evaluation results
            idea_text (str): The original business idea text
            output_dir (str): Directory to save the output file
            
        Returns:
            str: Path to the saved file
        """
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"startup_evaluation_{timestamp}.txt"
        filepath = Path(output_dir) / filename
        
        # Format content for file
        content = self._format_file_content(evaluation_results, idea_text)
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(self._colored_print(f"💾 Results saved to: {filepath}", "green", attrs=['bold']))
        return str(filepath)
    
    def _format_file_content(self, results, idea_text):
        """Format the evaluation results for file output."""
        content = []
        
        # Header
        content.append("="*80)
        content.append("STARTUP BUSINESS IDEA EVALUATION REPORT")
        content.append("="*80)
        content.append(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append("")
        
        # Original idea
        content.append("BUSINESS IDEA:")
        content.append("-" * 40)
        content.append(idea_text[:500] + "..." if len(idea_text) > 500 else idea_text)
        content.append("")
        
        # Scores
        content.append("EVALUATION SCORES:")
        content.append("-" * 40)
        scores = results.get("scores", {})
        if scores:
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            for criterion, score in sorted_scores:
                formatted_criterion = criterion.replace("_", " ").title()
                content.append(f"{formatted_criterion:<30}: {score}/10")
            
            avg_score = round(sum(scores.values()) / len(scores), 1)
            content.append("-" * 40)
            content.append(f"{'Average Score':<30}: {avg_score}/10")
        content.append("")
        
        # Verdict
        verdict = results.get("verdict", "N/A")
        content.append(f"FINAL VERDICT: {verdict}")
        content.append("=" * 40)
        content.append("")
        
        # Detailed sections
        sections = [
            ("strengths", "STRENGTHS"),
            ("risks", "RISKS"), 
            ("suggestions", "SUGGESTIONS")
        ]
        
        for key, title in sections:
            content.append(f"{title}:")
            content.append("-" * 40)
            items = results.get(key, [])
            if items:
                for i, item in enumerate(items, 1):
                    content.append(f"{i}. {item}")
            else:
                content.append("None identified")
            content.append("")
        
        return "\n".join(content)


def main():
    """Main function to run the startup evaluation or print a file."""
    parser = argparse.ArgumentParser(description="Startup Evaluation and Utility CLI")
    parser.add_argument("--print-file", help="Print the contents of a text file to the terminal and exit")
    parser.add_argument("--idea-file", help="Path to idea text file for evaluation (overrides default)")
    parser.add_argument("--output-file", help="Exact output file path to save the evaluation report")
    parser.add_argument("--model", help="Gemini model id (e.g., models/gemini-2.5-flash)")
    parser.add_argument("--json-only", action="store_true", help="Output and save raw JSON only (no formatted report)")
    args = parser.parse_args()

    # Utility path: print a given file and exit
    if args.print_file:
        try:
            with open(args.print_file, "r", encoding="utf-8") as f:
                content = f.read()
            print("\n" + "="*60)
            print("📄 FILE CONTENTS")
            print("="*60 + "\n")
            print(content)
            return 0
        except Exception as e:
            print(f"❌ Error printing file: {e}")
            return 1

    # Default path: run evaluation flow
    try:
        evaluator = StartupEvaluator()
        # Allow model override from CLI
        if args.model:
            try:
                evaluator.model = genai.GenerativeModel(args.model)
                print(evaluator._colored_print(f"🔧 Using model: {args.model}", "yellow"))
            except Exception as _:
                print(evaluator._colored_print("⚠️ Failed to set custom model; using default.", "yellow"))

        # Configuration (override with --idea-file if provided)
        idea_file_path = args.idea_file or r"C:\Users\RAHIL\Documents\GitHub\CSI_Hackathon\pdf_text\sample_english_1_extracted_20250927_212527.txt"

        # Load business idea
        print("🔄 Loading business idea...")
        idea_text = evaluator.load_business_idea(idea_file_path)

        # Evaluate the idea
        evaluation_results = evaluator.evaluate_idea(idea_text)

        # Debug: show normalized scores structure before display
        try:
            print(f"DEBUG scores type: {type(evaluation_results.get('scores'))}")
            print(f"DEBUG scores content: {evaluation_results.get('scores')}")
        except Exception as _:
            pass

        # Display and save results
        if args.json_only:
            # Print raw JSON
            print("\n" + "="*60)
            print("📊 RAW JSON OUTPUT")
            print("="*60 + "\n")
            print(json.dumps(evaluation_results, indent=2))
        else:
            evaluator.display_results(evaluation_results)

        # Save to desired file path or default directory
        if args.output_file:
            out_path = Path(args.output_file)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            if args.json_only:
                out_path.write_text(json.dumps(evaluation_results, indent=2), encoding="utf-8")
            else:
                formatted = evaluator._format_file_content(evaluation_results, idea_text)
                out_path.write_text(formatted, encoding="utf-8")
            print(evaluator._colored_print(f"\n📝 Saved report to: {out_path}", "green"))
        else:
            output_file = evaluator.save_to_file(evaluation_results, idea_text)
            print(evaluator._colored_print(f"\n🎉 Evaluation complete! Check {output_file} for full report.", "green", attrs=['bold']))

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()