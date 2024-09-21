import io

def generate_markdown(report):
    content = report.content
    markdown = f"""# {content['report_title']}

## Audit Organization
{content['audit_organization']}

## Audit Objectives
{', '.join(content['audit_objectives'])}

## Overall Conclusion
{content['overall_conclusion']}

## Key Findings
{chr(10).join([f"- {finding}" for finding in content['key_findings']])}

## Recommendations
{chr(10).join([f"- {rec}" for rec in content['recommendations']])}

## AI-Generated Insights
{content['llm_insight']}

## Potential Future Audit Objectives
{chr(10).join([f"- {obj}" for obj in content['potential_audit_objectives']])}
"""
    return io.BytesIO(markdown.encode())
