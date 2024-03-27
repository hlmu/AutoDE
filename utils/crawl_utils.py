from functools import partial
import re
import time
import traceback
import json

import openai
import requests
from tenacity import retry, stop_after_attempt, wait_random_exponential
import tenacity

from utils.ssl_utils import no_ssl_verification
from utils.utils import CLAUDE_PROXY_INFO, CLAUDE_PROXY_KEY, OPENAI_INFO
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

OPENAI_INFO.update({
	v["model"]:v for k,v in OPENAI_INFO.items() if "model" in v
})

class KeyManager:
	def __init__(self):
		self.key_pool = {}
		self.is_single_key = False

	def get_key(self, model, no_pool=False):
		if model in OPENAI_INFO:
			if no_pool or "api_key_list" not in OPENAI_INFO[model]:
				self.is_single_key = True
				return OPENAI_INFO[model]["api_key"]

			if model not in self.key_pool:
				self.key_pool[model] = OPENAI_INFO[model]["api_key_list"]
			if len(self.key_pool[model]) == 0:
				raise ValueError("Key pool is empty.")
			key = self.key_pool[model].pop(0)
			self.key_pool[model].append(key)
			return key
		else:
			print(model)
			raise NotImplementedError
	
	def delete_key(self, model, key):
		if model in self.key_pool:
			if self.is_single_key:
				return
			self.key_pool[model].remove(key)
		else:
			raise ValueError

key_manager = KeyManager()


def get_agent(agent, url=None):
	chat_completion = None
	if "gpt" in agent:
		import openai
		openai_info = OPENAI_INFO[agent]
		openai.api_key = openai_info["api_key"]
		if "azure" in agent:
			print("Using azure api")
			openai.api_base = openai_info["api_base"]
			openai.api_version = openai_info["api_version"]
			openai.api_type = openai_info["api_type"]

		chat_completion = partial(openai_chat_completion_wrapper, agent)
	elif "llama" in agent or "zephyr" in agent or "mistral" in agent:
		chat_completion = partial(llama_chat_completion_wrapper, url)
	elif "claude" in agent:
		chat_completion = partial(claude_chat_completion_PROXY_wrapper, CLAUDE_PROXY_INFO[agent]["model"])
	else:
		raise NotImplementedError
	return chat_completion


@retry(wait=wait_random_exponential(min=60, max=120), stop=stop_after_attempt(6))
def chat_completion_with_backoff(**kwargs):
    response = openai.ChatCompletion.create(**kwargs)
    return response

def openai_chat_completion_wrapper(*args, **kwargs):
	result = {}
	response_message = openai_chat_completion(*args, **kwargs)
	if response_message.get("function_call"):
		result = {
			"arguments": response_message["function_call"]["arguments"]
		}
	else:
		if "[DONE]" in response_message["content"]:
			msg = response_message["content"].replace("[DONE]", "").strip()
			result = {
				"end": True,
				"content": msg
			}
		else:
			result = {
				"content": response_message["content"]
			}
	return result

def extract_func_content(text):
    pattern = r'<func>(.*?)</func>'
    matches = re.findall(pattern, text, re.DOTALL)
    return matches

def claude_chat_completion_PROXY_wrapper(model, messages, functions=None, function_call=None, sleep=5, *args, **kwargs):
	url = ""
	headers = {
		"Authorization": CLAUDE_PROXY_KEY,
		"content-type": "application/json"
	}

	if function_call is not None and function_call != "auto" and not isinstance(function_call, dict):
		raise NotImplementedError
	if isinstance(function_call, dict):
		assert messages[-1]["role"] == "user"
		messages[-1]["content"] += "\n\nSUBMIT API"
	if functions is not None:
		messages[0]["content"] = messages[0]["content"].replace("{{api_doc}}", json.dumps(functions[0], ensure_ascii=False))

	data = {
		"messages": messages,
		"model": model,
		"max_tokens_to_sample": 8192,
	}

	success_flag = False
	max_retry = 5
	retries = 0
	while not success_flag and retries <= max_retry:
		try:
			response = requests.post(url, headers=headers, json=data)
			response_message = response.json()["choices"][0]["message"]
			success_flag = True
			time.sleep(sleep)
		except ValueError:
			traceback.print_exc()
			retries += 1
			print("Retrying...")
			time.sleep(60)
			continue
		except KeyError:
			traceback.print_exc()
			raise KeyError(response.json())
		if retries > max_retry:
			raise Exception("OpenAI API failed after 5 retries.")

	result = {}
	if "<func>" in response_message["content"]:
		api_call_str = extract_func_content(response_message["content"])[0].strip()
		result = {
			"arguments": api_call_str
		}
	else:
		if "[DONE]" in response_message["content"]:
			msg = response_message["content"].replace("[DONE]", "").strip()
			result = {
				"end": True,
				"content": msg
			}
		else:
			result = {
				"content": response_message["content"]
			}
	return result

