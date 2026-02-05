"""
Output Formatter for Workflow Execution Results
Formats workflow execution outputs in a human-readable format
"""
import re
from typing import Dict, Any, List


class OutputFormatter:
    """Formats workflow execution results into readable text format"""
    
    @staticmethod
    def format_execution_result(output: Dict[str, Any], metrics: Dict[str, Any]) -> str:
        """
        Format the execution result into a human-readable format.
        
        Args:
            output: The output dictionary containing final and all_steps
            metrics: The metrics dictionary with execution metadata
            
        Returns:
            Formatted string with readable output and metrics
        """
        formatted_parts = []
        
        # Format the main output
        if output and "all_steps" in output:
            for idx, step in enumerate(output["all_steps"], 1):
                if step and "output" in step:
                    step_output = step["output"]
                    formatted_step = OutputFormatter._format_step_output(step_output, idx)
                    if formatted_step:
                        formatted_parts.append(formatted_step)
        
        # Join all step outputs
        main_content = "\n\n".join(formatted_parts)
        
        # Format metrics at the bottom
        metrics_section = OutputFormatter._format_metrics(metrics)
        
        # Combine everything
        if main_content and metrics_section:
            return f"{main_content}\n\n{metrics_section}"
        elif main_content:
            return main_content
        elif metrics_section:
            return metrics_section
        else:
            return "No output generated"
    
    @staticmethod
    def _format_step_output(output: str, step_number: int = None) -> str:
        """
        Format a single step output by parsing markdown-style bullet points.
        
        Args:
            output: The raw output text from the step
            step_number: Optional step number for labeling
            
        Returns:
            Formatted text with proper structure
        """
        if not output or not isinstance(output, str):
            return ""
        
        # Remove excessive whitespace and newlines
        output = output.strip()
        
        # Parse markdown-style bullet points with bold headers (e.g., "* **1. Title:**")
        # Pattern: * **Number. Title:** Content
        pattern = r'\*\s+\*\*(\d+)\.\s+([^:*]+):\*\*\s+([^\n]+(?:\n(?!\*\s+\*\*)[^\n]+)*)'
        matches = re.findall(pattern, output, re.MULTILINE)
        
        if matches:
            # Format as numbered sections with bullet points
            formatted_sections = []
            for num, title, content in matches:
                # Clean up the title and content
                title = title.strip()
                content = content.strip()
                
                # Split content into sentences/points
                points = re.split(r'\.\s+(?=[A-Z])', content)
                points = [p.strip() for p in points if p.strip()]
                
                # Format the section
                section = f"{num}. {title}\n\n"
                for point in points:
                    # Clean up the point
                    point = point.strip()
                    if point and not point.endswith('.'):
                        point += "."
                    section += f"   • {point}\n"
                
                formatted_sections.append(section)
            
            return "\n".join(formatted_sections)
        
        # If no structured format found, try simpler bullet point parsing
        lines = output.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Convert markdown bullets to simple bullets
            if line.startswith('*') or line.startswith('-'):
                line = '• ' + line.lstrip('*-').strip()
            elif line.startswith('•'):
                line = '• ' + line.lstrip('•').strip()
            
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    @staticmethod
    def _format_metrics(metrics: Dict[str, Any]) -> str:
        """
        Format metrics section at the bottom.
        
        Args:
            metrics: Dictionary containing execution metrics
            
        Returns:
            Formatted metrics string
        """
        if not metrics:
            return ""
        
        # Extract metrics with defaults
        total_tokens = metrics.get("total_tokens", 0)
        duration = metrics.get("duration_seconds", 0)
        provider = metrics.get("provider", "unknown")
        iterations = metrics.get("iterations", 0)
        steps_executed = metrics.get("steps_executed", 0)
        
        # Calculate approximate input/output tokens (rough estimate: 40% input, 60% output)
        input_tokens = int(total_tokens * 0.4)
        output_tokens = total_tokens - input_tokens
        
        # Format the metrics section
        separator = "─" * 60
        metrics_text = f"""
{separator}

📊 Execution Summary

   • Input Tokens:        {input_tokens:,}
   • Output Tokens:       {output_tokens:,}
   • Total Tokens:        {total_tokens:,}
   • Provider:            {provider.title()}
   • Iterations:          {iterations}
   • Steps Executed:      {steps_executed}
   • Completion Time:     {duration:.2f} seconds

{separator}
"""
        return metrics_text.strip()
    
    @staticmethod
    def format_json_with_readable_output(
        output: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Return both JSON structure and formatted readable output.
        
        Args:
            output: The output dictionary
            metrics: The metrics dictionary
            
        Returns:
            Dictionary with both json and formatted_output keys
        """
        return {
            "json": {
                "final": output.get("final"),
                "all_steps": output.get("all_steps"),
                "_metrics": metrics
            },
            "formatted_output": OutputFormatter.format_execution_result(output, metrics)
        }
