import os
import json
import logging
import time
from openai import OpenAI, RateLimitError, APIError, APITimeoutError
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT, RateLimitError as AnthropicRateLimitError, APIError as AnthropicAPIError

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
anthropic = Anthropic(api_key=os.environ.get("CLAUDE_API_KEY"))
logging.basicConfig(level=logging.INFO)

def analyze_report_with_claude(content):
    prompt = f"""
    Analyze the following audit report content and extract key information:
    {content[:4000]}  # Limiting to 4000 characters to avoid token limit

    Please provide the following information in a structured JSON format:
    1. "report_title": The title of the audit report
    2. "audit_organization": The organization that conducted the audit
    3. "audit_objectives": A list of the main objectives of the audit
    4. "overall_conclusion": The overall conclusion or summary of the audit findings
    5. "key_findings": A list of the main findings from the audit
    6. "recommendations": A list of recommendations based on the audit findings
    7. "llm_insight": Your insights or analysis based on the report content
    8. "potential_audit_objectives": A list of potential objectives for future audits based on this report

    Ensure your response is a valid JSON object with these exact keys and nothing else.
    If you're unsure about any field, use "N/A" for string fields or an empty list for list fields.
    """

    max_retries = 3
    base_delay = 1

    for attempt in range(max_retries):
        try:
            logging.info(f"Attempt {attempt + 1} to analyze report with Claude")
            response = anthropic.completions.create(
                model="claude-2.1",
                prompt=f"{HUMAN_PROMPT} {prompt} {AI_PROMPT}",
                max_tokens_to_sample=4096,
            )

            result = response.completion.strip()
            logging.info(f"Claude API raw response: {result}")
            
            try:
                parsed_result = json.loads(result)
            except json.JSONDecodeError:
                logging.warning("JSON parsing failed. Falling back to text extraction.")
                parsed_result = extract_structured_data(result)

            sanitized_result = sanitize_result(parsed_result)

            return {"success": True, "data": sanitized_result}

        except AnthropicRateLimitError as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                logging.warning(f"Claude rate limit reached. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error(f"Claude rate limit error after {max_retries} attempts: {e}")
                return {
                    "success": False,
                    "error": "We're experiencing high demand. Please try again in a few minutes."
                }

        except AnthropicAPIError as e:
            logging.error(f"Claude API error: {e}")
            return {
                "success": False,
                "error": "An error occurred while processing your request. Please try again later."
            }

        except Exception as e:
            logging.error(f"An unexpected error occurred with Claude: {e}")
            return {
                "success": False,
                "error": f"An unexpected error occurred: {str(e)}. Please try again or contact support."
            }

    return {
        "success": False,
        "error": "Unable to process the report after multiple attempts. Please try again later."
    }

def analyze_report_with_gpt4(content):
    prompt = f"""
    Analyze the following audit report content and extract key information:
    {content[:4096]}  # Limiting to 4096 characters to avoid token limit

    Please provide the following information in a valid JSON format:
    1. "report_title": The title of the audit report
    2. "audit_organization": The organization that conducted the audit
    3. "audit_objectives": A list of the main objectives of the audit
    4. "overall_conclusion": The overall conclusion or summary of the audit findings
    5. "key_findings": A list of the main findings from the audit
    6. "recommendations": A list of recommendations based on the audit findings
    7. "llm_insight": Your insights or analysis based on the report content
    8. "potential_audit_objectives": A list of potential objectives for future audits based on this report

    Ensure your response is a valid JSON object with these exact keys and nothing else.
    If you're unsure about any field, use "N/A" for string fields or an empty list for list fields.
    """

    max_retries = 3
    base_delay = 1

    for attempt in range(max_retries):
        try:
            logging.info(f"Attempt {attempt + 1} to analyze report with GPT-4o-mini")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096
            )

            result = response.choices[0].message.content.strip()
            logging.info(f"OpenAI API Response: {result}")

            try:
                json_start = result.index('{')
                json_end = result.rindex('}') + 1
                json_str = result[json_start:json_end]
                parsed_result = json.loads(json_str)
            except (ValueError, json.JSONDecodeError) as json_error:
                logging.error(f"JSON parsing failed: {json_error}. Raw response: {result}")
                parsed_result = extract_structured_data(result)

            sanitized_result = sanitize_result(parsed_result)

            return {"success": True, "data": sanitized_result}

        except RateLimitError as e:
            logging.error(f"OpenAI API rate limit error: {e}")
            if "insufficient_quota" in str(e):
                return {
                    "success": False,
                    "error": "We're currently experiencing high demand. Please try again later or contact support."
                }
            elif attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                logging.warning(f"Rate limit reached. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                return {
                    "success": False,
                    "error": "We're experiencing temporary issues. Please try again in a few minutes."
                }

        except (APIError, APITimeoutError) as e:
            logging.error(f"OpenAI API error or timeout: {e}")
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                logging.warning(f"API error or timeout. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                return {
                    "success": False,
                    "error": "We're experiencing temporary issues. Please try again in a few minutes."
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

def extract_structured_data(text):
    data = {
        "report_title": "N/A",
        "audit_organization": "N/A",
        "audit_objectives": [],
        "overall_conclusion": "N/A",
        "key_findings": [],
        "recommendations": [],
        "llm_insight": "N/A",
        "potential_audit_objectives": []
    }

    lines = text.split('\n')
    current_key = None

    for line in lines:
        line = line.strip()
        if line.startswith(('report_title:', 'audit_organization:', 'overall_conclusion:', 'llm_insight:')):
            key, value = line.split(':', 1)
            data[key.strip()] = value.strip()
        elif line.startswith(('audit_objectives:', 'key_findings:', 'recommendations:', 'potential_audit_objectives:')):
            current_key = line.split(':')[0].strip()
        elif current_key and line.startswith('-'):
            data[current_key].append(line[1:].strip())

    return data

def sanitize_result(result):
    required_keys = [
        "report_title", "audit_organization", "audit_objectives",
        "overall_conclusion", "key_findings", "recommendations",
        "llm_insight", "potential_audit_objectives"
    ]

    sanitized = {}
    for key in required_keys:
        if key in result:
            value = result[key]
            if isinstance(value, str):
                sanitized[key] = value.strip().rstrip(',').strip('"')
            elif isinstance(value, list):
                sanitized[key] = [item.strip().rstrip(',').strip('"') for item in value if item.strip()]
            else:
                sanitized[key] = value
        else:
            sanitized[key] = "N/A" if key in ["report_title", "audit_organization", "overall_conclusion", "llm_insight"] else []

    return sanitized

def analyze_report(content, ai_model='gpt-4o-mini'):
    if ai_model == 'claude-sonnet':
        return analyze_report_with_claude(content)
    else:
        return analyze_report_with_gpt4(content)