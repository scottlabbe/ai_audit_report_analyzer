import os
import json
import logging
import time
from openai import OpenAI, RateLimitError, APIError, APITimeoutError
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT, RateLimitError as AnthropicRateLimitError, APIError as AnthropicAPIError

client = OpenAI()
anthropic = Anthropic(api_key=os.environ.get("CLAUDE_API_KEY"))
logging.basicConfig(level=logging.INFO)

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

            result = response.completion
            logging.info(f"Claude API Response: {result}")

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
                    raise ValueError(
                        f"Missing required key in Claude API response: {key}")

            return {"success": True, "data": parsed_result}

        except AnthropicRateLimitError as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                logging.warning(
                    f"Claude rate limit reached. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error(
                    f"Claude rate limit error after {max_retries} attempts: {e}")
                return {
                    "success": False,
                    "error": "We're experiencing temporary issues. Please try again in a few minutes."
                }

        except AnthropicAPIError as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                logging.warning(
                    f"Claude API error. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error(
                    f"Claude API error after {max_retries} attempts: {e}")
                return {
                    "success": False,
                    "error": "We're experiencing temporary issues. Please try again in a few minutes."
                }

        except json.JSONDecodeError as e:
            logging.error(f"Error parsing JSON response from Claude: {e}")
            logging.error(f"Raw response: {result}")
            return {
                "success": False,
                "error": "Error processing the report. Please try again or contact support."
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
                "error": "An unexpected error occurred. Please try again or contact support."
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
                    raise ValueError(
                        f"Missing required key in API response: {key}")

            return {"success": True, "data": parsed_result}

        except RateLimitError as e:
            if "insufficient_quota" in str(e):
                logging.error(
                    "OpenAI API quota exceeded. Unable to process the report.")
                return {
                    "success": False,
                    "error": "We're currently experiencing high demand. Please try again later or contact support."
                }
            elif attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                logging.warning(
                    f"Rate limit reached. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error(
                    f"Rate limit error after {max_retries} attempts: {e}")
                return {
                    "success": False,
                    "error": "We're experiencing temporary issues. Please try again in a few minutes."
                }

        except (APIError, APITimeoutError) as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                logging.warning(
                    f"API error or timeout. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error(
                    f"API error or timeout after {max_retries} attempts: {e}")
                return {
                    "success": False,
                    "error": "We're experiencing temporary issues. Please try again in a few minutes."
                }

        except json.JSONDecodeError as e:
            logging.error(f"Error parsing JSON response: {e}")
            logging.error(f"Raw response: {result}")
            return {
                "success": False,
                "error": "Error processing the report. Please try again or contact support."
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