def openai_chat_completion(model, messages, functions=None, function_call=None, sleep=5):
	success_flag = False
	max_retry = 5
	retries = 0
	while not success_flag and retries <= max_retry:
		try:
			key = key_manager.get_key(model)
			model_info = OPENAI_INFO[model]
			model_param = {}
			if "engine" in model_info:
				model_param["engine"] = model_info["engine"]
			elif "deployment_id" in model_info:
				model_param["deployment_id"] = model_info["deployment_id"]
			elif "model" in model_info:
				model_param["model"] = model_info["model"]
			else:
				raise NotImplementedError
			with no_ssl_verification():
				if functions is not None:
					response = chat_completion_with_backoff(
						messages=messages,
						functions=functions,
						function_call=function_call,  # auto is default, but we'll be explicit
						# function_call={"name": function['name']},  # auto is default, but we'll be explicit
						api_key=key,
						**model_param,
					)
				else:
					response = chat_completion_with_backoff(
						model=model,
						messages=messages,
						api_key=key,
						**model_param,
					)

			response_message = response["choices"][0]["message"]
			success_flag = True
			time.sleep(sleep)
		except KeyError as e:
			traceback.print_exc()
			retries += 1
			print("Retrying...")
			time.sleep(60)
			continue
		except tenacity.RetryError as e:
			traceback.print_exc()
			retries += 1
			print("Change key retrying...")
			key_manager.delete_key(model, key)
	if retries > max_retry:
		raise Exception("OpenAI API failed after 5 retries.")
	return response_message

def llama_chat_completion_wrapper(url, messages, functions=None, function_call=None, *args, **kwargs):
	kwargs.pop("sleep", None)
	if functions is not None and messages[0]["role"] != "system":
		raise ValueError("Llama chat completion with functions must have system messages")
	if function_call is not None and function_call != "auto" and not isinstance(function_call, dict):
		raise NotImplementedError
	if isinstance(function_call, dict):
		assert messages[-1]["role"] == "user"
		messages[-1]["content"] += "\n\nSUBMIT API"
		kwargs["do_function_call"] = True
	if functions is not None:
		messages[0]["content"] = messages[0]["content"].replace("{{api_doc}}", json.dumps(functions[0], ensure_ascii=False))
	
	response = llama_chat_completion(url, [messages], *args, **kwargs)
	result = {}
	if isinstance(response, dict) and "error" in response:
		return {
			"error": response["error"],
			"status_code": response["status_code"]
		}
	elif "<func>" in response[0]["generation"]["content"]:
		try:
			api_call_str = extract_func_content(response[0]["generation"]["content"])[0].strip()
			result = {
				"arguments": api_call_str
			}
		except IndexError:
			result = {
				"arguments": "{}"
			}	
	else:
		if "[DONE]" in response[0]["generation"]["content"]:
			msg = response[0]["generation"]["content"].replace("[DONE]", "").strip()
			result = {
				"end": True,
				"content": msg
			}
		else:
			result = {
				"content": response[0]["generation"]["content"]
			}
	return result

@retry(wait=wait_random_exponential(min=5, max=60), stop=stop_after_attempt(6))
def llama_chat_completion(url, dialogs, *args, **kwargs):
    # Create the payload
    payload = {
        "dialogs": dialogs,
    }
    payload.update(kwargs)

    # Send POST request
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return {
			"error": response.text,
			"status_code": response.status_code
		}
