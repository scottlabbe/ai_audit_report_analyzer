import os
import json
import logging
import time
import re
from openai import OpenAI, RateLimitError, APIError, APITimeoutError
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT, RateLimitError as AnthropicRateLimitError, APIError as AnthropicAPIError

client = OpenAI()
anthropic = Anthropic(api_key=os.environ.get("CLAUDE_API_KEY"))
logging.basicConfig(level=logging.INFO)

def extract_info_from_text(text):
    extracted_info = {
        "report_title": "N/A",
        "audit_organization": "N/A",
        "audit_objectives": [],
        "overall_conclusion": "N/A",
        "key_findings": [],
        "recommendations": [],
        "llm_insight": "N/A",
        "potential_audit_objectives": []
    }
    
    title_match = re.search(r"Report title:?\s*(.+)", text, re.IGNORECASE)
    if title_match:
        extracted_info["report_title"] = title_match.group(1).strip()
    
    org_match = re.search(r"Audit organization:?\s*(.+)", text, re.IGNORECASE)
    if org_match:
        extracted_info["audit_organization"] = org_match.group(1).strip()
    
    objectives_match = re.search(r"Audit objectives:?\s*(.+?)(?:\n\d\.|\n\n)", text, re.IGNORECASE | re.DOTALL)
    if objectives_match:
        objectives = objectives_match.group(1).strip().split('\n')
        extracted_info["audit_objectives"] = [obj.strip('- ') for obj in objectives if obj.strip()]
    
    conclusion_match = re.search(r"Overall conclusion:?\s*(.+?)(?:\n\d\.|\n\n)", text, re.IGNORECASE | re.DOTALL)
    if conclusion_match:
        extracted_info["overall_conclusion"] = conclusion_match.group(1).strip()
    
    findings_match = re.search(r"Key findings:?\s*(.+?)(?:\n\d\.|\n\n)", text, re.IGNORECASE | re.DOTALL)
    if findings_match:
        findings = findings_match.group(1).strip().split('\n')
        extracted_info["key_findings"] = [finding.strip('- ') for finding in findings if finding.strip()]
    
    recommendations_match = re.search(r"Recommendations:?\s*(.+?)(?:\n\d\.|\n\n)", text, re.IGNORECASE | re.DOTALL)
    if recommendations_match:
        recommendations = recommendations_match.group(1).strip().split('\n')
        extracted_info["recommendations"] = [rec.strip('- ') for rec in recommendations if rec.strip()]
    
    insight_match = re.search(r"Insights based on the report content:?\s*(.+?)(?:\n\d\.|\n\n)", text, re.IGNORECASE | re.DOTALL)
    if insight_match:
        extracted_info["llm_insight"] = insight_match.group(1).strip()
    
    potential_objectives_match = re.search(r"Potential audit objectives for future audits:?\s*(.+?)(?:\n\d\.|\n\n|$)", text, re.IGNORECASE | re.DOTALL)
    if potential_objectives_match:
        potential_objectives = potential_objectives_match.group(1).strip().split('\n')
        extracted_info["potential_audit_objectives"] = [obj.strip('- ') for obj in potential_objectives if obj.strip()]
    
    return extracted_info

def analyze_report_with_claude(content):
    prompt = f"""
    Analyze the following audit report content and extract key information:
    {content[:4096]}  # Limiting to 4000 characters to avoid token limit

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

    Ensure your response is a valid JSON object and nothing else.
    """

    max_retries = 3
    base_delay = 1

    for attempt in range(max_retries):
        try:
            response = anthropic.completions.create(
                model="claude-2.0",
                prompt=f"{HUMAN_PROMPT} {prompt} {AI_PROMPT}",
                max_tokens_to_sample=4096,
            )

            result = response.completion.strip()
            
            try:
                parsed_result = json.loads(result)
            except json.JSONDecodeError:
                parsed_result = extract_info_from_text(result)

            logging.info(f"Claude API Response (parsed): {parsed_result}")

            required_keys = [
                "report_title", "audit_organization", "audit_objectives",
                "overall_conclusion", "key_findings", "recommendations",
                "llm_insight", "potential_audit_objectives"
            ]
            for key in required_keys:
                if key not in parsed_result:
                    raise ValueError(f"Missing required key in Claude API response: {key}")

            return {"success": True, "data": parsed_result}

        except AnthropicRateLimitError as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                logging.warning(f"Claude rate limit reached. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error(f"Claude rate limit error after {max_retries} attempts: {e}")
                return {
                    "success": False,
                    "error": "We're experiencing temporary issues. Please try again in a few minutes."
                }

        except AnthropicAPIError as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                logging.warning(f"Claude API error. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error(f"Claude API error after {max_retries} attempts: {e}")
                return {
                    "success": False,
                    "error": "We're experiencing temporary issues. Please try again in a few minutes."
                }

        except ValueError as e:
            logging.error(f"Error in Claude API response format: {e}")
            return {
                "success": False,
                "error": "Error processing the report. Please try again or contact support."
            }

        except Exception as e:
            logging.error(f"An unexpected error occurred with Claude: {e}")
            return {
                "success": False,
                "error": "An unexpected error occurred while processing the report. Please try again or contact support."
            }

    return {
        "success": False,
        "error": "Unable to process the report after multiple attempts. Please try again later."
    }

def analyze_report_with_gpt4(content):
    prompt = f"""
    Analyze the following audit report content and extract key information:
    {content[:4096]}  # Limiting to 4000 characters to avoid token limit

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

    max_retries = 3
    base_delay = 1

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096
            )

            result = response.choices[0].message.content
            logging.info(f"OpenAI API Response: {result}")

            try:
                parsed_result = json.loads(result)
            except json.JSONDecodeError:
                parsed_result = extract_info_from_text(result)

            required_keys = [
                "report_title", "audit_organization", "audit_objectives",
                "overall_conclusion", "key_findings", "recommendations",
                "llm_insight", "potential_audit_objectives"
            ]
            for key in required_keys:
                if key not in parsed_result:
                    raise ValueError(f"Missing required key in API response: {key}")

            return {"success": True, "data": parsed_result}

        except RateLimitError as e:
            if "insufficient_quota" in str(e):
                logging.error("OpenAI API quota exceeded. Unable to process the report.")
                return {
                    "success": False,
                    "error": "We're currently experiencing high demand. Please try again later or contact support."
                }
            elif attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                logging.warning(f"Rate limit reached. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error(f"Rate limit error after {max_retries} attempts: {e}")
                return {
                    "success": False,
                    "error": "We're experiencing temporary issues. Please try again in a few minutes."
                }

        except (APIError, APITimeoutError) as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                logging.warning(f"API error or timeout. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error(f"API error or timeout after {max_retries} attempts: {e}")
                return {
                    "success": False,
                    "error": "We're experiencing temporary issues. Please try again in a few minutes."
                }

        except ValueError as e:
            logging.error(f"Error in API response format: {e}")
            return {
                "success": False,
                "error": "Error processing the report. Please try again or contact support."
            }

        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return {
                "success": False,
                "error": "An unexpected error occurred. Please try again or contact support."
            }

    return {
        "success": False,
        "error": "Unable to process the report after multiple attempts. Please try again later."
    }

def analyze_report(content, ai_model='gpt-4'):
    if ai_model == 'claude-sonnet':
        return analyze_report_with_claude(content)
    else:
        return analyze_report_with_gpt4(content)