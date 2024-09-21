import os
import json
from openai import OpenAI

client = OpenAI()

def analyze_report(content):
    prompt = f"""
    Analyze the following audit report content and extract key information:
    {content[:4000]}  # Limiting to 4000 characters to avoid token limit

    Please provide the following information:
    1. Report title
    2. Audit organization
    3. Audit objectives (list)
    4. Overall conclusion
    5. Key findings (list)
    6. Recommendations (list)
    7. Insights based on the report content
    8. Potential audit objectives for future audits (list)

    Format the response as a JSON object with the following keys:
    report_title, audit_organization, audit_objectives, overall_conclusion, key_findings, recommendations, llm_insight, potential_audit_objectives
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )
        
        result = response.choices[0].message.content
        
        # Parse the JSON response
        parsed_result = json.loads(result)
        
        # Validate the parsed result
        required_keys = [
            "report_title", "audit_organization", "audit_objectives",
            "overall_conclusion", "key_findings", "recommendations",
            "llm_insight", "potential_audit_objectives"
        ]
        for key in required_keys:
            if key not in parsed_result:
                raise ValueError(f"Missing required key in API response: {key}")
        
        return parsed_result

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return None
    except ValueError as e:
        print(f"Error in API response format: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
